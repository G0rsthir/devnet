from devnet_core.connections.config import SystemConfig
from devnet_core.exceptions import SystemConnectionError
from devnet_core.settings.file import ConfigModel
from devnet_core.settings.types import EnvSecret


class NetboxConfig(ConfigModel):
    name: str = "netbox"
    base_url: str
    token: EnvSecret
    verify_tls: bool = True


def build_config(
    *,
    name: str,
    host: str,
    verify_tls: bool,
    profile: ORMCredentialProfile | None,
) -> NetboxConfig:
    """
    Raises:
        SystemConnectionError: If the credentials can't be used to log in.
    """
    if problem := credential_profile_problem(profile):
        raise SystemConnectionError(source_name=name, msg=problem)
    assert profile is not None and profile.username and profile.password

    return NetboxConfig(
        name=name,
        base_url=host,
        verify_tls=verify_tls,
    )


def config_from_dict(config: SystemConfig) -> NetboxConfig:
    return build_config(
        name=source.name,
        host=source.host,
        verify_tls=source.is_certificate_validation_enabled,
        profile=source.credential_profile,
    )
