import uuid

from django.db import models


class LobbyRoom(models.Model):
    STATUS_OPEN = "open"
    STATUS_MATCHED = "matched"
    STATUS_STARTED = "started"
    STATUS_SETTLED = "settled"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_MATCHED, "Matched"),
        (STATUS_STARTED, "Started"),
        (STATUS_SETTLED, "Settled"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator_wallet = models.CharField(max_length=42, db_index=True)
    opponent_wallet = models.CharField(max_length=42, null=True, blank=True, db_index=True)
    wager_amount = models.DecimalField(max_digits=20, decimal_places=6)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    contract_game_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    matched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class SwapRecord(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet_address = models.CharField(max_length=42, db_index=True)
    from_token = models.CharField(max_length=42)
    to_token = models.CharField(max_length=42)
    from_amount = models.CharField(max_length=100)
    to_amount_estimate = models.CharField(max_length=100)
    volume_usd = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    tx_hash = models.CharField(max_length=80, null=True, blank=True)
    oneinch_response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class YieldRecord(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet_address = models.CharField(max_length=42, db_index=True)
    principal_wei = models.CharField(max_length=100)
    apr_bps = models.PositiveIntegerField()
    days = models.PositiveIntegerField(default=30)
    estimated_yield_wei = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
