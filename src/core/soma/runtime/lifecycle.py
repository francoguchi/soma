"""Process-local, one-way host lifecycle; absence belongs to controllers."""

TRANSITIONS = {
    "BOOTSTRAPPING": {"MIGRATING", "FAILED"},
    "MIGRATING": {"BINDING", "FAILED"},
    "BINDING": {"SERVING_NOT_READY", "FAILED"},
    "SERVING_NOT_READY": {"READY", "QUIESCING", "FAILED"},
    "READY": {"QUIESCING", "FAILED"},
    "QUIESCING": {"EXITING", "FAILED"},
    "EXITING": set(),
    "FAILED": set(),
}
