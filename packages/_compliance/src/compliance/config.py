from collections import Counter
from typing import Annotated, Self

from pydantic import Field, model_validator

from compliance.cisco import ConfigMustContain, ConfigMustNotMatch, VrfHasImportMap
from compliance.intent import ConfigMustContainNetbox
from compliance.netbox import NetboxMustHave
from devnet_core.settings import ConfigModel

# Each rule kind. `kind` in the config file selects the class
type AnyRule = Annotated[
    ConfigMustContain | ConfigMustNotMatch | VrfHasImportMap | NetboxMustHave | ConfigMustContainNetbox,
    Field(discriminator="kind"),
]


class ComplianceConfig(ConfigModel):
    """
    The `compliance` section of the config file
    """

    rules: tuple[AnyRule, ...] = ()

    @model_validator(mode="after")
    def _unique_names(self) -> Self:
        names = Counter(rule.name for rule in self.rules)
        if duplicates := sorted(name for name, count in names.items() if count > 1):
            raise ValueError(f"rule names must be unique: {', '.join(duplicates)}")
        return self
