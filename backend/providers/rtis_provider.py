import os
import json
import ssl
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.canonical_schemas import (
    EventSource, ProviderState, EventType, EventSeverity,
    DataQuality, RailwayEvent, NormalizedTrainState
)
from backend.providers.base import BaseRailwayDataProvider

class RTISDataProvider(BaseRailwayDataProvider):
    def __init__(self):
        poll_interval = float(os.getenv('RTIS_POLL_INTERVAL_SEC', '15.0'))
        super().__init__(
            name='CRIS/ISRO RTIS',
            source=EventSource.RTIS,
            poll_interval=poll_interval,
            max_consecutive_errors=3,
            circuit_breaker_timeout_sec=45.0
        )
        self.base_url = os.getenv('RTIS_API_BASE_URL', '').strip()
        self.client_id = os.getenv('RTIS_CLIENT_ID', '').strip()
        self.client_secret = os.getenv('RTIS_CLIENT_SECRET', '').strip()
        self.auth_token = os.getenv('RTIS_AUTH_TOKEN', '').strip()
        self.cert_path = os.getenv('RTIS_MTLS_CERT_PATH', '').strip()
        self.key_path = os.getenv('RTIS_MTLS_KEY_PATH', '').strip()
        self.active_train_ids = [
            t.strip() for t in os.getenv('RTIS_MONITORED_TRAINS', '12301,12302,12313,12314,22435,22436').split(',')
            if t.strip()
        ]

    def is_configured(self) -> bool:
        has_token = bool(self.auth_token and not self.auth_token.startswith('replace_') and not self.auth_token.startswith('your_'))
        has_client = bool(self.client_id and self.client_secret and not self.client_id.startswith('your_'))
        return bool(self.base_url and (has_token or has_client))

    async def initialize(self) -> bool:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.is_configured():
            self.state = ProviderState.AUTHENTICATION_REQUIRED
            self.diagnostic_message = (
                'RTIS credentials (RTIS_API_BASE_URL and RTIS_AUTH_TOKEN or RTIS_CLIENT_ID/SECRET) '
                'not configured. Real-time ISRO/CRIS feed is dormant.'
            )
            return False

        try:
            req = urllib.request.Request(
                f'{self.base_url}/health',
                headers={'User-Agent': 'RailwayBlockPlanner/2.0-RTIS', 'Accept': 'application/json'}
            )
            if self.auth_token:
                req.add_header('Authorization', f'Bearer {self.auth_token}')
            
            ctx = self._create_ssl_context()
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                if resp.status == 200:
                    self.record_success()
                    self.diagnostic_message = 'Connected to CRIS/ISRO RTIS Gateway'
                    return True
                else:
                    self.record_error(f'RTIS health returned HTTP {resp.status}')
                    return False
        except Exception as e:
            self.record_error(f'Cannot reach RTIS gateway: {str(e)}')
            return False

    def _create_ssl_context(self) -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        if self.cert_path and os.path.exists(self.cert_path) and self.key_path and os.path.exists(self.key_path):
            ctx.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
        return ctx

    async def poll(self) -> List[RailwayEvent]:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.is_configured():
            self.state = ProviderState.AUTHENTICATION_REQUIRED
            return []

        if not self.check_circuit_breaker():
            return []

        events: List[RailwayEvent] = []
        try:
            train_query = ','.join(self.active_train_ids)
            url = f'{self.base_url}/telemetry?trains={train_query}'
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'RailwayBlockPlanner/2.0-RTIS', 'Accept': 'application/json'}
            )
            if self.auth_token:
                req.add_header('Authorization', f'Bearer {self.auth_token}')

            ctx = self._create_ssl_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                records = data if isinstance(data, list) else data.get('trains', [])

                now_iso = datetime.now(timezone.utc).isoformat()
                for item in records:
                    train_id = str(item.get('train_id', '')).strip()
                    if not train_id:
                        continue

                    evt = RailwayEvent(
                        event_type=EventType.TRAIN_GPS_UPDATE,
                        source=EventSource.RTIS,
                        severity=EventSeverity.INFO,
                        train_id=train_id,
                        section_id=item.get('current_section'),
                        block_id=item.get('current_block'),
                        payload={
                            'latitude': item.get('latitude'),
                            'longitude': item.get('longitude'),
                            'speed_kmph': item.get('speed_kmph', 0.0),
                            'heading_deg': item.get('heading_deg'),
                            'current_section': item.get('current_section'),
                            'next_section': item.get('next_section'),
                            'delay_seconds': item.get('delay_seconds', 0),
                            'timestamp': item.get('timestamp', now_iso)
                        },
                        provenance={
                            'provider': 'CRIS/ISRO RTIS',
                            'endpoint': self.base_url,
                            'raw_timestamp': item.get('timestamp')
                        }
                    )
                    events.append(evt)

                    delay_sec = item.get('delay_seconds', 0)
                    if delay_sec >= 300:
                        drift_evt = RailwayEvent(
                            event_type=EventType.SCHEDULE_DRIFT,
                            source=EventSource.RTIS,
                            severity=EventSeverity.WARNING,
                            train_id=train_id,
                            section_id=item.get('current_section'),
                            payload={
                                'delay_seconds': delay_sec,
                                'delay_minutes': round(delay_sec / 60.0, 1),
                                'speed_kmph': item.get('speed_kmph', 0.0)
                            },
                            provenance={'provider': 'CRIS/ISRO RTIS'}
                        )
                        events.append(drift_evt)

                self.record_success()
                return events

        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                self.state = ProviderState.AUTHENTICATION_REQUIRED
                self.diagnostic_message = f'RTIS Authentication failed (HTTP {he.code}): Check token or mTLS keys'
            else:
                self.record_error(f'RTIS HTTP error {he.code}: {he.reason}')
            return []
        except Exception as e:
            self.record_error(f'RTIS poll failed: {str(e)}')
            return []

    async def shutdown(self) -> None:
        self.state = ProviderState.DISCONNECTED
        self.diagnostic_message = 'Shutdown'
