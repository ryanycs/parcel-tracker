from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TrackingInfo:
    order_id: str
    platform: str
    status: str
    time: str | None
    is_delivered: bool
    raw_data: dict = field(repr=False)


class Tracker(ABC):
    @abstractmethod
    def track_status(self, order_id: str) -> TrackingInfo | None:
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
        pass
