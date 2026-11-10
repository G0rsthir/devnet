from collections.abc import Iterable
from typing import Any, Protocol

from compliance.core.models import Device


class Source[T](Protocol):
    """
    Port: reads one kind of data about one device from one system

    An adapter is a class with these two members. It does not subclass Source.

    Args:
        provides: The class of the data, e.g. RunningConfig. A rule asks for the data by this class
    """

    provides: type[T]

    async def collect(self, device: Device) -> T:
        """
        Raises:
            Exception: If the system has no complete data for the device. Rules that need the data then get
                the outcome `error`
        """
        ...


# A list of sources of different kinds: `sources: list[AnySource] = [...]`
type AnySource = Source[Any]


class EvidenceError(Exception):
    """
    The data that a rule needs could not be collected
    """


class Evidence:
    """
    The data about one device, for one run

    A kind of data is collected at the first request, and one time only. If no rule asks for the
    running config, no session to the device opens.
    """

    def __init__(self, device: Device, sources: Iterable[AnySource]) -> None:
        self._device = device
        self._sources = {source.provides: source for source in sources}
        self._collected: dict[type, Any] = {}
        self._failed: dict[type, str] = {}

    async def get[T](self, kind: type[T]) -> T:
        """
        Raises:
            EvidenceError: If no source provides this kind, or the source failed. A failed source
                is not called again in this run
        """
        if kind in self._failed:
            raise EvidenceError(self._failed[kind])
        if kind not in self._collected:
            source = self._sources.get(kind)
            if source is None:
                self._failed[kind] = f"{kind.__name__}: no source is configured"
                raise EvidenceError(self._failed[kind])
            try:
                self._collected[kind] = await source.collect(self._device)
            except Exception as e:
                self._failed[kind] = f"{kind.__name__}: {e}"
                raise EvidenceError(self._failed[kind]) from e
        collected: T = self._collected[kind]
        return collected
