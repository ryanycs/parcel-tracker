import json

import requests

from .base import Tracker, TrackingInfo
from .enums import Platform


class LSATracker(Tracker):
    SEARCH_URL = "https://localhost:8000/packages/"

    def __init__(self):
        self.session = requests.Session()
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        response = self.session.get(self.SEARCH_URL + order_id)

        raw_data = json.loads(response.text)

        self.tracking_info = self._convert_to_tracking_info(raw_data)

        return self.tracking_info

    def _convert_to_tracking_info(self, raw_data) -> TrackingInfo | None:
        order_id = raw_data["package_id"]
        status = raw_data["status"]
        time = raw_data["status_time"]
        is_delivered = raw_data["status"] == "delivered"

        return TrackingInfo(
            order_id=order_id,
            platform=Platform.LSA,
            status=status,
            time=time,
            is_delivered=is_delivered,
            raw_data=raw_data
        )