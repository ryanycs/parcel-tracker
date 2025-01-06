from .base import Tracker, TrackingInfo
from .enums import Platform
from .family_mart import FamilyMartTracker
from .okmart import OKMartTracker
from .seven_eleven import SevenElevenTracker
from .shopee import ShopeeTracker


class TrackerFactory:
    @staticmethod
    def create_tracker(platform: Platform) -> Tracker:
        """
        Create a tracker based on the platform

        Parameters
        ----------
        platform : Platform
            The platform of the parcel

        Returns
        -------
        Tracker
            A tracker object for the specified platform

        Raises
        ------
        ValueError
            If the platform is not supported
        """

        match platform:
            case Platform.SevenEleven:
                return SevenElevenTracker()
            case Platform.FamilyMart:
                return FamilyMartTracker()
            case Platform.OKMart:
                return OKMartTracker()
            case Platform.Shopee:
                return ShopeeTracker()
            case _:
                raise ValueError(f"Invalid platform: {platform}")


def track(platform: Platform, order_id: str) -> TrackingInfo | None:
    """
    Track the parcel status by order_id

    Parameters
    ----------
    order_id : str
        The order_id of the parcel

    Returns
    -------
    TrackingInfo | None
        A `TrackingInfo` object with the status details of the parcel,
        or `None` if no information is available.
    """

    tracker = TrackerFactory.create_tracker(platform)
    return tracker.track_status(order_id)
