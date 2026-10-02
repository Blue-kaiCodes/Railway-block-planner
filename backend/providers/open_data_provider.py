import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from backend.canonical_schemas import EventSource, ProviderState, RailwayEvent, EventType, EventSeverity
from backend.providers.base import BaseRailwayDataProvider

class OpenDataProvider(BaseRailwayDataProvider):
    def __init__(self):
        super().__init__(
            name='Open Government Data (data.gov.in)',
            source=EventSource.OPEN_DATA_GOV,
            poll_interval=3600.0,
            max_consecutive_errors=3,
            circuit_breaker_timeout_sec=300.0
        )
        self.api_key = os.getenv('OGD_API_KEY', '').strip()
        self.resource_id = os.getenv('OGD_RESOURCE_ID', '').strip()
        self.base_url = 'https://api.data.gov.in/resource'
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        self.cache_file = os.path.join(self.cache_dir, 'ogd_timetables_cache.json')

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith('your_'))

    async def initialize(self) -> bool:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.is_configured():
            self.state = ProviderState.AUTHENTICATION_REQUIRED
            self.diagnostic_message = 'OGD_API_KEY (data.gov.in) not configured. Timetable reference sync is dormant.'
            return False

        self.state = ProviderState.CONNECTED
        self.diagnostic_message = 'Ready to synchronize data.gov.in reference timetables'
        return True

    async def poll(self) -> List[RailwayEvent]:
        self.last_heartbeat = datetime.now(timezone.utc)
        if not self.is_configured():
            self.state = ProviderState.AUTHENTICATION_REQUIRED
            return []

        if os.path.exists(self.cache_file):
            mtime = datetime.fromtimestamp(os.path.getmtime(self.cache_file), tz=timezone.utc)
            if datetime.now(timezone.utc) - mtime < timedelta(hours=24):
                self.record_success()
                return []

        if not self.check_circuit_breaker():
            return []

        try:
            url = f'{self.base_url}/{self.resource_id}?api-key={self.api_key}&format=json&limit=50'
            req = urllib.request.Request(url, headers={'User-Agent': 'RailwayBlockPlanner/2.0-OGD'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                records = data.get('records', [])
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2)

                self.record_success()
                return []
        except Exception as e:
            self.record_error(f'Failed to fetch OGD timetables: {str(e)}')
            return []

    async def shutdown(self) -> None:
        self.state = ProviderState.DISCONNECTED
        self.diagnostic_message = 'Shutdown'
