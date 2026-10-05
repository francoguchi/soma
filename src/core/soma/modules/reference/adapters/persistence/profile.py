from soma.foundation.errors import SomaError


def singleton(connection):
    return connection.execute(
        "SELECT local_user_profile_id,display_name,revision FROM local_user_profiles WHERE singleton_guard=1"
    ).fetchone()


def create(connection, actor_id, name, now, parent_command_id):
    if not connection.execute(
        "SELECT 1 FROM command_receipts WHERE command_id=?",
        (parent_command_id,),
    ).fetchone():
        raise SomaError("VALIDATION_FAILED", "Parent setup receipt is required.", "correct_input")
    if singleton(connection) is not None:
        raise SomaError("SINGLETON_PROFILE_EXISTS", "Local User Profile already exists.", "refresh")
    connection.execute(
        "INSERT INTO local_user_profiles VALUES (?,1,?,1,?,?)", (actor_id, name, now, now)
    )


def update(connection, actor_id, name, now):
    connection.execute(
        "UPDATE local_user_profiles SET display_name=?,revision=revision+1,updated_at_utc=? WHERE local_user_profile_id=?",
        (name, now, actor_id),
    )
