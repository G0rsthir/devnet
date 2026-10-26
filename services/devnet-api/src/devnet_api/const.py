from enum import StrEnum


class RefreshScope(StrEnum):
    TOKEN_REFRESH = "token:refresh"


class AccessScope(StrEnum):
    SYSTEM_NETBOX = "system:netbox"
