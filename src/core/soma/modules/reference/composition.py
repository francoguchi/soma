from dataclasses import dataclass
from soma.foundation.appearance import setting_registration
from soma.modules.reference.application.settings import Settings
from soma.modules.reference.domain.settings import SettingDefinition, SettingDefinitionRegistry

from soma.modules.reference.application.dispatch import DispatchLocations
from soma.modules.reference.application.lifecycle import ReferenceLifecycle
from soma.modules.reference.domain.dependencies import ReferenceDependencyRegistry
from soma.modules.reference.application.customer import Customers
from soma.modules.reference.application.contact import Contacts
from soma.modules.reference.adapters.communication import Communication
from soma.modules.reference.application.profile import Profile
from soma.modules.reference.audit import reference_audit_writer
from soma.modules.reference.adapters.persistence.matching_profile import (
    require_persisted_matching_profile,
)
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.errors import SomaError


@dataclass(frozen=True)
class Reference:
    profile: Profile
    customers: Customers
    contacts: Contacts
    communication: Communication
    dispatch: DispatchLocations
    lifecycle: ReferenceLifecycle
    settings: Settings


def compose(
    factory, *, dependency_validators=(), required_validator_ids=(), setting_definitions=()
):
    settings = SettingDefinitionRegistry()
    settings.register(SettingDefinition(**setting_registration()))
    for definition in setting_definitions:
        settings.register(definition)
    settings.finalize()
    dependencies = ReferenceDependencyRegistry()
    for validator in dependency_validators:
        dependencies.register(validator)
    dependencies.finalize(required_validator_ids=required_validator_ids)
    writer = reference_audit_writer()
    assembled = Reference(
        Profile(factory, writer),
        Customers(factory, writer),
        Contacts(factory, writer),
        Communication(),
        DispatchLocations(factory, writer),
        ReferenceLifecycle(factory, writer, dependencies),
        Settings(factory, writer, settings),
    )
    with ReadSnapshot(factory) as snapshot:
        require_persisted_matching_profile(snapshot.connection)
        credential = snapshot.connection.execute(
            "SELECT actor_id FROM local_admin_credentials"
        ).fetchone()
        profile = snapshot.connection.execute(
            "SELECT local_user_profile_id FROM local_user_profiles"
        ).fetchone()
        if credential is not None and (profile is None or profile[0] != credential[0]):
            raise SomaError(
                "PROFILE_SETUP_INCOMPLETE",
                "Configured development instance requires explicit reset before Reference composition.",
                "restart",
            )
    return assembled
