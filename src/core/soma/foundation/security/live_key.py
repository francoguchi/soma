import secrets

from soma.foundation.filesystem import atomic_write
from soma.foundation.filesystem.windows_acl import protect_owner
from soma.foundation.security.dpapi import WindowsDpapiProvider, security_failure


class LiveDataKeyProvider:
    def __init__(self, lease, *, dpapi=None):
        self.lease = lease
        self.dpapi = dpapi if dpapi is not None else WindowsDpapiProvider()

    def prepare(self) -> bytes:
        self.lease.require()
        config = self.lease.config
        path = config.path("data", "live-key.dpapi")
        if not path.exists():
            if config.path("data", "soma.db").exists():
                raise security_failure()
            secret = secrets.token_bytes(32)
            protected = self.dpapi.protect_current_user(
                secret, "live_data_dek", self.lease.instance_id
            )
            atomic_write(
                config.instance_root, "data/live-key.dpapi", protected, protect=protect_owner
            )
        return self.unwrap_live_dek()

    def unwrap_live_dek(self) -> bytes:
        self.lease.require()
        try:
            path = self.lease.config.path("data", "live-key.dpapi")
            if not path.is_file() or path.stat().st_size > 65664:
                raise security_failure()
            value = self.dpapi.unprotect_current_user(
                path.read_bytes(), "live_data_dek", self.lease.instance_id
            )
            if type(value) is not bytes or len(value) != 32:
                raise security_failure()
            return value
        except OSError:
            raise security_failure() from None
