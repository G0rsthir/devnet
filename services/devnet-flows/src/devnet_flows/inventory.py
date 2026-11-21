from pydantic import BaseModel, ConfigDict


class _Parameter(BaseModel):
    """
    A flow parameter: the UI shows a form for it. Frozen, so one instance can be the default of a parameter
    """

    model_config = ConfigDict(frozen=True, extra="forbid")


class DeviceQuery(_Parameter):
    """
    The NetBox devices of a batch run. An empty field matches each device
    """

    # A device matches one of them
    names: tuple[str, ...] = ()
    # Slugs. A device matches one of them
    sites: tuple[str, ...] = ()
    roles: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ()
    # Slugs. A device matches only if it has each of them
    tags: tuple[str, ...] = ()

    def filters(self) -> dict[str, list[str]]:
        """
        The NetBox filters of the query, e.g. {"site": ["hq"], "tag": ["core"]}
        """
        fields = {
            "name": self.names,
            "site": self.sites,
            "role": self.roles,
            "platform": self.platforms,
            "tag": self.tags,
        }
        return {name: list(values) for name, values in fields.items() if values}


class InventoryDevice(BaseModel):
    """
    One device of a batch run, as select-devices reads it from NetBox. A task converts it into the input of its job
    """

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    # Slugs
    platform: str | None = None
    role: str
    site: str
    tags: tuple[str, ...] = ()
    # The primary IPv4 address, without its prefix length, e.g. 10.0.0.1
    primary_ip: str | None = None
