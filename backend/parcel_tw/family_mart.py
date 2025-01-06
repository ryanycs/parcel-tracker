import json
import logging
import ssl

import requests
from requests.adapters import HTTPAdapter

from .base import Tracker, TrackingInfo
from .enums import Platform


# stackoveflow solution for requests.exceptions.SSLError
# https://stackoverflow.com/questions/77303136
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.options |= 0x4
        kwargs["ssl_context"] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


class FamilyMartTracker(Tracker):
    SEARCH_URL = "https://ecfme.fme.com.tw/FMEDCFPWebV2_II/list.aspx/GetOrderDetail"

    def __init__(self):
        self.session = requests.Session()
        self.session.mount("https://", TLSAdapter())  # used to avoid SSLError
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        headers = {"Content-Type": "application/json; charset=UTF-8"}

        payload = {"EC_ORDER_NO": order_id, "ORDER_NO": order_id, "RCV_USER_NAME": None}
        logging.info("[FamilyMart] Sending post request to the search page...")
        response = self.session.post(self.SEARCH_URL, json=payload, headers=headers)

        logging.info("[FamilyMart] Parsing the response...")
        raw_data = self._parse_response(response.text)
        self.tracking_info = self._convert_to_tracking_info(raw_data)

        return self.tracking_info

    def _parse_response(self, response):
        s = response.replace("\\", "")
        json_data = json.loads(s[6:-2])

        return json_data

    def _convert_to_tracking_info(self, raw_data) -> TrackingInfo | None:
        if len(raw_data["List"]) == 0:
            return None

        status_list = raw_data["List"]
        latest_status = status_list[0]  # First element in the list is the latest status

        order_id = latest_status["ORDER_NO"]
        time = latest_status["ORDER_DATE_R"] + ":00"  # Add seconds to the time
        status_message = latest_status["STATUS_D"]
        is_delivered = (
            "貨件配達取件店舖" in status_message or "已完成取件" in status_message
        )
        return TrackingInfo(
            order_id=order_id,
            platform=Platform.FamilyMart.value,
            status=status_message,
            time=time,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )
