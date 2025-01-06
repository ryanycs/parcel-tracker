import logging
import re
from typing import Final

import requests
from bs4 import BeautifulSoup

from .base import Tracker, TrackingInfo
from .enums import Platform

VALIDATE_URL: Final = "https://ecservice.okmart.com.tw/Tracking/ValidateNumber.ashx"
RESULT_URL: Final = "https://ecservice.okmart.com.tw/Tracking/Result"


class OKMartTracker(Tracker):
    def __init__(self) -> None:
        self.session = requests.Session()
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        try:
            data = OKMartRequestHandler().get_data(order_id)
        except Exception as e:
            logging.error(f"[OKMart] {e}")
            return None

        self.tracking_info = OKMartTrackingInfoAdapter.convert(data)

        return self.tracking_info


class OKMartRequestHandler:
    def __init__(self):
        """
        Request handler for OKMart website

        Parameters
        ----------
        max_retry : int
            The maximum number of retries when the captcha is incorrect
        """

        self.session = requests.Session()

    def get_data(self, order_id: str) -> dict:
        """
        Get the tracking information froms OKMart website

        Parameters
        ----------
        order_id : str
            The order_id of the parcel

        Returns
        -------
        dict | None
            The tracking information of the parcel in `dict`, or `None` if failed
        """

        validate_code = self._get_validate_code()

        if validate_code is None:
            raise RuntimeError("Failed to get validate code")

        response = self._get_search_result(order_id, validate_code)
        result = OKMartResponseParser(response.text).parse()

        return result

    def _get_validate_code(self) -> str | None:
        logging.info("[OKMart] Getting validate code...")
        response = self.session.get(VALIDATE_URL)

        cookie = response.headers["Set-Cookie"]
        matchobj = re.search(r"ValidateNumber=code=(.....); path=/", cookie)
        if matchobj:
            return matchobj.group(1)

    def _get_search_result(
        self, order_id: str, validate_code: str
    ) -> requests.Response:
        logging.info("[OKMart] Getting search result...")
        headers = {
            "Cookie": f"ValidateNumber=code={validate_code}&odno={order_id}&cutknm=&cutktl="
        }
        params = {"inputOdNo": order_id, "inputCode1": validate_code}

        response = self.session.get(RESULT_URL, params=params, headers=headers)
        return response


class OKMartResponseParser:
    def __init__(self, html: str) -> None:
        """
        Parser for OKMart tracking response

        Parameters
        ----------
        html : str
            The html content of the response
        """

        self.soup = BeautifulSoup(html, "html.parser")
        self.result = {}

    def parse(self) -> dict:
        """
        Parse the response and extract the information

        Returns
        -------
        dict
            The extracted information
        """

        self.result["triNo"] = self._find_by_class_name("triNo")  # 寄件編號
        self.result["odNo"] = self._find_by_class_name("odNo")  # 訂單編號
        self.result["type"] = self._find_by_class_name("type")  # 類別
        self.result["status"] = self._find_by_class_name("status")  # 目前貨況
        self.result["stNo"] = self._find_by_class_name("stNo")  # 取件門市店號
        self.result["stNm"] = self._find_by_class_name("stNm")  # 取件門市名稱
        tags = self.soup.find_all(class_="stNm")
        self.result["stNm2"] = tags[1].text if len(tags) > 1 else None  # 取件門市地址
        self.result["takeFrom"] = self._find_by_class_name("takeFrom")  # 貨到門市日期
        self.result["takeTo"] = self._find_by_class_name("takeTo")  # 取貨截止
        self.result["takeAt"] = self._find_by_class_name("takeAt")  # 取貨日期
        self.result["taker"] = self._find_by_class_name("taker")  # 取件人

        return self.result

    def _find_by_class_name(self, class_name: str) -> str | None:
        tag = self.soup.find(class_=class_name)
        if tag:
            return tag.text.strip()
        else:
            return None


class OKMartTrackingInfoAdapter:
    @staticmethod
    def convert(raw_data: dict) -> TrackingInfo | None:
        """
        Convert the raw data to `TrackingInfo` object

        Parameters
        ----------
        raw_data : dict | None
            The raw data from the 7-11 e-tracking website

        Returns
        -------
        TrackingInfo | None
            A `TrackingInfo` object with the status details of the parcel,
            or `None` if no information is available.
        """

        if raw_data["odNo"] is None:
            return None

        order_id = raw_data["odNo"]
        status = raw_data["status"]
        # TODO: Check the message of status is arrived
        is_delivered = raw_data["status"] == "已送達" or raw_data["status"] == "已取貨"

        return TrackingInfo(
            order_id=order_id,
            platform=Platform.OKMart.value,
            time=None,
            status=status,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )
