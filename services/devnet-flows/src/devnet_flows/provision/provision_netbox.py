async def provision_netbox(netbox: NetboxConfig, provision: NetboxProvision) -> None:
    async with NetboxClient(netbox) as client:
        # Later, first: the objects packages declare, in order: choice sets, custom fields, tags
        webhook = WebhookRequest(
            name="devnet",
            payload_url=provision.webhook_url,
            # Holds the token: don't log this object
            additional_headers=f"Authorization: Bearer {provision.webhook_token.get_secret_value()}",
            ssl_verification=provision.webhook_verify_tls,
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
