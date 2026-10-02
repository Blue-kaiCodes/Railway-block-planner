import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from backend.canonical_schemas import (
    SensorIngestPayload, SensorEntity, SensorType, SensorStatus,
    DataQuality, EventSource, EventType, EventSeverity,
    RailwayEvent, BlockState
)
from backend.railway_state import RailwayStateStore, get_state_store

logger = logging.getLogger('railway.sensor_gateway')

class SensorGateway:
    def __init__(self, state_store: Optional[RailwayStateStore] = None):
        self.state_store = state_store or get_state_store()
        self.auth_token = os.getenv('SENSOR_INGESTION_TOKEN', 'test_sensor_gateway_token_2026').strip()
        self.mqtt_broker = os.getenv('MQTT_BROKER_URL', '').strip()
        self.mqtt_topic = os.getenv('MQTT_TOPIC_SENSOR_EVENTS', 'railway/sensors/+')

    def validate_token(self, token: Optional[str]) -> bool:
        if not self.auth_token:
            return True
        if not token:
            return False
        clean = token.replace('Bearer ', '').strip()
        return clean == self.auth_token

    def ingest_payload(self, p: SensorIngestPayload) -> Dict[str, Any]:
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        sensor = self.state_store.get_sensor(p.sensor_id)
        if not sensor:
            sensor = SensorEntity(
                sensor_id=p.sensor_id,
                sensor_type=p.sensor_type,
                section_id=p.section_id,
                status=SensorStatus.ONLINE,
                last_seen=now_iso,
                source=p.source,
                data_quality=DataQuality.LIVE,
                telemetry={},
                metadata={'registered_via': 'gateway_ingest'}
            )

        sensor.last_seen = now_iso
        sensor.status = SensorStatus.ONLINE

        telemetry = dict(sensor.telemetry or {})
        if p.temperature_celsius is not None:
            telemetry['temperature_celsius'] = p.temperature_celsius
        if p.water_level_meters is not None:
            telemetry['water_level_meters'] = p.water_level_meters
        if p.axle_count is not None:
            telemetry['axle_count'] = p.axle_count
        if p.vibration_g is not None:
            telemetry['vibration_g'] = p.vibration_g
        if p.payload:
            telemetry.update(p.payload)
        sensor.telemetry = telemetry
        self.state_store.upsert_sensor(sensor)

        for metric, val in [
            ('temperature_celsius', p.temperature_celsius),
            ('water_level_meters', p.water_level_meters),
            ('axle_count', p.axle_count),
            ('vibration_g', p.vibration_g)
        ]:
            if val is not None:
                self.state_store.record_telemetry(
                    sensor_id=p.sensor_id,
                    timestamp=p.timestamp or now_iso,
                    metric_name=metric,
                    metric_value=float(val),
                    raw_payload=p.payload
                )

        sec_suffix = p.section_id[-2:] if len(p.section_id) >= 2 else '01'
        block_id = p.payload.get('block_id', f'BLK-{sec_suffix}')
        blk = self.state_store.get_block_state(block_id)
        if not blk:
            blk = BlockState(
                block_id=block_id,
                section_id=p.section_id,
                occupancy_state='CLEAR',
                restriction_status='NORMAL'
            )

        events_generated: List[RailwayEvent] = []

        if p.sensor_type == SensorType.AXLE_COUNTER:
            events_generated.extend(self._process_axle_counter(p, blk, now_iso))
        elif p.sensor_type == SensorType.RAIL_TEMPERATURE:
            events_generated.extend(self._process_rail_temperature(p, blk, now_iso))
        elif p.sensor_type == SensorType.BRIDGE_WATER_LEVEL:
            events_generated.extend(self._process_bridge_water(p, blk, now_iso))
        elif p.sensor_type == SensorType.TRACK_GEOMETRY or p.sensor_type == SensorType.VIBRATION:
            events_generated.extend(self._process_track_geometry(p, blk, now_iso))
        else:
            evt = RailwayEvent(
                event_type=p.event_type,
                source=p.source,
                entity_id=p.sensor_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=block_id,
                timestamp=p.timestamp or now_iso,
                severity=p.severity,
                title=f'Sensor Event: {p.sensor_id}',
                description=p.details or f'{p.sensor_type.value} reported status',
                payload=p.payload,
                provenance={'ingest': 'SensorGateway', 'sensor_id': p.sensor_id}
            )
            events_generated.append(evt)

        for evt in events_generated:
            self.state_store.record_event(evt)

        self.state_store.upsert_block_state(blk)

        return {
            'status': 'SUCCESS',
            'sensor_id': p.sensor_id,
            'events_count': len(events_generated),
            'block_id': blk.block_id,
            'block_occupancy': blk.occupancy_state,
            'restriction_status': blk.restriction_status,
            'timestamp': now_iso
        }

    def _process_axle_counter(self, p: SensorIngestPayload, blk: BlockState, now_iso: str) -> List[RailwayEvent]:
        events: List[RailwayEvent] = []
        count = p.axle_count or 0
        direction = p.payload.get('direction', 'IN')
        train_id = p.payload.get('train_id')

        if direction == 'IN' or p.event_type == EventType.SECTION_ENTRY:
            blk.axle_count_balance += count
            blk.occupancy_state = 'OCCUPIED'
            blk.last_entry_time = now_iso
            if train_id:
                blk.occupied_by = train_id

            events.append(RailwayEvent(
                event_type=EventType.SECTION_ENTRY,
                source=EventSource.AXLE_COUNTER,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                train_id=train_id,
                timestamp=p.timestamp or now_iso,
                severity=EventSeverity.INFO,
                title=f'Section Entry: {blk.block_id}',
                description=f'Axle counter {p.sensor_id} recorded {count} axles IN. Balance: {blk.axle_count_balance}',
                payload={'axle_count_in': count, 'balance': blk.axle_count_balance, 'train_id': train_id},
                provenance={'sensor_id': p.sensor_id}
            ))

        elif direction == 'OUT' or p.event_type == EventType.SECTION_EXIT:
            prev_balance = blk.axle_count_balance
            blk.axle_count_balance -= count
            blk.last_exit_time = now_iso

            if blk.axle_count_balance < 0:
                events.append(RailwayEvent(
                    event_type=EventType.TRACK_ANOMALY,
                    source=EventSource.AXLE_COUNTER,
                    entity_id=blk.block_id,
                    sensor_id=p.sensor_id,
                    section_id=p.section_id,
                    block_id=blk.block_id,
                    timestamp=now_iso,
                    severity=EventSeverity.CRITICAL,
                    title=f'Axle Counter Mismatch: {blk.block_id}',
                    description=f'Negative axle balance ({blk.axle_count_balance}) detected at {p.sensor_id}. Out ({count}) > Previous ({prev_balance}). Possible axle miscount or train split!',
                    payload={'previous_balance': prev_balance, 'out_count': count, 'new_balance': blk.axle_count_balance},
                    provenance={'sensor_id': p.sensor_id}
                ))
                blk.axle_count_balance = 0

            if blk.axle_count_balance == 0:
                blk.occupancy_state = 'CLEAR'
                blk.occupied_by = None
                events.append(RailwayEvent(
                    event_type=EventType.SECTION_CLEAR,
                    source=EventSource.AXLE_COUNTER,
                    entity_id=blk.block_id,
                    sensor_id=p.sensor_id,
                    section_id=p.section_id,
                    block_id=blk.block_id,
                    timestamp=now_iso,
                    severity=EventSeverity.INFO,
                    title=f'Section Cleared: {blk.block_id}',
                    description=f'Axle counter balance reached zero. Block {blk.block_id} cleared.',
                    payload={'axles_out': count, 'balance': 0},
                    provenance={'sensor_id': p.sensor_id}
                ))

        return events

    def _process_rail_temperature(self, p: SensorIngestPayload, blk: BlockState, now_iso: str) -> List[RailwayEvent]:
        events: List[RailwayEvent] = []
        temp = p.temperature_celsius
        if temp is None:
            return events

        if temp >= 65.0:
            blk.restriction_status = 'RESTRICTED'
            blk.active_speed_limit_kmph = 30.0
            events.append(RailwayEvent(
                event_type=EventType.SPEED_RESTRICTION_APPLIED,
                source=EventSource.TRACK_SENSOR,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                timestamp=now_iso,
                severity=EventSeverity.CRITICAL,
                title=f'Extreme Rail Temp Alert: {temp} C',
                description=f'Rail temperature reached {temp} C at {blk.block_id} (exceeds 65 C buckling threshold). Mandatory 30 km/h caution imposed.',
                payload={'temperature_celsius': temp, 'speed_limit_kmph': 30.0, 'hazard': 'RAIL_BUCKLING'},
                provenance={'sensor_id': p.sensor_id}
            ))
        elif temp >= 55.0:
            events.append(RailwayEvent(
                event_type=EventType.RAIL_TEMPERATURE_ALERT,
                source=EventSource.TRACK_SENSOR,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                timestamp=now_iso,
                severity=EventSeverity.WARNING,
                title=f'High Rail Temp Warning: {temp} C',
                description=f'Rail temperature elevated at {temp} C on {blk.block_id}. Patrolling advised.',
                payload={'temperature_celsius': temp},
                provenance={'sensor_id': p.sensor_id}
            ))
        elif temp <= 50.0 and blk.active_speed_limit_kmph == 30.0:
            blk.restriction_status = 'NORMAL'
            blk.active_speed_limit_kmph = None
            events.append(RailwayEvent(
                event_type=EventType.SPEED_RESTRICTION_REMOVED,
                source=EventSource.TRACK_SENSOR,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                timestamp=now_iso,
                severity=EventSeverity.INFO,
                title=f'Rail Temp Normalized: {temp} C',
                description=f'Track temperature cooled to {temp} C. Thermal speed restriction lifted.',
                payload={'temperature_celsius': temp},
                provenance={'sensor_id': p.sensor_id}
            ))

        return events

    def _process_bridge_water(self, p: SensorIngestPayload, blk: BlockState, now_iso: str) -> List[RailwayEvent]:
        events: List[RailwayEvent] = []
        level = p.water_level_meters
        if level is None:
            return events

        if level >= 4.5:
            blk.restriction_status = 'RESTRICTED'
            blk.active_speed_limit_kmph = 0.0
            events.append(RailwayEvent(
                event_type=EventType.BRIDGE_WATER_ALERT,
                source=EventSource.TRACK_SENSOR,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                timestamp=now_iso,
                severity=EventSeverity.EMERGENCY,
                title=f'Bridge Pier Flood Danger: {level}m',
                description=f'Water level at bridge pier sensor {p.sensor_id} is {level}m (exceeds Danger Level 4.5m). Section {blk.block_id} SUSPENDED.',
                payload={'water_level_meters': level, 'danger_level': 4.5, 'action': 'SUSPEND_TRAFFIC'},
                provenance={'sensor_id': p.sensor_id}
            ))
        elif level >= 3.5:
            blk.restriction_status = 'RESTRICTED'
            blk.active_speed_limit_kmph = 20.0
            events.append(RailwayEvent(
                event_type=EventType.BRIDGE_WATER_ALERT,
                source=EventSource.TRACK_SENSOR,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                timestamp=now_iso,
                severity=EventSeverity.WARNING,
                title=f'Bridge High Water Warning: {level}m',
                description=f'Water level at bridge pier is {level}m (exceeds Warning Level 3.5m). Speed restricted to 20 km/h.',
                payload={'water_level_meters': level, 'warning_level': 3.5, 'speed_limit_kmph': 20.0},
                provenance={'sensor_id': p.sensor_id}
            ))

        return events

    def _process_track_geometry(self, p: SensorIngestPayload, blk: BlockState, now_iso: str) -> List[RailwayEvent]:
        events: List[RailwayEvent] = []
        vib = p.vibration_g
        dev = p.payload.get('alignment_deviation_mm', 0.0)

        if vib is not None and vib >= 0.8:
            events.append(RailwayEvent(
                event_type=EventType.TRACK_GEOMETRY_DEFECT,
                source=EventSource.TRACK_SENSOR,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                timestamp=now_iso,
                severity=EventSeverity.CRITICAL,
                title=f'Excessive Track Vibration: {vib}g',
                description=f'Sensor {p.sensor_id} measured {vib}g dynamic impact vibration. Possible rail weld fracture or severe joint dipping.',
                payload={'vibration_g': vib},
                provenance={'sensor_id': p.sensor_id}
            ))
        elif dev >= 15.0:
            events.append(RailwayEvent(
                event_type=EventType.TRACK_GEOMETRY_DEFECT,
                source=EventSource.TRACK_SENSOR,
                entity_id=blk.block_id,
                sensor_id=p.sensor_id,
                section_id=p.section_id,
                block_id=blk.block_id,
                timestamp=now_iso,
                severity=EventSeverity.WARNING,
                title=f'Track Geometry Alignment Defect: {dev}mm',
                description=f'Track alignment deviation of {dev}mm detected at {blk.block_id}. Urgent tamping required.',
                payload={'alignment_deviation_mm': dev},
                provenance={'sensor_id': p.sensor_id}
            ))

        return events

    def check_heartbeats(self, timeout_minutes: int = 5):
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)).isoformat()
        sensors = self.state_store.get_all_sensors()
        for s in sensors:
            if s.last_seen < cutoff and s.status != SensorStatus.OFFLINE:
                s.status = SensorStatus.OFFLINE
                self.state_store.upsert_sensor(s)
                self.state_store.record_event(RailwayEvent(
                    event_type=EventType.SENSOR_OFFLINE,
                    source=EventSource.TRACK_SENSOR,
                    entity_id=s.sensor_id,
                    sensor_id=s.sensor_id,
                    section_id=s.section_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    severity=EventSeverity.WARNING,
                    title=f'Sensor Offline: {s.sensor_id}',
                    description=f'Sensor {s.sensor_id} has not sent telemetry in over {timeout_minutes} minutes.',
                    payload={'last_seen': s.last_seen},
                    provenance={'gateway': 'heartbeat_monitor'}
                ))

    def seed_default_sensors(self):
        default_sensors = [
            SensorEntity(sensor_id='AXLE-SEC01-01', sensor_type=SensorType.AXLE_COUNTER, section_id='SEC-01', status=SensorStatus.ONLINE, telemetry={'axle_count': 0, 'balance': 0}, battery_pct=98.5),
            SensorEntity(sensor_id='AXLE-SEC02-01', sensor_type=SensorType.AXLE_COUNTER, section_id='SEC-02', status=SensorStatus.ONLINE, telemetry={'axle_count': 0, 'balance': 0}, battery_pct=94.0),
            SensorEntity(sensor_id='AXLE-SEC03-01', sensor_type=SensorType.AXLE_COUNTER, section_id='SEC-03', status=SensorStatus.ONLINE, telemetry={'axle_count': 0, 'balance': 0}, battery_pct=99.0),
            SensorEntity(sensor_id='AXLE-SEC04-01', sensor_type=SensorType.AXLE_COUNTER, section_id='SEC-04', status=SensorStatus.ONLINE, telemetry={'axle_count': 0, 'balance': 0}, battery_pct=91.2),
            SensorEntity(sensor_id='AXLE-SEC05-01', sensor_type=SensorType.AXLE_COUNTER, section_id='SEC-05', status=SensorStatus.ONLINE, telemetry={'axle_count': 0, 'balance': 0}, battery_pct=95.8),
            SensorEntity(sensor_id='TEMP-SEC01-01', sensor_type=SensorType.RAIL_TEMPERATURE, section_id='SEC-01', status=SensorStatus.ONLINE, telemetry={'temperature_celsius': 38.2}, battery_pct=88.0),
            SensorEntity(sensor_id='TEMP-SEC03-01', sensor_type=SensorType.RAIL_TEMPERATURE, section_id='SEC-03', status=SensorStatus.ONLINE, telemetry={'temperature_celsius': 42.5}, battery_pct=92.5),
            SensorEntity(sensor_id='TEMP-SEC04-01', sensor_type=SensorType.RAIL_TEMPERATURE, section_id='SEC-04', status=SensorStatus.ONLINE, telemetry={'temperature_celsius': 40.1}, battery_pct=86.4),
            SensorEntity(sensor_id='WTR-BRG-01', sensor_type=SensorType.BRIDGE_WATER_LEVEL, section_id='SEC-02', status=SensorStatus.ONLINE, telemetry={'water_level_meters': 2.1}, battery_pct=97.0),
            SensorEntity(sensor_id='WTR-BRG-02', sensor_type=SensorType.BRIDGE_WATER_LEVEL, section_id='SEC-04', status=SensorStatus.ONLINE, telemetry={'water_level_meters': 1.8}, battery_pct=93.5),
            SensorEntity(sensor_id='GEOM-SEC02-01', sensor_type=SensorType.TRACK_GEOMETRY, section_id='SEC-02', status=SensorStatus.ONLINE, telemetry={'vibration_g': 0.15, 'alignment_deviation_mm': 2.1}, battery_pct=89.0),
            SensorEntity(sensor_id='GEOM-SEC05-01', sensor_type=SensorType.TRACK_GEOMETRY, section_id='SEC-05', status=SensorStatus.ONLINE, telemetry={'vibration_g': 0.18, 'alignment_deviation_mm': 3.4}, battery_pct=94.2),
        ]
        for s in default_sensors:
            self.state_store.upsert_sensor(s)

sensor_gateway = SensorGateway()

def get_sensor_gateway() -> SensorGateway:
    return sensor_gateway
