from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, kw_only=True)
class SystemConfig:
    url: str | None = None
    username: str | None = None
    password: str | None = None
    token: str | None = None
    verify_tls: bool = True
    extra: dict[str, Any] = field(default_factory=dict)
