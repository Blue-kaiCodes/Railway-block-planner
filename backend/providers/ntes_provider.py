import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.canonical_schemas import (
    EventSource, ProviderState, EventType, EventSeverity,
    DataQuality, RailwayEvent
)
from backend.providers.base import BaseRailwayDataProvider

class NTESDataProvider(BaseRailwayDataProvider):
    def __init__(self):
        poll_interval = float(os.getenv('NTES_POLL_INTERVAL_SEC', '30.0'))
        super().__init__(
            name='Indian Railways NTES',
            source=EventSource.NTES,
            poll_interval=poll_interval,
            max_consecutive_errors=4,
            circuit_breaker_timeout_sec=60.0
        )
        self.base_url = os.getenv('NTES_API_BASE_URL', '').strip()
        self.api_key = os.getenv('NTES_API_KEY', '').strip()
        self.apisetu_client_id = os.getenv('API_SETU_CLIENT_ID', '').strip()
        self.apisetu_api_key = os.getenv('API_SETU_API_KEY', '').strip()
        self.monitored_trains = [
            t.strip() for t in os.getenv('NTES_MONITORED_TRAINS', '12301,12302,12313,12314,22435,22436').split(',')
            if t.strip()
        ]

    def is_configured(self) -> bool:
        has_ntes = bool(self.api_key and not self.api_key.startswith('your_'))
        has_setu = bool(self.apisetu_client_id and self.apisetu_api_key and not self.apisetu_client_id.startswith('your_'))
        return bool(self.base_url and (has_ntes or has_setu))

    async def initialize(self) -> bool:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.is_configured():
            self.state = ProviderState.AUTHENTICATION_REQUIRED
            self.diagnostic_message = (
                'NTES credentials (NTES_API_BASE_URL and NTES_API_KEY or API_SETU keys) '
                'not configured. Schedule drift sync is dormant.'
            )
            return False

        try:
            req = urllib.request.Request(
                f'{self.base_url}/status',
                headers={'User-Agent': 'RailwayBlockPlanner/2.0-NTES', 'Accept': 'application/json'}
            )
            if self.api_key:
                req.add_header('X-API-KEY', self.api_key)
            if self.apisetu_client_id:
                req.add_header('X-APISETU-CLIENTID', self.apisetu_client_id)
                req.add_header('X-APISETU-APIKEY', self.apisetu_api_key)

            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    self.record_success()
                    self.diagnostic_message = 'Connected to NTES / API Setu'
                    return True
                else:
                    self.record_error(f'NTES ping returned HTTP {resp.status}')
                    return False
        except Exception as e:
            self.record_error(f'NTES endpoint unreachable: {str(e)}')
            return False

    async def poll(self) -> List[RailwayEvent]:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.is_configured():
            self.state = ProviderState.AUTHENTICATION_REQUIRED
            return []

        if not self.check_circuit_breaker():
            return []

        events: List[RailwayEvent] = []
        for train_id in self.monitored_trains:
            try:
                url = f'{self.base_url}/train/{train_id}/live'
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'RailwayBlockPlanner/2.0-NTES', 'Accept': 'application/json'}
                )
                if self.api_key:
                    req.add_header('X-API-KEY', self.api_key)
                if self.apisetu_client_id:
                    req.add_header('X-APISETU-CLIENTID', self.apisetu_client_id)
                    req.add_header('X-APISETU-APIKEY', self.apisetu_api_key)

                with urllib.request.urlopen(req, timeout=8) as resp:
                    payload = json.loads(resp.read().decode('utf-8'))
                    
                    delay_min = payload.get('delay_minutes', 0)
                    station_code = payload.get('current_station', '')
                    has_arrived = payload.get('has_arrived', False)
                    has_departed = payload.get('has_departed', False)

                    if has_arrived:
                        events.append(RailwayEvent(
                            event_type=EventType.TRAIN_STATION_ARRIVAL,
                            source=EventSource.NTES,
                            severity=EventSeverity.INFO,
                            train_id=train_id,
                            section_id=station_code,
                            payload={
                                'station': station_code,
                                'actual_arrival': payload.get('actual_arrival'),
                                'scheduled_arrival': payload.get('scheduled_arrival'),
                                'delay_minutes': delay_min
                            },
                            provenance={'provider': 'NTES'}
                        ))

                    if has_departed:
                        events.append(RailwayEvent(
                            event_type=EventType.TRAIN_STATION_DEPARTURE,
                            source=EventSource.NTES,
                            severity=EventSeverity.INFO,
                            train_id=train_id,
                            section_id=station_code,
                            payload={
                                'station': station_code,
                                'actual_departure': payload.get('actual_departure'),
                                'scheduled_departure': payload.get('scheduled_departure'),
                                'delay_minutes': delay_min
                            },
                            provenance={'provider': 'NTES'}
                        ))

                    if delay_min >= 5:
                        events.append(RailwayEvent(
                            event_type=EventType.SCHEDULE_DRIFT,
                            source=EventSource.NTES,
                            severity=EventSeverity.WARNING,
                            train_id=train_id,
                            section_id=station_code,
                            payload={
                                'delay_seconds': delay_min * 60,
                                'delay_minutes': delay_min,
                                'station': station_code
                            },
                            provenance={'provider': 'NTES'}
                        ))

            except urllib.error.HTTPError as he:
                if he.code in (401, 403):
                    self.state = ProviderState.AUTHENTICATION_REQUIRED
                    self.diagnostic_message = f'NTES Authentication failed: HTTP {he.code}'
                    return []
                else:
                    self.record_error(f'NTES train {train_id} returned HTTP {he.code}')
            except Exception as e:
                self.record_error(f'NTES poll error for train {train_id}: {str(e)}')

        self.record_success()
        return events

    async def shutdown(self) -> None:
        self.state = ProviderState.DISCONNECTED
        self.diagnostic_message = 'Shutdown'
