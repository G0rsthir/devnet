from enum import StrEnum


class RefreshScope(StrEnum):
    TOKEN_REFRESH = "token:refresh"


class AccessScope(StrEnum):
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
