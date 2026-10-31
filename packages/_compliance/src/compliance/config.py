# compliance/config.py. The rule kinds are made up; they show where a union fits
class MustContain(ConfigModel):
    kind: Literal["must_contain"]
    lines: list[str]


class MustNotMatch(ConfigModel):
    kind: Literal["must_not_match"]
    pattern: str


type Rule = Annotated[MustContain | MustNotMatch, Field(discriminator="kind")]
