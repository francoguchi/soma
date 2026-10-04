import threading

from soma.foundation.audit import AuditContract, AuditEvent, AuditWriter
from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import new_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.security.passwords import AuthenticationThrottle, Passwords
from soma.foundation.transactions import CommandBoundary, ResultContract
from soma.foundation.time import utc_epoch_seconds


class Authentication:
    def __init__(self, factory, sessions, log):
        self.factory, self.sessions, self.log = factory, sessions, log
        self.passwords, self.throttle = Passwords(), AuthenticationThrottle()
        self.setup_lock = threading.Lock()
        self.login_lock = threading.Lock()

        def validate_payload(value):
            if value != {"credential_version": 1}:
                raise ValidationError("Invalid authentication audit payload.")

        def validate_result(value):
            from soma.foundation.identity import require_uuid4

            if type(value) is not dict or set(value) != {"actor_id"}:
                raise ValidationError()
            require_uuid4(value["actor_id"])

        writer = AuditWriter(
            [
                AuditContract(
                    "foundation.local_admin_configured",
                    1,
                    "LocalAdminConfiguredV1",
                    1,
                    validate_payload,
                    lambda v: False,
                )
            ]
        )
        self.boundary = CommandBoundary(
            factory, [ResultContract("LocalAdminConfiguredResultV1", 1, validate_result)], writer
        )

    def credential(self):
        with ReadSnapshot(self.factory) as snapshot:
            rows = snapshot.connection.execute(
                "SELECT actor_id,password_phc FROM local_admin_credentials LIMIT 2"
            ).fetchall()
        if len(rows) > 1:
            raise SomaError("AUTH_INVALID_CREDENTIALS", "The password could not be verified.")
        return rows[0] if rows else None

    def state(self):
        return "login_required" if self.credential() else "setup_required"

    def setup(self, password, confirmation):
        # Expensive password hashing and random credential issuance precede the write.
        with self.setup_lock:
            if self.credential() is not None:
                raise SomaError(
                    "AUTH_ALREADY_CONFIGURED", "Local Administrator is already configured."
                )
            phc = self.passwords.hash(password, confirmation)
            actor = new_uuid4()
            token, csrf = self.sessions.issue(actor)
            command = new_uuid4()

            def operation(uow):
                if uow.connection.execute(
                    "SELECT singleton_key FROM local_admin_credentials"
                ).fetchone():
                    raise SomaError(
                        "AUTH_ALREADY_CONFIGURED", "Local Administrator is already configured."
                    )
                now = utc_epoch_seconds()
                uow.connection.execute(
                    "INSERT INTO local_admin_credentials VALUES (1,?,?,1,?,?)",
                    (actor, phc, now, now),
                )
                event = AuditEvent(
                    new_uuid4(),
                    "foundation.local_admin_configured",
                    1,
                    "local_admin",
                    "local_admin",
                    command,
                    {"credential_version": 1},
                    actor_id=actor,
                    target_id=actor,
                )
                return {"actor_id": actor}, [event]

            try:
                # Secret bytes/verifier are closure-only: never request/replay/audit JSON.
                self.boundary.execute(
                    command,
                    "foundation.configure_local_admin",
                    {"actor_id": actor},
                    ("LocalAdminConfiguredResultV1", 1),
                    operation,
                )
            except BaseException:
                self.sessions.revoke(token)
                raise
            return token, csrf

    def login(self, password):
        with self.login_lock:
            self.throttle.check()
            row = self.credential()  # read connection closes before Argon2
            success = row is not None and self.passwords.verify(row[1], password)
            self.throttle.record(success)
            if not success:
                self.log.emit("AUTH_INVALID_CREDENTIALS")
                raise SomaError(
                    "AUTH_INVALID_CREDENTIALS",
                    "The password could not be verified. Try again shortly.",
                    "correct_input",
                )
            return self.sessions.issue(row[0])
