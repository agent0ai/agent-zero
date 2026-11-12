"""Production public-key rotation; the pairing store owns the atomic lock/write."""
from __future__ import annotations

from typing import Any

from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BROWSER_BRIDGE_RECORD_SCHEMA_VERSION, BrowserBridgePairingUnavailable,
    BrowserBridgePairingStore, _public_key, validate_identifier,
    get_browser_bridge_pairing_store,
)

ROTATION_TTL_MS = 600_000


def validate_rotation(value: Any, record: dict) -> dict:
    keys = {"rotation_id", "from_generation", "public_key", "created_at_ms", "expires_at_ms", "status"}
    if not isinstance(value, dict) or set(value) != keys or record["state"] != "active":
        raise BrowserBridgePairingUnavailable("invalid credential rotation")
    if (type(value["from_generation"]) is not int or not 1 <= value["from_generation"] < 2_147_483_647
        or type(value["created_at_ms"]) is not int or value["created_at_ms"] < 0
        or type(value["expires_at_ms"]) is not int
        or value["expires_at_ms"] != value["created_at_ms"] + ROTATION_TTL_MS
        or value["status"] not in {"pending", "active"}):
        raise BrowserBridgePairingUnavailable("invalid credential rotation")
    result = dict(value)
    result["rotation_id"] = validate_identifier(value["rotation_id"], field_name="rotation_id")
    result["public_key"] = _public_key(value["public_key"])
    offset = 1 if value["status"] == "active" else 0
    if (record["key_generation"] != value["from_generation"] + offset
        or (result["public_key"] == record["public_key"]) != (offset == 1)):
        raise BrowserBridgePairingUnavailable("invalid credential rotation")
    return result


class BrowserBridgeCredentialStore:
    def __init__(self, pairing: BrowserBridgePairingStore):
        if not isinstance(pairing, BrowserBridgePairingStore):
            raise TypeError("pairing owner required")
        self.pairing = pairing

    def _write(self, records: list[dict]) -> None:
        self.pairing._repository._save({"schema_version": BROWSER_BRIDGE_RECORD_SCHEMA_VERSION, "bridges": records})

    @staticmethod
    def _match(record, bridge_id, server_id, subject_id=None):
        return (record["bridge_id"] == bridge_id and record["server_instance_id"] == server_id
                and record["state"] == "active" and (subject_id is None or record["subject_id"] == subject_id))

    def begin(self, *, bridge_id: str, server_id: str, subject_id: str,
              key_generation: int, rotation_id: str, public_key: Any) -> dict:
        rotation_id = validate_identifier(rotation_id, field_name="rotation_id")
        public_key = _public_key(public_key)
        with self.pairing._lock:
            now = self.pairing._clock_ms()
            records = self.pairing._repository._validated_records()
            record = next((r for r in records if self._match(r, bridge_id, server_id, subject_id)), None)
            if record is None or record["key_generation"] != key_generation:
                raise BrowserBridgePairingUnavailable("credential authority changed")
            previous = record.get("rotation")
            if previous and previous["rotation_id"] == rotation_id:
                if previous["public_key"] != public_key:
                    raise BrowserBridgePairingUnavailable("rotation conflict")
                return self._status(record, previous, now)
            if (record["public_key"] == public_key or key_generation >= 2_147_483_647
                or (previous and previous["status"] == "pending" and now < previous["expires_at_ms"])):
                raise BrowserBridgePairingUnavailable("rotation conflict")
            record["rotation"] = {"rotation_id": rotation_id, "from_generation": key_generation,
                "public_key": public_key, "created_at_ms": now,
                "expires_at_ms": now + ROTATION_TTL_MS, "status": "pending"}
            validate_rotation(record["rotation"], record)
            self._write(records)
            return self._status(record, record["rotation"], now)

    def status(self, *, bridge_id, server_id, subject_id, key_generation, rotation_id):
        with self.pairing._lock:
            record = self.pairing._repository.active_record(bridge_id=bridge_id, server_instance_id=server_id)
            if not record or record["subject_id"] != subject_id or record["key_generation"] != key_generation:
                raise BrowserBridgePairingUnavailable("credential authority changed")
            rotation = record.get("rotation")
            if rotation is None or rotation["rotation_id"] != rotation_id:
                raise BrowserBridgePairingUnavailable("unknown rotation")
            return self._status(record, rotation, self.pairing._clock_ms())

    @staticmethod
    def _status(record, rotation, now):
        status = rotation["status"]
        if status == "pending" and now >= rotation["expires_at_ms"]:
            status = "expired"
        return {"contract_version": 1, "rotation_id": rotation["rotation_id"],
                "key_generation": record["key_generation"], "status": status,
                "expires_at_ms": rotation["expires_at_ms"] if status == "pending" else None}

    def self_revoke(self, *, bridge_id, server_id, subject_id, key_generation):
        with self.pairing._lock:
            record = self.pairing._repository.active_record(bridge_id=bridge_id, server_instance_id=server_id)
            if not record or record["subject_id"] != subject_id or record["key_generation"] != key_generation:
                raise BrowserBridgePairingUnavailable("credential authority changed")
            return self.pairing._repository.revoke(bridge_id=bridge_id, server_instance_id=server_id,
                subject_id=subject_id, revoked_at_ms=self.pairing._clock_ms())

    def authentication_records(self, bridge_id: str, server_id: str) -> tuple[dict, ...]:
        with self.pairing._lock:
            record = self.pairing._repository.active_record(bridge_id=bridge_id, server_instance_id=server_id)
            if not record:
                return ()
            rotation = record.get("rotation")
            if rotation and rotation["status"] == "pending" and self.pairing._clock_ms() < rotation["expires_at_ms"]:
                candidate = dict(record)
                candidate["key_generation"] += 1
                candidate["public_key"] = dict(rotation["public_key"])
                return (record, candidate)
            return (record,)

    def accept_verified_key(self, verified: dict, authenticated_at_ms: int) -> None:
        """CAS exact verified public key, not merely generation (pending-key ABA)."""
        with self.pairing._lock:
            now = self.pairing._clock_ms()
            records = self.pairing._repository._validated_records()
            record = next((r for r in records if self._match(r, verified["bridge_id"],
                           verified["server_instance_id"], verified["subject_id"])), None)
            if (record is None or type(authenticated_at_ms) is not int or authenticated_at_ms < 0
                or any(record[k] != verified[k] for k in ("extension_id", "companion_instance_id", "scopes"))):
                raise BrowserBridgePairingUnavailable("credential authority changed")
            if record["key_generation"] == verified["key_generation"] and record["public_key"] == verified["public_key"]:
                record["last_authenticated_at_ms"] = authenticated_at_ms
            else:
                rotation = record.get("rotation")
                if (not rotation or rotation["status"] != "pending" or now >= rotation["expires_at_ms"]
                    or verified["key_generation"] != record["key_generation"] + 1
                    or verified["public_key"] != rotation["public_key"]
                    or verified.get("rotation", {}).get("rotation_id") != rotation["rotation_id"]):
                    raise BrowserBridgePairingUnavailable("credential authority changed")
                record["key_generation"] = verified["key_generation"]
                record["public_key"] = dict(verified["public_key"])
                record["last_authenticated_at_ms"] = authenticated_at_ms
                record["rotation"] = {**rotation, "status": "active"}
            self._write(records)


def get_browser_bridge_credential_store() -> BrowserBridgeCredentialStore:
    return BrowserBridgeCredentialStore(get_browser_bridge_pairing_store())
