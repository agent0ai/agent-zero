from decimal import Decimal

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LobbyRoom, SwapRecord, YieldRecord
from .serializers import (
    LobbyMatchRequestSerializer,
    LobbyRoomSerializer,
    OneInchQuoteRequestSerializer,
    YieldEstimateRequestSerializer,
)
from .services import DEFAULT_CHAIN_ID, estimate_aave_yield, fetch_oneinch_quote


def normalize_wallet(wallet_address: str) -> str:
    if not isinstance(wallet_address, str) or len(wallet_address) != 42 or not wallet_address.startswith("0x"):
        raise ValueError("wallet_address must be a 42-char 0x address")
    return wallet_address.lower()


def broadcast_lobby_event(event_name: str, room: LobbyRoom):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    payload = LobbyRoomSerializer(room).data
    async_to_sync(channel_layer.group_send)(
        "lobby",
        {
            "type": "lobby.message",
            "event": event_name,
            "payload": payload,
        },
    )


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class LobbyMatchView(APIView):
    def post(self, request):
        serializer = LobbyMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            wallet_address = normalize_wallet(serializer.validated_data["wallet_address"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        wager_amount = serializer.validated_data["wager_amount"]
        tolerance = wager_amount * Decimal("0.10")
        lower = wager_amount - tolerance
        upper = wager_amount + tolerance

        with transaction.atomic():
            candidate = (
                LobbyRoom.objects.select_for_update()
                .filter(
                    status=LobbyRoom.STATUS_OPEN,
                    opponent_wallet__isnull=True,
                    wager_amount__gte=lower,
                    wager_amount__lte=upper,
                )
                .exclude(creator_wallet=wallet_address)
                .order_by("created_at")
                .first()
            )

            if candidate:
                candidate.opponent_wallet = wallet_address
                candidate.status = LobbyRoom.STATUS_MATCHED
                candidate.matched_at = timezone.now()
                candidate.save(update_fields=["opponent_wallet", "status", "matched_at"])
                room_data = LobbyRoomSerializer(candidate).data
                matched = True
                room = candidate
            else:
                room = LobbyRoom.objects.create(
                    creator_wallet=wallet_address,
                    wager_amount=wager_amount,
                    status=LobbyRoom.STATUS_OPEN,
                )
                room_data = LobbyRoomSerializer(room).data
                matched = False

        broadcast_lobby_event("room.matched" if matched else "room.opened", room)
        return Response(
            {"matched": matched, "room": room_data},
            status=status.HTTP_200_OK if matched else status.HTTP_201_CREATED,
        )


class LobbyRoomListView(APIView):
    def get(self, request):
        rooms = LobbyRoom.objects.all()
        status_filter = request.query_params.get("status")
        wallet = request.query_params.get("wallet")

        if status_filter:
            rooms = rooms.filter(status=status_filter)
        if wallet:
            wallet = wallet.lower()
            rooms = rooms.filter(Q(creator_wallet=wallet) | Q(opponent_wallet=wallet))

        return Response(LobbyRoomSerializer(rooms, many=True).data)


class OneInchQuoteView(APIView):
    def post(self, request):
        serializer = OneInchQuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            wallet_address = normalize_wallet(data["wallet_address"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        chain_id = data.get("chain_id") or DEFAULT_CHAIN_ID

        try:
            quote = fetch_oneinch_quote(
                chain_id=chain_id,
                from_token=data["from_token"],
                to_token=data["to_token"],
                amount=data["amount"],
            )
        except requests.RequestException as exc:
            return Response(
                {"detail": "Failed to fetch 1inch quote", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        record = SwapRecord.objects.create(
            wallet_address=wallet_address,
            from_token=data["from_token"],
            to_token=data["to_token"],
            from_amount=data["amount"],
            to_amount_estimate=str(quote.get("dstAmount", "0")),
            oneinch_response=quote,
        )

        return Response(
            {
                "swap_uid": str(record.uid),
                "quote": quote,
            }
        )


class YieldEstimateView(APIView):
    def post(self, request):
        serializer = YieldEstimateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            wallet_address = normalize_wallet(data["wallet_address"])
            principal_wei = int(data["principal_wei"])
        except (TypeError, ValueError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        apr_bps = data["apr_bps"]
        days = data["days"]
        estimated_yield_wei = estimate_aave_yield(
            principal_wei=principal_wei,
            apr_bps=apr_bps,
            days=days,
        )

        record = YieldRecord.objects.create(
            wallet_address=wallet_address,
            principal_wei=str(principal_wei),
            apr_bps=apr_bps,
            days=days,
            estimated_yield_wei=str(estimated_yield_wei),
        )

        return Response(
            {
                "yield_uid": str(record.uid),
                "principal_wei": str(principal_wei),
                "estimated_yield_wei": str(estimated_yield_wei),
                "apr_bps": apr_bps,
                "days": days,
            }
        )
