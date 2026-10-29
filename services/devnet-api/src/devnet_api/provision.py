async def provision_netbox(config: NetboxConfig, webhook_url: str, token: str, *, dry_run: bool) -> None:
    async with NetboxClient(config) as client:
        webhook = WebhookRequest(
            name="devnet",
            payload_url=webhook_url,
            # Holds the token: don't log this object
            additional_headers=f"Authorization: Bearer {token}",
        )
        webhook_id = await ensure(client, webhook, dry_run=dry_run)
        rule = WritableEventRuleRequest(
            name="devnet: device changed",
            object_types=["dcim.device"],
            event_types=["object_created", "object_updated", "object_deleted"],
            action_type="webhook",
            action_object_type="extras.webhook",
            action_object_id=webhook_id,
        )
        await ensure(client, rule, dry_run=dry_run)
