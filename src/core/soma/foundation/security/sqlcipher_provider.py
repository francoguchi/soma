from importlib.metadata import PackageNotFoundError, version

from soma.foundation.security.dpapi import security_failure


class SqlCipherSecurity:
    def __init__(self, live_key):
        self.live_key = live_key

    def key_connection(self, connection) -> None:
        try:
            if version("sqlcipher3") != "0.6.2":
                raise security_failure()
            key = self.live_key.unwrap_live_dek()
            if type(key) is not bytes or len(key) != 32:
                raise security_failure()
            connection.execute("PRAGMA cipher_memory_security=ON")
            # PRAGMA key has no parameter slot. Only a fixed-length CSPRNG key's hex
            # is inserted; no SQL text or caller string is accepted here.
            connection.execute("PRAGMA key = \"x'" + key.hex() + "'\"")
        except PackageNotFoundError:
            raise security_failure() from None
        finally:
            key = None

    def verify(self, connection) -> None:
        try:
            cipher = connection.execute("PRAGMA cipher_version").fetchone()
            if cipher is None or cipher[0] not in {
                "4.17.0",
                "4.17.0 community",
                "4.17.0 enterprise",
            }:
                raise security_failure()
            for name, expected in [
                ("cipher_page_size", "4096"),
                ("cipher_use_hmac", "1"),
                ("cipher_plaintext_header_size", "0"),
                ("cipher_memory_security", "1"),
                ("cipher_hmac_algorithm", "HMAC_SHA512"),
            ]:
                row = connection.execute(f"PRAGMA {name}").fetchone()
                if row is None or str(row[0]) != expected:
                    raise security_failure()
            connection.execute("SELECT count(*) FROM sqlite_schema").fetchone()
        except Exception:
            raise security_failure() from None
