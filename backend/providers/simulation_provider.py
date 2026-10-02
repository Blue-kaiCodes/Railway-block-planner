import os
import math
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from backend.canonical_schemas import (
    EventSource, ProviderState, EventType, EventSeverity,
    DataQuality, RailwayEvent, NormalizedTrainState
)
from backend.providers.base import BaseRailwayDataProvider

class SimulationDataProvider(BaseRailwayDataProvider):
    # Explicit Development and Testing Simulation Provider.
    # STRICT COMPLIANCE NOTICE:
    # - Exists purely for local offline testing when live feeds are unavailable.
    # - Every event and train state is explicitly stamped with:
    #   data_quality = DataQuality.SIMULATED
    #   provenance = {'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'}
    # - Can be fully disabled at any time via ENABLE_SIMULATION_PROVIDER=false.
    def __init__(self):
        poll_interval = float(os.getenv('SIMULATION_TICK_INTERVAL_SEC', '5.0'))
        super().__init__(
            name='Development Simulation Provider',
            source=EventSource.SIMULATION,
            poll_interval=poll_interval
        )
        self.enabled = os.getenv('ENABLE_SIMULATION_PROVIDER', 'true').lower() in ('true', '1', 'yes')

        self.sections = [
            {'id': 'SEC-01', 'name': 'Howrah - Barddhaman', 'km_start': 0, 'km_end': 100, 'blocks': ['BLK-01', 'BLK-02']},
            {'id': 'SEC-02', 'name': 'Barddhaman - Asansol', 'km_start': 100, 'km_end': 200, 'blocks': ['BLK-03', 'BLK-04']},
            {'id': 'SEC-03', 'name': 'Asansol - Dhanbad', 'km_start': 200, 'km_end': 260, 'blocks': ['BLK-05']},
            {'id': 'SEC-04', 'name': 'Dhanbad - Gaya', 'km_start': 260, 'km_end': 460, 'blocks': ['BLK-06', 'BLK-07']},
            {'id': 'SEC-05', 'name': 'Gaya - Pt. Deen Dayal Upadhyaya', 'km_start': 460, 'km_end': 660, 'blocks': ['BLK-08']}
        ]

        self.train_roster = [
            {
                'train_id': '12301',
                'train_name': 'Howrah Rajdhani Express',
                'direction': 'UP',
                'km': 85.0,
                'speed_kmph': 110.0,
                'current_section': 'SEC-01',
                'current_block': 'BLK-02',
                'axles': 88,
                'delay_seconds': 120
            },
            {
                'train_id': '12313',
                'train_name': 'Sealdah Rajdhani Express',
                'direction': 'UP',
                'km': 190.0,
                'speed_kmph': 105.0,
                'current_section': 'SEC-02',
                'current_block': 'BLK-04',
                'axles': 92,
                'delay_seconds': 0
            },
            {
                'train_id': '22435',
                'train_name': 'Vande Bharat Express',
                'direction': 'DOWN',
                'km': 310.0,
                'speed_kmph': 125.0,
                'current_section': 'SEC-04',
                'current_block': 'BLK-06',
                'axles': 64,
                'delay_seconds': 60
            },
            {
                'train_id': '12302',
                'train_name': 'New Delhi - Howrah Rajdhani',
                'direction': 'DOWN',
                'km': 490.0,
                'speed_kmph': 115.0,
                'current_section': 'SEC-05',
                'current_block': 'BLK-08',
                'axles': 88,
                'delay_seconds': 360
            }
        ]

    async def initialize(self) -> bool:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.enabled:
            self.state = ProviderState.DISCONNECTED
            self.diagnostic_message = 'Simulation provider disabled via configuration (ENABLE_SIMULATION_PROVIDER=false).'
            return False

        self.state = ProviderState.CONNECTED
        self.diagnostic_message = 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA) - Active for development/testing'
        self.record_success()
        return True

    def is_configured(self) -> bool:
        return self.enabled

    def _get_block_for_km(self, km: float) -> tuple[str, str]:
        for sec in self.sections:
            if sec['km_start'] <= km <= sec['km_end']:
                blocks = sec['blocks']
                sec_len = sec['km_end'] - sec['km_start']
                frac = (km - sec['km_start']) / max(sec_len, 1)
                idx = min(int(frac * len(blocks)), len(blocks) - 1)
                return sec['id'], blocks[idx]
        return 'SEC-01', 'BLK-01'

    async def poll(self) -> List[RailwayEvent]:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.enabled:
            return []

        events: List[RailwayEvent] = []
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        dt_hours = self.poll_interval / 3600.0

        for train in self.train_roster:
            old_km = train['km']
            speed = train['speed_kmph']
            old_block = train['current_block']
            old_section = train['current_section']

            if train['direction'] == 'UP':
                new_km = old_km + (speed * dt_hours)
                if new_km > 660.0:
                    new_km = 10.0
            else:
                new_km = old_km - (speed * dt_hours)
                if new_km < 10.0:
                    new_km = 650.0

            train['km'] = round(new_km, 2)
            new_section, new_block = self._get_block_for_km(new_km)
            train['current_section'] = new_section
            train['current_block'] = new_block

            lat = round(22.58 + (new_km / 660.0) * (25.28 - 22.58), 5)
            lon = round(88.35 + (new_km / 660.0) * (83.12 - 88.35), 5)

            events.append(RailwayEvent(
                event_type=EventType.TRAIN_GPS_UPDATE,
                source=EventSource.SIMULATION,
                severity=EventSeverity.INFO,
                train_id=train['train_id'],
                section_id=new_section,
                block_id=new_block,
                payload={
                    'train_name': train['train_name'],
                    'latitude': lat,
                    'longitude': lon,
                    'speed_kmph': train['speed_kmph'],
                    'direction': train['direction'],
                    'current_section': new_section,
                    'current_block': new_block,
                    'delay_seconds': train['delay_seconds'],
                    'timestamp': now_iso
                },
                provenance={
                    'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)',
                    'generator': 'PhysicsKinematicsEngine',
                    'tick_interval_sec': self.poll_interval
                }
            ))

            if new_block != old_block:
                events.append(RailwayEvent(
                    event_type=EventType.AXLE_COUNTER_EXIT,
                    source=EventSource.SIMULATION,
                    severity=EventSeverity.INFO,
                    train_id=train['train_id'],
                    section_id=old_section,
                    block_id=old_block,
                    payload={
                        'axle_count_out': train['axles'],
                        'axle_balance': 0,
                        'timestamp': now_iso
                    },
                    provenance={'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'}
                ))
                events.append(RailwayEvent(
                    event_type=EventType.BLOCK_CLEARED,
                    source=EventSource.SIMULATION,
                    severity=EventSeverity.INFO,
                    train_id=train['train_id'],
                    section_id=old_section,
                    block_id=old_block,
                    payload={'cleared_by_train': train['train_id']},
                    provenance={'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'}
                ))

                events.append(RailwayEvent(
                    event_type=EventType.AXLE_COUNTER_ENTRY,
                    source=EventSource.SIMULATION,
                    severity=EventSeverity.INFO,
                    train_id=train['train_id'],
                    section_id=new_section,
                    block_id=new_block,
                    payload={
                        'axle_count_in': train['axles'],
                        'axle_balance': train['axles'],
                        'timestamp': now_iso
                    },
                    provenance={'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'}
                ))
                events.append(RailwayEvent(
                    event_type=EventType.BLOCK_OCCUPIED,
                    source=EventSource.SIMULATION,
                    severity=EventSeverity.WARNING,
                    train_id=train['train_id'],
                    section_id=new_section,
                    block_id=new_block,
                    payload={'occupied_by_train': train['train_id'], 'speed_kmph': speed},
                    provenance={'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'}
                ))

        self.record_success()
        return events

    def inject_simulated_disturbance(self, disturbance_type: str, target_id: str, value: Any) -> Optional[RailwayEvent]:
        now_iso = datetime.now(timezone.utc).isoformat()
        if disturbance_type == 'TRAIN_DELAY':
            for t in self.train_roster:
                if t['train_id'] == target_id:
                    t['delay_seconds'] += int(value)
                    return RailwayEvent(
                        event_type=EventType.SCHEDULE_DRIFT,
                        source=EventSource.SIMULATION,
                        severity=EventSeverity.WARNING,
                        train_id=target_id,
                        section_id=t['current_section'],
                        block_id=t['current_block'],
                        payload={
                            'delay_seconds': t['delay_seconds'],
                            'added_delay_seconds': int(value),
                            'reason': 'Simulated signal hold / crossing delay'
                        },
                        provenance={'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'}
                    )
        elif disturbance_type == 'SPEED_RESTRICTION':
            return RailwayEvent(
                event_type=EventType.SPEED_RESTRICTION_IMPOSED,
                source=EventSource.SIMULATION,
                severity=EventSeverity.WARNING,
                block_id=target_id,
                payload={
                    'max_speed_kmph': float(value),
                    'reason': 'Simulated track maintenance / high temperature'
                },
                provenance={'disclaimer': 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'}
            )
        return None

    async def shutdown(self) -> None:
        self.state = ProviderState.DISCONNECTED
        self.diagnostic_message = 'Shutdown'
