from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import LobbyRoom, SwapRecord, YieldRecord
from .services import estimate_aave_yield


class LobbyMatchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.wallet_1 = "0x1111111111111111111111111111111111111111"
        self.wallet_2 = "0x2222222222222222222222222222222222222222"

    def test_within_tolerance_matches_existing_room(self):
        first = self.client.post(
            "/api/lobby/match/",
            {"wallet_address": self.wallet_1, "wager_amount": "10.000000"},
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertFalse(first.data["matched"])
        room_id = first.data["room"]["id"]

        second = self.client.post(
            "/api/lobby/match/",
            {"wallet_address": self.wallet_2, "wager_amount": "10.900000"},
            format="json",
        )
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.data["matched"])
        self.assertEqual(second.data["room"]["id"], room_id)

        room = LobbyRoom.objects.get(id=room_id)
        self.assertEqual(room.status, LobbyRoom.STATUS_MATCHED)
        self.assertEqual(room.opponent_wallet, self.wallet_2.lower())

    def test_outside_tolerance_creates_new_room(self):
        self.client.post(
            "/api/lobby/match/",
            {"wallet_address": self.wallet_1, "wager_amount": "10.000000"},
            format="json",
        )
        second = self.client.post(
            "/api/lobby/match/",
            {"wallet_address": self.wallet_2, "wager_amount": "12.000000"},
            format="json",
        )
        self.assertEqual(second.status_code, 201)
        self.assertFalse(second.data["matched"])
        self.assertEqual(LobbyRoom.objects.count(), 2)


class MonetizationEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.wallet = "0x9999999999999999999999999999999999999999"

    @patch("game.services.requests.get")
    def test_swap_quote_persists_record(self, mock_get):
        fake_response = Mock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = {
            "dstAmount": "123456",
            "srcToken": {"symbol": "USDC"},
            "dstToken": {"symbol": "WMATIC"},
        }
        mock_get.return_value = fake_response

        response = self.client.post(
            "/api/swap/quote/",
            {
                "wallet_address": self.wallet,
                "from_token": "0x0000000000000000000000000000000000001010",
                "to_token": "0x0000000000000000000000000000000000001011",
                "amount": "1000000",
                "chain_id": 137,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("swap_uid", response.data)
        self.assertEqual(SwapRecord.objects.count(), 1)
        record = SwapRecord.objects.first()
        self.assertEqual(record.to_amount_estimate, "123456")

    def test_yield_estimate_creates_record(self):
        principal = 10**18
        apr_bps = 700
        days = 30
        expected = estimate_aave_yield(principal_wei=principal, apr_bps=apr_bps, days=days)

        response = self.client.post(
            "/api/yield/estimate/",
            {
                "wallet_address": self.wallet,
                "principal_wei": str(principal),
                "apr_bps": apr_bps,
                "days": days,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data["estimated_yield_wei"]), expected)
        self.assertEqual(YieldRecord.objects.count(), 1)
