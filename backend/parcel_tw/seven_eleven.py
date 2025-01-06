import io
import logging
import re
from typing import Final

import pytesseract
import requests
from bs4 import BeautifulSoup, Tag
from PIL import Image

from .base import Tracker, TrackingInfo
from .enums import Platform

BASE_URL: Final = "https://eservice.7-11.com.tw/e-tracking/"
SEARCH_URL: Final = BASE_URL + "search.aspx"


class SevenElevenTracker(Tracker):
    def __init__(self):
        self.tracking_info = None

    def track_status(self, order_id: str) -> TrackingInfo | None:
        if not self._validate_order_id(order_id):
            return None

        try:
            data = SevenElevenRequestHandler().get_data(order_id)
        except Exception as e:
            logging.error(f"[7-11] {e}")
            return None

        self.tracking_info = SevenElevenTrackingInfoAdapter.convert(data)

        return self.tracking_info

    def _validate_order_id(self, order_id: str) -> bool:
        return len(order_id) == 8 or len(order_id) == 11 or len(order_id) == 12


class SevenElevenRequestHandler:
    def __init__(self, max_retry: int = 5):
        """
        Request handler for 7-11 e-tracking website

        Parameters
        ----------
        max_retry : int
            The maximum number of retries when the captcha is incorrect
        """

        self.session = requests.Session()
        self.max_retry = max_retry

    def get_data(self, order_id) -> dict | None:
        """
        Get the tracking information froms 7-11 e-tracking website

        Parameters
        ----------
        order_id : str
            The order_id of the parcel

        Returns
        -------
        dict | None
            The tracking information of the parcel in `dict`, or `None` if failed
        """

        retry_counter = 0
        while retry_counter < self.max_retry:
            try:
                logging.info(f"[7-11] Requesting tracking info for order {order_id}...")
                response = self._post_search(order_id)
                result = SevenElevenResponseParser(response.text).parse()
                if result["msg"] == "驗證碼錯誤!!":
                    retry_counter += 1
                    raise ValueError("Incorrect captcha")
                return result
            except ValueError:
                logging.warning(
                    f"[7-11] Captcha is incorrect, retrying... ({retry_counter}/{self.max_retry})"
                )

        return None

    def _post_search(self, order_id: str) -> requests.Response:
        """
        Post the search request to the 7-11 e-tracking website

        Parameters
        ----------
        order_id : str
            The order_id of the parcel

        Returns
        -------
        requests.Response
            The response of the search request
        """

        response = self.session.get(SEARCH_URL)
        if response.status_code != 200:
            raise Exception("Failed to get search page")

        payload = self._construct_payload(response, order_id)
        response = self.session.post(SEARCH_URL, data=payload)
        if response.status_code != 200:
            raise Exception("Failed to post search request")
        return response

    def _construct_payload(self, response: requests.Response, order_id) -> dict:
        soup = BeautifulSoup(response.text, "html.parser")
        view_state = self._find_value_by_id(soup, "__VIEWSTATE")
        view_state_generator = self._find_value_by_id(soup, "__VIEWSTATEGENERATOR")
        validate_code = SevenElevenCaptchaSolver(
            self.session, response.text
        ).get_validate_code()
        payload = {
            "__EVENTTARGET": "submit",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": view_state,
            "__VIEWSTATEGENERATOR": view_state_generator,
            "txtProductNum": order_id,
            "tbChkCode": validate_code,
            "txtIMGName": "",
            "txtPage": 1,
        }
        return payload

    def _find_value_by_id(self, soup: BeautifulSoup, id: str) -> str | None:
        tag = soup.find("input", id=id)
        if isinstance(tag, Tag):
            value = tag.get("value")
            if isinstance(value, str):
                return value
        return None


class SevenElevenCaptchaSolver:
    def __init__(self, session: requests.Session, html: str):
        """
        Captcha solver for 7-11 e-tracking website

        Paramaters
        ----------
        session : requests.Session
            The session object for sending requests
        html : str
            The html content of the search page
        """

        self.session = session
        self.html = html

    def get_validate_code(self) -> str:
        """
        Get the validate code from the captcha image

        Returns
        -------
        str
            The validate code
        """

        validate_image = self._get_validate_image()
        tesseract_config = "-c tessedit_char_whitelist=0123456789 --psm 8"
        validate_code = pytesseract.image_to_string(
            validate_image, config=tesseract_config
        ).strip()
        return validate_code

    def _get_validate_image(self) -> Image.Image:
        validate_image_url = self._get_validate_image_url()
        response = self.session.get(validate_image_url)
        if response.status_code != 200:
            raise Exception("Failed to get validate image")
        return Image.open(io.BytesIO(response.content))

    def _get_validate_image_url(self) -> str:
        url_suffix = re.search(r'src="(ValidateImage\.aspx\?ts=[0-9]+)"', self.html)
        if url_suffix is not None:
            return BASE_URL + url_suffix.group(1)
        else:
            raise Exception("Failed to get validate image url")


class SevenElevenResponseParser:
    def __init__(self, html: str):
        """
        Parser for 7-11 e-tracking response

        Parameters
        ----------
        html : str
            The html content of the response
        """

        self.soup = BeautifulSoup(html, "html.parser")
        self.result = {
            "msg": None,
            "m_news": None,
            "result": {"info": None, "shipping": None},
        }

    def parse(self) -> dict:
        """
        Parse the response and extract the information

        Returns
        -------
        dict
            The extracted information
        """

        # Check if there is any alert message in the script tag
        script_tags = self.soup.find_all("script")
        for tag in script_tags:
            text = tag.get_text()
            if "alert(" in text:
                self.result["msg"] = self._extract_alert_message(text)
                return self.result

        # Check if there is any error message
        error_message = self.soup.find("span", id="lbMsg")
        if error_message is not None:
            self.result["msg"] = error_message.get_text()
            return self.result

        self.result["m_news"] = self._extract_m_news_message()
        self.result["result"]["info"] = self._extract_info_message()
        self.result["result"]["shipping"] = self._extract_shipping_message()
        self.result["msg"] = "success"

        return self.result

    def _extract_alert_message(self, text: str) -> str:
        return text.split("alert('")[1].split("');")[0]

    def _extract_m_news_message(self) -> str:
        m_news = self.soup.find("div", {"class": "m_news"})
        if isinstance(m_news, Tag):
            return m_news.get_text()
        else:
            return ""

    def _extract_info_message(self) -> dict:
        res = {}
        info_tag = self.soup.find("div", class_="info")
        if isinstance(info_tag, Tag):
            infos = info_tag.find_all("span")
            for info in infos:
                res[info.get("id")] = info.get_text()

            service_type = info_tag.find("h4", id="servicetype")
            if service_type is not None:
                res["servicetype"] = service_type.get_text()
        return res

    def _extract_shipping_message(self) -> list:
        res = []
        shipping_tag = self.soup.find("div", class_="shipping")
        if isinstance(shipping_tag, Tag):
            shippings = shipping_tag.find_all("p")
            for shipping in shippings:
                res.append(shipping.get_text())
        return res


class SevenElevenTrackingInfoAdapter:
    @staticmethod
    def convert(raw_data: dict | None) -> TrackingInfo | None:
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

        if raw_data is None or raw_data["result"]["info"] is None:
            return None

        order_id = raw_data["result"]["info"]["query_no"]

        # Extract status and time from m_news
        pattern = r"(.*)(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"
        match_obj = re.match(pattern, raw_data["m_news"])
        if match_obj is not None:
            status = match_obj.group(1)
            time = match_obj.group(2)
        else:
            return None

        is_delivered = "包裹配達取件門市" in status or "已完成包裹成功取件" in status

        return TrackingInfo(
            order_id=order_id,
            platform=Platform.SevenEleven.value,
            status=status,
            time=time,
            is_delivered=is_delivered,
            raw_data=raw_data,
        )
