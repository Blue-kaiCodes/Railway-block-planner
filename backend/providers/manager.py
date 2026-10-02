import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.canonical_schemas import (
    EventSource, ProviderState, EventType, EventSeverity,
    DataQuality, RailwayEvent, NormalizedTrainState, BlockState
)
from backend.railway_state import RailwayStateStore, get_state_store
from backend.providers.base import BaseRailwayDataProvider
from backend.providers.rtis_provider import RTISDataProvider
from backend.providers.ntes_provider import NTESDataProvider
from backend.providers.open_data_provider import OpenDataProvider
from backend.providers.simulation_provider import SimulationDataProvider

logger = logging.getLogger('railway.provider_manager')

class ProviderManager:
    def __init__(self, state_store: Optional[RailwayStateStore] = None):
        self.state_store = state_store or get_state_store()
        self.providers: Dict[str, BaseRailwayDataProvider] = {
            'rtis': RTISDataProvider(),
            'ntes': NTESDataProvider(),
            'ogd': OpenDataProvider(),
            'simulation': SimulationDataProvider()
        }
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        if self._running:
            return
        self._running = True
        logger.info('Initializing Railway Data Providers...')

        for key, prov in self.providers.items():
            try:
                success = await prov.initialize()
                status_str = 'ONLINE' if success else prov.state.value
                logger.info(f'Provider [{prov.name}] initialization: {status_str}')
            except Exception as e:
                prov.record_error(f'Failed to initialize: {str(e)}')
                logger.error(f'Provider [{prov.name}] initialization error: {e}')

            task = asyncio.create_task(self._provider_poll_loop(key, prov))
            self._tasks.append(task)

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        for prov in self.providers.values():
            try:
                await prov.shutdown()
            except Exception as e:
                logger.warning(f'Error shutting down {prov.name}: {e}')
        self._tasks.clear()

    async def _provider_poll_loop(self, key: str, provider: BaseRailwayDataProvider):
        await asyncio.sleep(0.5)

        while self._running:
            try:
                if provider.state not in (ProviderState.AUTHENTICATION_REQUIRED, ProviderState.DISCONNECTED) or key == 'simulation':
                    events = await provider.poll()
                    for evt in events:
                        self.process_incoming_event(evt)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f'Polling loop exception in provider {provider.name}: {e}')
                provider.record_error(str(e))

            await asyncio.sleep(provider.poll_interval)

    def process_incoming_event(self, evt: RailwayEvent):
        self.state_store.record_event(evt)

        if evt.event_type == EventType.TRAIN_GPS_UPDATE and evt.train_id:
            payload = evt.payload or {}
            quality = DataQuality.SIMULATED if evt.source == EventSource.SIMULATION else DataQuality.LIVE
            train = NormalizedTrainState(
                train_id=evt.train_id,
                train_name=payload.get('train_name'),
                source=evt.source,
                latitude=payload.get('latitude'),
                longitude=payload.get('longitude'),
                speed_kmph=float(payload.get('speed_kmph', 0.0)),
                direction=payload.get('direction', 'DOWN'),
                current_section=payload.get('current_section') or evt.section_id or 'UNKNOWN',
                next_section=payload.get('next_section'),
                status='RUNNING' if float(payload.get('speed_kmph', 0.0)) > 0 else 'HALTED',
                delay_seconds=int(payload.get('delay_seconds', 0)),
                timestamp=payload.get('timestamp') or evt.timestamp.isoformat(),
                received_at=datetime.now(timezone.utc).isoformat(),
                source_event_id=evt.event_id,
                data_quality=quality
            )
            self.state_store.upsert_train_state(train)
            self.state_store.record_telemetry(
                sensor_id=train.train_id,
                timestamp=train.timestamp,
                metric_name='speed_kmph',
                metric_value=train.speed_kmph,
                raw_payload=payload
            )

        elif evt.block_id:
            blk = self.state_store.get_block_state(evt.block_id)
            if not blk:
                blk = BlockState(
                    block_id=evt.block_id,
                    section_id=evt.section_id or 'SEC-01',
                    occupancy_state='CLEAR',
                    restriction_status='NORMAL'
                )

            if evt.event_type == EventType.BLOCK_OCCUPIED:
                blk.occupancy_state = 'OCCUPIED'
                blk.occupied_by = evt.train_id or evt.payload.get('occupied_by_train')
            elif evt.event_type == EventType.BLOCK_CLEARED:
                blk.occupancy_state = 'CLEAR'
                blk.occupied_by = None
                blk.axle_count_balance = 0
            elif evt.event_type == EventType.AXLE_COUNTER_ENTRY:
                in_count = evt.payload.get('axle_count_in', 0)
                blk.axle_count_balance += in_count
                if blk.axle_count_balance > 0:
                    blk.occupancy_state = 'OCCUPIED'
                    if evt.train_id:
                        blk.occupied_by = evt.train_id
            elif evt.event_type == EventType.AXLE_COUNTER_EXIT:
                out_count = evt.payload.get('axle_count_out', 0)
                blk.axle_count_balance = max(0, blk.axle_count_balance - out_count)
                if blk.axle_count_balance == 0:
                    blk.occupancy_state = 'CLEAR'
                    blk.occupied_by = None
            elif evt.event_type == EventType.SPEED_RESTRICTION_IMPOSED:
                blk.restriction_status = 'RESTRICTED'
                blk.active_speed_limit_kmph = float(evt.payload.get('max_speed_kmph', 45.0))
            elif evt.event_type == EventType.SPEED_RESTRICTION_LIFTED:
                blk.restriction_status = 'NORMAL'
                blk.active_speed_limit_kmph = None

            self.state_store.upsert_block_state(blk)

    def get_health_summary(self) -> Dict[str, Any]:
        providers_health = {k: v.get_health() for k, v in self.providers.items()}

        rtis_health = providers_health.get('rtis', {})
        ntes_health = providers_health.get('ntes', {})
        sim_health = providers_health.get('simulation', {})

        if rtis_health.get('state') == 'CONNECTED':
            primary_source = 'CRIS/ISRO RTIS'
            quality = 'LIVE'
            disclaimer = None
            is_live = True
        elif ntes_health.get('state') == 'CONNECTED':
            primary_source = 'Indian Railways NTES'
            quality = 'LIVE'
            disclaimer = None
            is_live = True
        elif sim_health.get('state') == 'CONNECTED':
            primary_source = 'SIMULATION'
            quality = 'SIMULATED'
            disclaimer = 'DATA SOURCE: SIMULATION (NOT LIVE RAILWAY DATA)'
            is_live = False
        else:
            primary_source = 'NONE'
            quality = 'UNAVAILABLE'
            disclaimer = 'No active railway data feed connected. Configure RTIS/NTES credentials or enable simulation.'
            is_live = False

        return {
            'status': 'HEALTHY' if is_live or primary_source == 'SIMULATION' else 'ATTENTION_REQUIRED',
            'primary_source': primary_source,
            'data_quality': quality,
            'is_live_data': is_live,
            'disclaimer': disclaimer,
            'providers': providers_health,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def inject_simulation_disturbance(self, disturbance_type: str, target_id: str, value: Any) -> Optional[RailwayEvent]:
        sim = self.providers.get('simulation')
        if isinstance(sim, SimulationDataProvider) and sim.enabled:
            evt = sim.inject_simulated_disturbance(disturbance_type, target_id, value)
            if evt:
                self.process_incoming_event(evt)
                return evt
        return None

provider_manager = ProviderManager()

def get_provider_manager() -> ProviderManager:
    return provider_manager
