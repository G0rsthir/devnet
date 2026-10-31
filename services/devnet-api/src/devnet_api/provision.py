from datetime import UTC, datetime, timedelta

from pydantic import ValidationError

from devnet_api.const import AccessScope
from devnet_api.services.token import AuthTokenService
from devnet_config import get_config
from devnet_core.exceptions import ConfigurationError
from devnet_core.settings import ConfigModel
from system_netbox.client import NetboxClient
from system_netbox.config import NetboxConfig
from system_netbox.models.generated import WebhookRequest, WritableEventRuleRequest

# Provision again before this ends: NetBox's webhooks fail once the token expires
TOKEN_LIFETIME = timedelta(days=365)


class NetboxProvision(ConfigModel):
    # devnet-api endpoint that NetBox sends device changes to
    webhook_url: str


def netbox_provision_config() -> NetboxProvision:
    """
    Raises:
        ConfigurationError: If the provision.netbox section is missing or invalid
    """
    try:
        return NetboxProvision.model_validate(get_config().provision.get("netbox"))
    except ValidationError as e:
        raise ConfigurationError(f"provision.netbox: {e}") from e


async def provision_netbox(config: NetboxConfig, webhook_url: str, token_service: AuthTokenService) -> None:
    """
    Create or update the webhook and event rule that send NetBox device changes to devnet-api

    Issues a new token on every run. Earlier tokens stay valid until they expire
    """
    token = token_service.issue_access_token(
        sub="netbox",
        expires_at=datetime.now(UTC) + TOKEN_LIFETIME,
        scopes=[AccessScope.SYSTEM_NETBOX],
    )
    async with NetboxClient(config) as client:
        webhook = WebhookRequest(
            name="devnet",
            payload_url=webhook_url,
            # Holds the token: don't log this object
            additional_headers=f"Authorization: Bearer {token}",
        )
        webhook_id = await client.extras.webhooks.ensure(webhook)
        rule = WritableEventRuleRequest(
            name="devnet: device changed",
            object_types=["dcim.device"],
            event_types=["object_created", "object_updated", "object_deleted"],
            action_type="webhook",
            action_object_type="extras.webhook",
            action_object_id=webhook_id,
        )
        await client.extras.event_rules.ensure(rule)
