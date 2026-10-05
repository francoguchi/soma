"""Closed Scope-01 route policy; owner operations remain in application services."""

import re
from dataclasses import asdict, is_dataclass

from starlette.responses import JSONResponse
from soma.foundation.contracts import validate_contract
from soma.foundation.errors import SomaError, ValidationError
from soma.foundation.identity import require_uuid4
from soma.foundation.persistence.read_snapshot import ReadSnapshot
from soma.foundation.strict_json import loads_strict_bytes, loads_strict, canonical_json_bytes
from soma.modules.reference.transport.errors import reference_error_envelope


def main_route(path):
    """Closed Reference/Settings Main routes supplied to Foundation static serving."""
    return (
        re.fullmatch(
            r"/settings/(?:profile|preferences|reference-data(?:/(?:customer_organization|contact|dispatch_location)(?:/(?:new|[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}))?)?)",
            path,
        )
        is not None
    )


SPECS = (
    dict(
        name="identities",
        method="POST",
        path="/api/v1/reference/identities",
        handler="identities",
        request="identities-request",
        response="identities-result",
        mutation=False,
        target="contact",
    ),
    dict(
        name="settings-definitions",
        method="GET",
        path="/api/v1/settings/registry/definitions",
        handler="settings_definitions",
        request="empty-request",
        response="settings-definitions",
        mutation=False,
        target="setting",
    ),
    dict(
        name="profile-detail",
        method="GET",
        path="/api/v1/local-user-profile",
        handler="profile_detail",
        request="empty-request",
        response="profile-detail",
        mutation=False,
        target="local_user_profile",
    ),
    {
        "name": "list-customer",
        "method": "GET",
        "path": "/api/v1/reference/customer-organizations",
        "handler": "active:customer_organization",
        "request": "list-customer-request",
        "response": "reference-page",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "create-customer",
        "method": "POST",
        "path": "/api/v1/reference/customer-organizations",
        "handler": "create:customer_organization",
        "request": "create-customer-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "customer_organization",
    },
    {
        "name": "detail-customer",
        "method": "GET",
        "path": "/api/v1/reference/customer-organizations/{id}",
        "handler": "detail:customer_organization",
        "request": "detail-customer-request",
        "response": "customer-detail",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "update-customer",
        "method": "PATCH",
        "path": "/api/v1/reference/customer-organizations/{id}",
        "handler": "update:customer_organization",
        "request": "update-customer-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "customer_organization",
    },
    {
        "name": "list-contact",
        "method": "GET",
        "path": "/api/v1/reference/contacts",
        "handler": "active:contact",
        "request": "list-contact-request",
        "response": "reference-page",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "create-contact",
        "method": "POST",
        "path": "/api/v1/reference/contacts",
        "handler": "create:contact",
        "request": "create-contact-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "contact",
    },
    {
        "name": "detail-contact",
        "method": "GET",
        "path": "/api/v1/reference/contacts/{id}",
        "handler": "detail:contact",
        "request": "detail-contact-request",
        "response": "contact-detail",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "update-contact",
        "method": "PATCH",
        "path": "/api/v1/reference/contacts/{id}",
        "handler": "update:contact",
        "request": "update-contact-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "contact",
    },
    {
        "name": "list-dispatch",
        "method": "GET",
        "path": "/api/v1/reference/dispatch-locations",
        "handler": "active:dispatch_location",
        "request": "list-dispatch-request",
        "response": "reference-page",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "create-dispatch",
        "method": "POST",
        "path": "/api/v1/reference/dispatch-locations",
        "handler": "create:dispatch_location",
        "request": "create-dispatch-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "dispatch_location",
    },
    {
        "name": "detail-dispatch",
        "method": "GET",
        "path": "/api/v1/reference/dispatch-locations/{id}",
        "handler": "detail:dispatch_location",
        "request": "detail-dispatch-request",
        "response": "dispatch-detail",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "update-dispatch",
        "method": "PATCH",
        "path": "/api/v1/reference/dispatch-locations/{id}",
        "handler": "update:dispatch_location",
        "request": "update-dispatch-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "dispatch_location",
    },
    {
        "name": "set-account-code",
        "method": "PUT",
        "path": "/api/v1/reference/customer-organizations/{id}/customer-account-code",
        "handler": "set_code",
        "request": "set-account-code-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "customer_organization",
    },
    {
        "name": "review-account-code",
        "method": "POST",
        "path": "/api/v1/reference/customer-account-code/review-preview",
        "handler": "review",
        "request": "review-account-code-request",
        "response": "review-result",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "share-account-code",
        "method": "POST",
        "path": "/api/v1/reference/customer-organizations/{id}/customer-account-code/confirm-shared-claim",
        "handler": "share_code",
        "request": "share-account-code-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "customer_organization",
    },
    {
        "name": "reassign-account-code",
        "method": "POST",
        "path": "/api/v1/reference/customer-account-code/reassign",
        "handler": "reassign_code",
        "request": "reassign-account-code-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "customer_organization",
    },
    {
        "name": "account-code-history",
        "method": "GET",
        "path": "/api/v1/reference/customer-organizations/{id}/customer-account-code/history",
        "handler": "history:account_code",
        "request": "account-code-history-request",
        "response": "account-code-page",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "match-customer",
        "method": "POST",
        "path": "/api/v1/reference/match/customer-organization",
        "handler": "match:customer",
        "request": "match-customer-request",
        "response": "candidate-result",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "match-contact",
        "method": "POST",
        "path": "/api/v1/reference/match/contact",
        "handler": "match:contact",
        "request": "match-contact-request",
        "response": "candidate-result",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "list-channels",
        "method": "GET",
        "path": "/api/v1/reference/contacts/{id}/channels",
        "handler": "history:channels",
        "request": "list-channels-request",
        "response": "channels-page",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "add-channel",
        "method": "POST",
        "path": "/api/v1/reference/contacts/{id}/channels",
        "handler": "add_channel",
        "request": "add-channel-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "contact_channel",
    },
    {
        "name": "update-channel",
        "method": "PATCH",
        "path": "/api/v1/reference/contacts/{id}/channels/{channel_id}",
        "handler": "update_channel",
        "request": "update-channel-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "contact_channel",
    },
    {
        "name": "archive-channel",
        "method": "POST",
        "path": "/api/v1/reference/contacts/{id}/channels/{channel_id}/archive",
        "handler": "archive_channel",
        "request": "archive-channel-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "contact_channel",
    },
    {
        "name": "validate-channel",
        "method": "POST",
        "path": "/api/v1/reference/contacts/{id}/channels/validate-for-use",
        "handler": "channel_use",
        "request": "validate-channel-request",
        "response": "channel-use-result",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "change-affiliation",
        "method": "POST",
        "path": "/api/v1/reference/contacts/{id}/affiliation",
        "handler": "affiliation",
        "request": "change-affiliation-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "contact",
    },
    {
        "name": "affiliation-history",
        "method": "GET",
        "path": "/api/v1/reference/contacts/{id}/affiliation-history",
        "handler": "history:affiliation",
        "request": "affiliation-history-request",
        "response": "affiliation-page",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "archive-preview",
        "method": "POST",
        "path": "/api/v1/reference/{reference_type}/{id}/archive-preview",
        "handler": "archive-preview",
        "request": "archive-preview-request",
        "response": "blocker-preview",
        "mutation": False,
        "target": "dynamic",
    },
    {
        "name": "archive",
        "method": "POST",
        "path": "/api/v1/reference/{reference_type}/{id}/archive",
        "handler": "archive",
        "request": "archive-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "dynamic",
    },
    {
        "name": "reactivate",
        "method": "POST",
        "path": "/api/v1/reference/{reference_type}/{id}/reactivate",
        "handler": "reactivate",
        "request": "reactivate-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "dynamic",
    },
    {
        "name": "get-setting",
        "method": "GET",
        "path": "/api/v1/settings/{setting_key}",
        "handler": "get_setting",
        "request": "get-setting-request",
        "response": "setting-value",
        "mutation": False,
        "target": "contact",
    },
    {
        "name": "write-setting",
        "method": "PUT",
        "path": "/api/v1/settings/{setting_key}",
        "handler": "write_setting",
        "request": "write-setting-request",
        "response": "setting-value",
        "mutation": True,
        "target": "setting",
    },
    {
        "name": "update-profile",
        "method": "PATCH",
        "path": "/api/v1/local-user-profile/display-name",
        "handler": "profile",
        "request": "update-profile-request",
        "response": "mutation-result",
        "mutation": True,
        "target": "local_user_profile",
    },
)


def resolve(method, path):
    for spec in SPECS:
        if method != spec["method"]:
            continue
        pattern = re.sub(r"\{([a-z_]+)\}", r"(?P<\1>[^/]+)", spec["path"])
        match = re.fullmatch(pattern, path)
        if match is None:
            continue
        params = match.groupdict()
        if "reference_type" in params and params["reference_type"] not in (
            "customer_organization",
            "contact",
            "dispatch_location",
        ):
            continue
        for key in ("id", "channel_id"):
            if key in params:
                require_uuid4(params[key])
        return spec, params
    return None


def json_value(value):
    if is_dataclass(value):
        value = asdict(value)
    if type(value) is dict:
        return {key: json_value(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [json_value(item) for item in value]
    return value


class ReferenceTransport:
    def __init__(self, reference, factory, sessions):
        self.reference, self.factory, self.sessions = reference, factory, sessions

    def handle(self, request, raw):
        try:
            resolved = resolve(request.method, request.url.path)
            if resolved is None:
                raise SomaError("NOT_FOUND", "This Reference operation is not available.")
            spec, params = resolved
            context = self.sessions.validate(request, mutation=spec["mutation"])
            if (
                len(str(request.url.path).encode("utf-8")) + len(request.url.query.encode("utf-8"))
                > 4096
            ):
                raise ValidationError("Reference URL exceeds its bound.")
            if request.method == "GET":
                body = {}
                for key, value in request.query_params.multi_items():
                    if key in body:
                        raise ValidationError("Duplicate query field.")
                    if key in ("count_exact", "include_archived"):
                        if value not in ("true", "false"):
                            raise ValidationError("Invalid query boolean.")
                        body[key] = value == "true"
                    elif key == "limit":
                        if not re.fullmatch(r"[0-9]{1,3}", value):
                            raise ValidationError("Invalid page limit.")
                        body[key] = int(value)
                    else:
                        body[key] = value
            else:
                if request.headers.getlist("content-type") != ["application/json"]:
                    raise ValidationError("Reference bodies require application/json.")
                if request.query_params:
                    raise ValidationError("Body operations reject query fields.")
                body = loads_strict_bytes(
                    raw, max_bytes=16384 if spec["handler"] == "write_setting" else 8192
                )
            validate_contract("urn:soma:01:" + spec["request"] + ":v1", body)
            result = self._invoke(spec, params, body, context["actor_id"])
            result = json_value(result)
            if spec["mutation"] and spec["response"] == "mutation-result":
                result["result_refs"] = [
                    dict(type=params.get("reference_type", spec["target"]), id=result["target_id"])
                ]
            if spec["response"] == "setting-value":
                result["value_json"] = canonical_json_bytes(result.pop("value")).decode()
            validate_contract("urn:soma:01:" + spec["response"] + ":v1", result)
            return JSONResponse(
                result, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
            )
        except SomaError as error:
            status = {"NOT_FOUND": 404, "UNAUTHENTICATED": 401, "FORBIDDEN": 403}.get(
                error.code, 400
            )
            return JSONResponse(
                reference_error_envelope(error),
                status_code=status,
                headers={"Cache-Control": "no-store"},
            )

    def _invoke(self, spec, params, body, actor):
        ref, handler = self.reference, spec["handler"]
        if not spec["mutation"]:
            if handler == "archive-preview":
                return ref.lifecycle.preview(
                    operation="archive",
                    target_type=params["reference_type"],
                    target_id=params["id"],
                    **body,
                )
            with ReadSnapshot(self.factory) as snapshot:
                if handler == "identities":
                    return ref.queries.identities(snapshot, **body)
                if handler == "settings_definitions":
                    return ref.settings.presentation_definitions()
                if handler == "profile_detail":
                    value = ref.profile.get(snapshot)
                    if value is None:
                        raise SomaError("NOT_FOUND", "Local User Profile does not exist.")
                    return value
                if handler.startswith("active:"):
                    return ref.queries.active(snapshot, handler.split(":")[1], **body)
                if handler.startswith("detail:"):
                    return ref.queries.detail(snapshot, handler.split(":")[1], params["id"])
                if handler.startswith("history:"):
                    return ref.queries.history(
                        snapshot, handler.split(":")[1], params["id"], **body
                    )
                if handler.startswith("match:"):
                    method = (
                        ref.queries.match_customer_organization
                        if handler.endswith("customer")
                        else ref.queries.match_contact
                    )
                    return method(snapshot, body)
                if handler == "review":
                    return ref.queries.preview_customer_account_code_conflict(snapshot, body)
                if handler == "channel_use":
                    return ref.queries.channel_use(snapshot, params["id"], **body)
                if handler == "get_setting":
                    return ref.settings.get(snapshot, params["setting_key"])
        request = body | dict(actor_id=actor)
        if handler.startswith("create:"):
            kind = handler.split(":")[1]
            method = {
                "customer_organization": ref.customers.create_customer_organization,
                "contact": ref.contacts.create_contact,
                "dispatch_location": ref.dispatch.create_standalone,
            }[kind]
            return method(**request)
        if handler.startswith("update:"):
            kind = handler.split(":")[1]
            method, identity_key = {
                "customer_organization": (ref.customers.update_descriptive_data, "customer_org_id"),
                "contact": (ref.contacts.update_descriptive_data, "contact_id"),
                "dispatch_location": (ref.dispatch.update_descriptive_data, "dispatch_location_id"),
            }[kind]
            return method(**(request | {identity_key: params["id"]}))
        if handler == "set_code":
            return ref.customers.set_customer_account_code(customer_org_id=params["id"], **request)
        if handler == "share_code":
            return ref.customers.confirm_customer_account_code_shared_claim(
                customer_org_id=params["id"], **request
            )
        if handler == "reassign_code":
            return ref.customers.reassign_customer_account_code(**request)
        if handler in ("add_channel", "update_channel", "archive_channel"):
            request["contact_id"] = params["id"]
            if "channel_id" in params:
                request["contact_channel_id"] = params["channel_id"]
            return getattr(
                ref.contacts,
                {
                    "add_channel": "add_contact_channel",
                    "update_channel": "update_contact_channel",
                    "archive_channel": "archive_contact_channel",
                }[handler],
            )(**request)
        if handler == "affiliation":
            return ref.contacts.change_contact_affiliation(contact_id=params["id"], **request)
        if handler in ("archive", "reactivate"):
            return getattr(ref.lifecycle, handler + "_reference")(
                target_type=params["reference_type"], target_id=params["id"], **request
            )
        if handler == "write_setting":
            request["value"] = loads_strict(request.pop("value_json"), max_bytes=16384)
            return ref.settings.write(setting_key=params["setting_key"], **request)
        if handler == "profile":
            return ref.profile.update_display_name(**request)
        raise SomaError("NOT_FOUND", "Reference owner operation is unavailable.")
