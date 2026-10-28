class NetboxObject(ConfigModel):
    """
    An object devnet needs in NetBox. Fields left as None aren't compared or written, so people can change them
    """

    # API path, and the field that identifies an object of this kind
    endpoint: ClassVar[str]
    key: ClassVar[str] = "name"


class Webhook(NetboxObject):
    endpoint = "/api/extras/webhooks/"

    name: str
    payload_url: str
    # Holds the devnet-api token
    additional_headers: SecretStr
    ssl_verification: bool = True

    @field_serializer("additional_headers")
    def _reveal(self, value: SecretStr) -> str:
        return value.get_secret_value()


class EventRule(NetboxObject):
    endpoint = "/api/extras/event-rules/"

    name: str
    object_types: list[str]
    event_types: list[str]
    action_type: str = "webhook"
    action_object_type: str = "extras.webhook"
    # None only in a dry run, before the webhook exists
    action_object_id: int | None = None


def _matches(desired: Any, actual: Any) -> bool:
    # Choice fields read back as {"value": "select", "label": "Selection"}
    if isinstance(actual, dict) and "value" in actual and not isinstance(desired, dict):
        return desired == actual["value"]
    # object_types, event_types: order doesn't matter
    if isinstance(desired, list) and all(isinstance(v, str) for v in desired):
        return isinstance(actual, list) and sorted(desired) == sorted(actual)
    # Related objects read back in full: compare only the keys we set, e.g. {"name": ...}
    if isinstance(desired, dict) and isinstance(actual, dict):
        return all(_matches(v, actual.get(k)) for k, v in desired.items())
    return desired == actual


async def ensure(client: NetboxClient, obj: NetboxObject, *, dry_run: bool) -> int | None:
    """
    Create the object, or update the fields it sets that differ. Never deletes

    Returns:
        The object's ID. None in a dry run, if it doesn't exist yet
    """
    data = obj.model_dump(mode="json", exclude_none=True)
    key = data[obj.key]
    found = await client.find_one(obj.endpoint, **{obj.key: key})
    if found is None:
        logger.info("+ %s%s", obj.endpoint, key)
        return None if dry_run else (await client.create(obj.endpoint, data))["id"]
    # Log field names only: values can be secrets
    if changed := {k: v for k, v in data.items() if not _matches(v, found.get(k))}:
        logger.info("~ %s%s: %s", obj.endpoint, key, ", ".join(changed))
        if not dry_run:
            await client.update(obj.endpoint, found["id"], changed)
    else:
        logger.info("= %s%s", obj.endpoint, key)
    return found["id"]
