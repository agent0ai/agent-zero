"""Hash-only replay receipts using the existing atomic KVP store.

New receipts are indexed individually. Original v1 records stay a read-only
fallback; its version marker fences older writers before the first new write.
Receipts are never evicted or interpreted as permission to retry.
Callers hold their existing lane lock across reservation, effect and settlement.
"""

import re


_HASH = re.compile(r"[a-f0-9]{64}")
_MISSING = object()


class BrowserBridgeJournal:
    def __init__(self, store_key, validate_record, error_factory, *, load=None, save=None):
        from helpers import kvp

        if (load is None) != (save is None):
            raise ValueError("journal load and save must be supplied together")
        self.store_key = store_key
        self.validate_record = validate_record
        self.error_factory = error_factory
        self.load = load or kvp.get_persistent
        self.save = save or kvp.set_persistent

    def get(self, key):
        if not isinstance(key, str) or not _HASH.fullmatch(key):
            return None  # Foreign Core queue IDs are not bridge receipts.
        try:
            value = self.load(self._key(key), _MISSING)
            if value is not _MISSING:
                self._envelope(value, "record")
                self.validate_record(value["record"])
                return dict(value["record"])
            return self._legacy_records().get(key)
        except Exception:
            raise self.error_factory() from None

    def put(self, key, record):
        try:
            if not isinstance(key, str) or not _HASH.fullmatch(key):
                raise ValueError()
            self.validate_record(record)
            self._legacy_records(fence=True)
            self.save(self._key(key), {"schema_version": 1, "record": dict(record)})
        except Exception:
            raise self.error_factory() from None

    def _key(self, key):
        return f"{self.store_key}.records.{key}"

    def _legacy_records(self, *, fence=False):
        value = self.load(self.store_key, None)
        if value is None:
            value = {"schema_version": 1, "records": {}}
        self._envelope(value, "records", versions=(1, 2))
        records = value["records"]
        if not isinstance(records, dict) or len(records) > 2048:
            raise ValueError()
        for key, record in records.items():
            if not isinstance(key, str) or not _HASH.fullmatch(key):
                raise ValueError()
            self.validate_record(record)
        if fence and value["schema_version"] == 1:
            # Older builds must fail closed, not overlook indexed receipts.
            self.save(self.store_key, {"schema_version": 2, "records": records})
        return {key: dict(record) for key, record in records.items()}

    @staticmethod
    def _envelope(value, field, *, versions=(1,)):
        if not isinstance(value, dict) or set(value) != {"schema_version", field} or type(value["schema_version"]) is not int or value["schema_version"] not in versions:
            raise ValueError()
