"""Email-only communication queries, using the caller's coherent read snapshot."""

from soma.foundation.errors import SomaError
from soma.foundation.identity import require_uuid4
from soma.modules.reference.application.commands import revision as require_revision
from soma.modules.reference.domain.channels import ChannelUseValidation, validate_email
from soma.modules.reference.ports.contact import ContactCandidatePage, ContactIdentity
from .persistence import contact as store
from .persistence.matching_profile import require_persisted_matching_profile


def _page(limit, cursor):
    if type(limit) is not int or not 1 <= limit <= 200:
        raise SomaError(
            "MATCH_INPUT_INVALID", "Page size must be between 1 and 200.", "correct_input"
        )
    if cursor is not None:
        require_uuid4(cursor)


class Communication:
    def match_email_candidates(self, snapshot, raw_address, *, limit=50, after_contact_id=None):
        _page(limit, after_contact_id)
        _, key = validate_email(raw_address)
        connection = snapshot.connection
        require_persisted_matching_profile(connection)
        rows = connection.execute(
            "SELECT DISTINCT c.contact_id,c.revision FROM contact_channels ch JOIN contacts c ON c.contact_id=ch.contact_id "
            "WHERE ch.channel_kind='email' AND ch.lifecycle_state='active' AND ch.match_key=? "
            "AND c.lifecycle_state='active' AND c.contact_id>? ORDER BY c.contact_id LIMIT ?",
            (key, after_contact_id or "", limit + 1),
        ).fetchall()
        return ContactCandidatePage(
            tuple(ContactIdentity(*row) for row in rows[:limit]),
            rows[limit - 1][0] if len(rows) > limit else None,
        )

    def validate_contact(self, snapshot, contact_id, revision):
        require_uuid4(contact_id)
        require_revision(revision)
        require_persisted_matching_profile(snapshot.connection)
        row = store.contact(snapshot.connection, contact_id)
        if row is None:
            return "MISSING"
        if row[4] != revision:
            raise SomaError("STALE_REVISION", "Contact revision changed.", "refresh")
        return "ACTIVE" if row[3] == "active" else "ARCHIVED"

    def validate_channel_for_use(
        self, snapshot, contact_id, channel_or_auto, purpose, *, limit=50, after_channel_id=None
    ):
        require_uuid4(contact_id)
        _page(limit, after_channel_id)
        if purpose != "msg_recipient":
            raise SomaError(
                "MATCH_INPUT_INVALID", "Channel purpose is unsupported.", "correct_input"
            )
        if channel_or_auto != "AUTO":
            require_uuid4(channel_or_auto)
        connection = snapshot.connection
        require_persisted_matching_profile(connection)
        row = store.contact(connection, contact_id)
        if row is None:
            return ChannelUseValidation("MISSING", contact_id)
        if row[3] != "active":
            return ChannelUseValidation("ARCHIVED", contact_id)
        if channel_or_auto != "AUTO":
            try:
                channel = store.channel(connection, contact_id, channel_or_auto)
            except SomaError as exc:
                if exc.code == "NOT_FOUND":
                    return ChannelUseValidation("MISSING", contact_id, channel_or_auto)
                raise
            if channel[5] != "active":
                return ChannelUseValidation("ARCHIVED", contact_id, channel_or_auto)
            try:
                value, _ = validate_email(channel[3])
            except SomaError:
                return ChannelUseValidation("INVALID", contact_id, channel_or_auto)
            return ChannelUseValidation(
                "USABLE", contact_id, channel_or_auto, value_text=value, usable_count=1
            )

        # Stream fixed-size reads: accurate uniqueness proof without unbounded materialization.
        count, first, ids, cursor = 0, None, [], ""
        while True:
            rows = connection.execute(
                "SELECT contact_channel_id,value_text FROM contact_channels WHERE contact_id=? "
                "AND lifecycle_state='active' AND channel_kind='email' AND contact_channel_id>? "
                "ORDER BY contact_channel_id LIMIT 200",
                (contact_id, cursor),
            ).fetchall()
            if not rows:
                break
            for identity, value in rows:
                try:
                    stored, _ = validate_email(value)
                except SomaError:
                    continue
                count += 1
                if first is None:
                    first = (identity, stored)
                if identity > (after_channel_id or "") and len(ids) <= limit:
                    ids.append(identity)
            cursor = rows[-1][0]
            if len(rows) < 200:
                break
        if count == 0:
            return ChannelUseValidation("MISSING", contact_id)
        if count == 1:
            return ChannelUseValidation(
                "USABLE", contact_id, first[0], value_text=first[1], usable_count=1
            )
        return ChannelUseValidation(
            "MULTIPLE_USABLE",
            contact_id,
            usable_count=count,
            candidate_channel_ids=tuple(ids[:limit]),
            continuation_after_id=ids[limit - 1] if len(ids) > limit else None,
        )
