cli = Typer(no_args_is_help=True)


@cli.command()
def provision(
    dry_run: Annotated[bool, Option("--dry-run", help="Show what would change, write nothing")] = False,
):
    """
    Create or update the Prefect objects devnet-flows needs
    """
    try:
        asyncio.run(provision_prefect(dry_run=dry_run))
    except ConfigurationError as e:
        echo(str(e), err=True)
        raise Exit(1) from e
