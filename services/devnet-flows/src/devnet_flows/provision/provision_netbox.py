async def provision_netbox(netbox: NetboxConfig, provision: NetboxProvision, *, dry_run: bool) -> None:
    async with NetboxClient(netbox) as client:
        # Later, first: the objects packages declare, in order: choice sets, custom fields, tags
        webhook = Webhook(
            name="devnet",
            payload_url=provision.webhook_url,
            additional_headers=SecretStr(f"Authorization: Bearer {provision.webhook_token.get_secret_value()}"),
            ssl_verification=provision.webhook_verify_tls,
        )
        webhook_id = await ensure(client, webhook, dry_run=dry_run)
        rule = EventRule(
            name="devnet: device changed",
            object_types=["dcim.device"],
            event_types=["object_created", "object_updated", "object_deleted"],
            action_object_id=webhook_id,
        )
        await ensure(client, rule, dry_run=dry_run)
