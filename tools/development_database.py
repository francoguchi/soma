"""Resolve and bootstrap/reset only the designated source development database."""

import argparse
from pathlib import Path

from soma.foundation.config import RuntimeConfig
from soma.foundation.development.database import factory_for_lease, rebuild
from soma.foundation.persistence.instance import InstanceLease
from soma.foundation.persistence.migrations import MigrationRunner
from soma.foundation.persistence.manifest import MigrationManifest
from soma.foundation.persistence.schema_verify import verify_schema
from soma.foundation.persistence.snapshot import SnapshotProvider

ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=("resolve", "bootstrap", "reset", "verify", "snapshot")
    )
    parser.add_argument("--confirm")
    parser.add_argument("--output", help="Snapshot path relative to the instance backups root")
    args = parser.parse_args()
    config = RuntimeConfig.discover(ROOT)
    print(f"Development instance: {config.instance_root}")
    print(f"Runtime record present: {config.path('runtime', 'runtime.json').exists()}")
    if args.operation == "reset":
        print(f"Rebuilt instance: {rebuild(config, confirmation=args.confirm)}; stopped")
    elif args.operation != "resolve":
        with InstanceLease(config) as lease:
            factory = factory_for_lease(lease)
            if args.operation == "bootstrap":
                print(
                    f"Verified schema generation: {MigrationRunner(factory).initialize_or_migrate()}"
                )
            elif args.operation == "snapshot":
                if args.output is None:
                    parser.error("snapshot requires --output")
                descriptor = SnapshotProvider(factory).create(args.output)
                print(
                    f"Verified encrypted snapshot: {descriptor.path}; {descriptor.size_bytes} bytes; {descriptor.sha256}"
                )
            else:
                connection = factory.open(read_only=True)
                try:
                    verify_schema(
                        connection,
                        MigrationManifest.load(),
                        instance_id=lease.instance_id,
                        deep=True,
                    )
                    print("Protected schema, identity, ledger, FK, and integrity checks passed")
                finally:
                    connection.close()
