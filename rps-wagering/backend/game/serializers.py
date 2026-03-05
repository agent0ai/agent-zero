from rest_framework import serializers

from .models import LobbyRoom, SwapRecord, YieldRecord


class LobbyRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LobbyRoom
        fields = [
            "id",
            "creator_wallet",
            "opponent_wallet",
            "wager_amount",
            "status",
            "contract_game_id",
            "created_at",
            "matched_at",
        ]


class LobbyMatchRequestSerializer(serializers.Serializer):
    wallet_address = serializers.CharField(max_length=42)
    wager_amount = serializers.DecimalField(max_digits=20, decimal_places=6)


class OneInchQuoteRequestSerializer(serializers.Serializer):
    wallet_address = serializers.CharField(max_length=42)
    from_token = serializers.CharField(max_length=42)
    to_token = serializers.CharField(max_length=42)
    amount = serializers.CharField(max_length=100)
    chain_id = serializers.IntegerField(required=False)


class SwapRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SwapRecord
        fields = [
            "uid",
            "wallet_address",
            "from_token",
            "to_token",
            "from_amount",
            "to_amount_estimate",
            "volume_usd",
            "tx_hash",
            "oneinch_response",
            "created_at",
        ]


class YieldEstimateRequestSerializer(serializers.Serializer):
    wallet_address = serializers.CharField(max_length=42)
    principal_wei = serializers.CharField(max_length=100)
    apr_bps = serializers.IntegerField(min_value=1, max_value=50000)
    days = serializers.IntegerField(min_value=1, max_value=3650, required=False, default=30)


class YieldRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = YieldRecord
        fields = [
            "uid",
            "wallet_address",
            "principal_wei",
            "apr_bps",
            "days",
            "estimated_yield_wei",
            "created_at",
        ]
