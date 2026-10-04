import re
from dataclasses import asdict, dataclass
from importlib.resources import files

from soma.foundation.errors import ValidationError
from soma.foundation.strict_json import loads_strict


@dataclass(frozen=True, slots=True)
class BuildIdentity:
    application_version: str
    runtime_protocol_version: int
    contract_generation: int
    migration_generation: int
    schema_generation: int
    source_commit: str | None
    dirty: bool | None
    build_kind: str

    def __post_init__(self) -> None:
        if self.application_version != "0.1.0.dev0" or self.build_kind != "source":
            raise ValidationError("Unsupported application build identity.")
        for value in (self.runtime_protocol_version, self.contract_generation):
            if type(value) is not int or value != 1:
                raise ValidationError("Incompatible protocol or contract identity.")
        for value in (self.migration_generation, self.schema_generation):
            if type(value) is not int or value < 0:
                raise ValidationError("Invalid schema or migration identity.")
        if self.dirty is not None and type(self.dirty) is not bool:
            raise ValidationError("Invalid source state.")
        if self.source_commit is not None and (
            type(self.source_commit) is not str
            or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", self.source_commit)
        ):
            raise ValidationError("Invalid source commit identity.")

    def as_dict(self) -> dict:
        return asdict(self)


def current_build() -> BuildIdentity:
    return BuildIdentity(
        **loads_strict(files(__package__).joinpath("identity.json").read_text(encoding="utf-8"))
    )
