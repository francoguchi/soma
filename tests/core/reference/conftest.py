import pytest

from soma.foundation.config import RuntimeConfig
from soma.foundation.development.database import factory_for_lease
from soma.foundation.persistence.instance import InstanceLease
from soma.foundation.persistence.manifest import MigrationManifest
from soma.foundation.persistence.migrations import MigrationRunner
from soma.modules.reference.composition import compose


@pytest.fixture
def reference(tmp_path):
    config = RuntimeConfig(tmp_path / "instance", tmp_path / "checkout", "test")
    with InstanceLease(config) as lease:
        factory = factory_for_lease(lease)
        manifest = MigrationManifest.load()
        MigrationRunner(factory, manifest).initialize_or_migrate()
        yield compose(factory), factory, manifest
