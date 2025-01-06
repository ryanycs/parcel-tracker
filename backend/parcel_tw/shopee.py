import logging
import time
from hashlib import sha256
from typing import Final

import requests

from .base import Tracker, TrackingInfo
from .enums import Platform

SEARCH_URL: Final = "https://spx.tw/api/v2/fleet_order/tracking/search"
SALT: Final = b"MGViZmZmZTYzZDJhNDgxY2Y1N2ZlN2Q1ZWJkYzlmZDY="  # Shopee API hashing salt


class ShopeeTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        try:
            data = ShopeeRequestHandler().get_data(order_id)
        except Exception as e:
            logging.error(f"[Shopee] {e}")
            return None

        logging.info("[Shopee] Parsing the response...")
        self.tracking_info = ShopeeTrackingInfoAdapter.convert(data)

        return self.tracking_info


class ShopeeRequestHandler:
    def __init__(self):
        self.session = requests.Session()

    def get_data(self, order_id: str) -> dict:
        """
        Get tracking info from Shopee API

        Parameters:
        -----------
        order_id: str
            Shopee order ID

        Returns:
        --------
        dict
            The tracking information of the parcel in `dict`, or `None` if failed
        """

        timestamp = int(time.time())
        headers = {
            "cookie": "fms_language=tw",
        }
        params = {
            "sls_tracking_number": order_id
            + "|"
            + str(timestamp)
            + sha256(order_id.encode() + str(timestamp).encode() + SALT).hexdigest()
        }
        logging.info(f"[Shopee] Requesting tracking info for order {order_id}...")
        response = self.session.get(SEARCH_URL, params=params, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Failed to get tracking info from Shopee API: {response.text}"
            )

        return response.json()


class ShopeeTrackingInfoAdapter:
    @staticmethod
    def convert(raw_data: dict) -> TrackingInfo | None:
        """
        Convert the raw data to `TrackingInfo` object

        Parameters
        ----------
        raw_data : dict
            The raw data from the Shopee API

        Returns
        -------
        TrackingInfo | None
            A `TrackingInfo` object with the status details of the parcel,
            or `None` if no information is available.
        """

        data = raw_data["data"]
        if data is None or len(data) == 0:
            return None

        order_id = data.get("sls_tracking_number")

        tracking_list = data.get("tracking_list")

        latest_status = tracking_list[0]
        latest_status_message = latest_status.get("message")

        timestamp = latest_status.get("timestamp")
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        status = latest_status.get("status")
        is_delivered = (
            "SP_Ready_Collection" in status or "SP_Collection_Collected" in status
        )

        return TrackingInfo(
            order_id=order_id,
            platform=Platform.Shopee.value,
            status=latest_status_message,
            time=datetime,
            is_delivered=is_delivered,
            raw_data=data,
        )
