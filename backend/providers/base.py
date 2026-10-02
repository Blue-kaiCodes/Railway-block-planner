import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from backend.canonical_schemas import EventSource, ProviderState, RailwayEvent

class BaseRailwayDataProvider(ABC):
    def __init__(
        self,
        name: str,
        source: EventSource,
        poll_interval: float = 30.0,
        max_consecutive_errors: int = 5,
        circuit_breaker_timeout_sec: float = 60.0
    ):
        self.name = name
        self.source = source
        self.poll_interval = poll_interval
        self.max_consecutive_errors = max_consecutive_errors
        self.circuit_breaker_timeout_sec = circuit_breaker_timeout_sec

        self.state: ProviderState = ProviderState.DISCONNECTED
        self.last_heartbeat: Optional[datetime] = None
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.consecutive_errors: int = 0
        self.circuit_breaker_open: bool = False
        self.circuit_breaker_open_until: Optional[datetime] = None
        self.diagnostic_message: str = 'Initialized'

    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def poll(self) -> List[RailwayEvent]:
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        pass

    def check_circuit_breaker(self) -> bool:
        now = datetime.now(timezone.utc)
        if self.circuit_breaker_open:
            if self.circuit_breaker_open_until and now >= self.circuit_breaker_open_until:
                self.circuit_breaker_open = False
                self.circuit_breaker_open_until = None
                self.state = ProviderState.DEGRADED
                self.diagnostic_message = 'Circuit breaker half-open: attempting recovery'
                return True
            return False
        return True

    def record_success(self):
        self.consecutive_errors = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_open_until = None
        self.state = ProviderState.CONNECTED
        now = datetime.now(timezone.utc)
        self.last_success = now
        self.last_heartbeat = now
        self.last_error = None
        self.diagnostic_message = 'Operational'

    def record_error(self, err_msg: str):
        self.consecutive_errors += 1
        self.last_error = err_msg
        self.last_heartbeat = datetime.now(timezone.utc)

        if self.consecutive_errors >= self.max_consecutive_errors:
            self.circuit_breaker_open = True
            self.circuit_breaker_open_until = datetime.now(timezone.utc) + timedelta(seconds=self.circuit_breaker_timeout_sec)
            self.state = ProviderState.UNAVAILABLE
            self.diagnostic_message = f'Circuit breaker tripped after {self.consecutive_errors} failures: {err_msg}'
        else:
            self.state = ProviderState.DEGRADED
            self.diagnostic_message = f'Transient error ({self.consecutive_errors}/{self.max_consecutive_errors}): {err_msg}'

    def get_health(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'source': self.source.value,
            'state': self.state.value,
            'poll_interval_sec': self.poll_interval,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'consecutive_errors': self.consecutive_errors,
            'circuit_breaker_open': self.circuit_breaker_open,
            'last_error': self.last_error,
            'message': self.diagnostic_message
        }
