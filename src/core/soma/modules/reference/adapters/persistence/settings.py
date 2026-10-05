from soma.foundation.errors import ValidationError


def load(connection, key):
    return connection.execute(
        "SELECT contract_name,contract_version,value_json,revision FROM setting_values WHERE setting_key=?",
        (key,),
    ).fetchone()


def insert(connection, key, contract, version, raw, now, command):
    connection.execute(
        "INSERT INTO setting_values VALUES (?,?,?,?,1,?,?)",
        (key, contract, version, raw, now, command),
    )


def update(connection, key, contract, version, raw, rev, now, command):
    changed = connection.execute(
        "UPDATE setting_values SET contract_name=?,contract_version=?,value_json=?,"
        "revision=revision+1,updated_at_utc=?,command_id=? WHERE setting_key=? AND revision=?",
        (contract, version, raw, now, command, key, rev),
    )
    if changed.rowcount != 1:
        raise ValidationError("Setting revision changed during its command.")


class StateReader:
    """Owner eligibility checks receive bounded read access to the existing UoW."""

    def __init__(self, connection):
        self.__connection = connection

    def execute(self, sql, parameters=()):
        if type(sql) is not str or not sql.lstrip().upper().startswith("SELECT "):
            raise ValidationError("Setting owner checks may only read state.")
        return StateResult(self.__connection.execute(sql, parameters))


class StateResult:
    def __init__(self, cursor):
        self.__cursor = cursor

    def fetchone(self):
        return self.__cursor.fetchone()
