import os
from typing import Dict, Any, Optional
from datetime import datetime

class TrainDataProvider:
    def __init__(self):
        self.provider_name = os.getenv("TRAIN_API_PROVIDER", "mock_or_unconfigured")
        self.api_key = os.getenv("TRAIN_API_KEY", "")
        self.base_url = os.getenv("TRAIN_API_BASE_URL", "https://api.railwaydata.gov.in/v1")

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def get_provider_status(self) -> Dict[str, Any]:
        configured = self.is_configured()
        return {
            "configured": configured,
            "live_feed_configured": configured,
            "provider": self.provider_name if configured else "NONE",
            "provider_name": self.provider_name if configured else "NONE",
            "base_url": self.base_url if configured else None,
            "message": "LIVE DATA CONFIGURED" if configured else "LIVE DATA NOT CONFIGURED: Set TRAIN_API_KEY in backend .env to connect live Indian Railways feeds."
        }

    def get_live_train_status(self, train_number: str) -> Dict[str, Any]:
        train_num = train_number.strip()
        if not self.is_configured():
            return {
                "status": "LIVE DATA NOT CONFIGURED",
                "configured": False,
                "train_number": train_num,
                "train_name": f"Express Service {train_num}",
                "section": "Howrah – DDU Trunk Line",
                "scheduled_arrival": 10.5,
                "scheduled_departure": 12.0,
                "simulated_status": "Running On Time (Timetable Isolated)",
                "delay_mins": 0,
                "label": "SIMULATED TIMETABLE",
                "message": "Live API provider is not configured in environment variables. Set TRAIN_API_KEY in backend .env to query real-time NTES / Indian Railways API.",
                "last_updated": datetime.now().strftime("%H:%M:%S IST")
            }

        # If configured with external provider, perform real HTTP call here
        import urllib.request
        import json
        try:
            url = f"{self.base_url}/live/{train_num}?key={self.api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "RailwayBlockPlanner/2.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return {
                    "status": "SUCCESS",
                    "configured": True,
                    "train_number": train_num,
                    "label": "LIVE DATA",
                    "data": data,
                    "last_updated": datetime.now().strftime("%H:%M:%S IST")
                }
        except Exception as e:
            return {
                "status": "ERROR",
                "configured": True,
                "train_number": train_num,
                "label": "LIVE STATUS UNAVAILABLE",
                "message": f"External provider request failed: {str(e)}",
                "last_updated": datetime.now().strftime("%H:%M:%S IST")
            }

train_provider = TrainDataProvider()
