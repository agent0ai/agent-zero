"""
Integration tests for PMS Sync Service
Tests bi-directional sync between PMS and PropertyManager
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date
from decimal import Decimal

from instruments.custom.pms_hub.sync_service import PMSSyncService
from instruments.custom.pms_hub.canonical_models import (
    Reservation,
    ReservationStatus,
    PaymentStatus,
)


class TestSyncServiceInitialization:
    """Tests for sync service initialization"""

    @pytest.mark.unit
    def test_sync_service_creation(self):
        """Test creating sync service"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            assert sync is not None


class TestReservationSync:
    """Tests for reservation synchronization"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_reservation_to_property_manager(self, sample_reservation, mock_property_manager):
        """Test syncing reservation to property manager"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = mock_property_manager

            # Mock property sync
            with patch.object(sync, "_sync_property", return_value=1):
                with patch.object(sync, "_sync_guest_to_tenant", return_value=1):
                    with patch.object(sync, "_sync_reservation_to_lease", return_value=100):
                        with patch.object(sync, "_record_payment", return_value=True):
                            success, lease_id = await sync.sync_reservation_to_property_manager(sample_reservation)

            assert success is True
            assert lease_id == 100

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_reservation_missing_property(self, sample_reservation, mock_property_manager):
        """Test sync fails when property sync fails"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = mock_property_manager

            with patch.object(sync, "_sync_property", return_value=None):
                success, lease_id = await sync.sync_reservation_to_property_manager(sample_reservation)

            assert success is False
            assert lease_id is None


class TestPropertySync:
    """Tests for property synchronization"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_property_creation(self):
        """Test property sync creates property in manager"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = AsyncMock()
            sync.pm.add_property = AsyncMock(return_value={
                "status": "success",
                "data": {"id": 1}
            })

            # Mock provider
            mock_provider = AsyncMock()
            mock_provider.get_property = AsyncMock(return_value=None)

            with patch.object(
                sync.registry,
                "get_provider_async",
                return_value=mock_provider
            ):
                with patch.object(sync, "registry") as mock_registry:
                    mock_registry.list_providers.return_value = ["test"]
                    mock_registry.get_provider_async = AsyncMock(return_value=mock_provider)

                    # Need valid property for test
                    from instruments.custom.pms_hub.canonical_models import Property
                    prop = Property(
                        provider_id="p1",
                        provider="test",
                        external_id="e1",
                        name="Test",
                        address="123",
                        city="City",
                        state="ST"
                    )
                    mock_provider.get_property = AsyncMock(return_value=prop)

                    result = await sync._sync_property("p1")
                    assert result == 1


class TestGuestSync:
    """Tests for guest to tenant synchronization"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_guest_creates_tenant(self, sample_reservation):
        """Test guest data syncs to tenant"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = AsyncMock()
            sync.pm.add_tenant = AsyncMock(return_value={
                "status": "success",
                "data": {"id": 1}
            })

            tenant_id = await sync._sync_guest_to_tenant(sample_reservation)

            assert tenant_id == 1
            # Verify tenant was called with guest data
            sync.pm.add_tenant.assert_called_once()
            call_args = sync.pm.add_tenant.call_args
            assert call_args[0][0]["email"] == sample_reservation.guest_email
            assert call_args[0][0]["first_name"] == "John"
            assert call_args[0][0]["last_name"] == "Doe"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_guest_name_parsing(self):
        """Test guest name parsing"""
        from instruments.custom.pms_hub.canonical_models import Reservation

        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = AsyncMock()
            sync.pm.add_tenant = AsyncMock(return_value={
                "status": "success",
                "data": {"id": 1}
            })

            res = Reservation(
                provider_id="r1",
                provider="test",
                property_provider_id="p1",
                guest_name="John Michael Doe",
                guest_email="john@example.com",
                check_in_date=date(2025, 2, 1),
                check_out_date=date(2025, 2, 7),
            )

            await sync._sync_guest_to_tenant(res)

            call_args = sync.pm.add_tenant.call_args[0][0]
            assert call_args["first_name"] == "John"
            assert call_args["last_name"] == "Michael Doe"


class TestLeaseSync:
    """Tests for reservation to lease synchronization"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_reservation_creates_lease(self, sample_reservation):
        """Test reservation syncs to lease"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = AsyncMock()
            sync.pm.create_lease = AsyncMock(return_value={
                "status": "success",
                "data": {"id": 100}
            })

            lease_id = await sync._sync_reservation_to_lease(
                property_id=1,
                unit_id=None,
                tenant_id=1,
                reservation=sample_reservation
            )

            assert lease_id == 100
            # Verify lease was created with correct data
            sync.pm.create_lease.assert_called_once()
            call_args = sync.pm.create_lease.call_args[0][0]
            assert call_args["lease_type"] == "nightly"
            assert call_args["rent_frequency"] == "nightly"
            assert call_args["start_date"] == "2025-02-01"
            assert call_args["end_date"] == "2025-02-07"

    @pytest.mark.unit
    def test_reservation_status_mapping(self):
        """Test reservation status mapping to lease status"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()

            status_map = {
                ReservationStatus.PENDING: "pending",
                ReservationStatus.CONFIRMED: "active",
                ReservationStatus.CHECKED_IN: "active",
                ReservationStatus.CHECKED_OUT: "expired",
                ReservationStatus.CANCELLED: "terminated",
                ReservationStatus.DECLINED: "terminated",
            }

            for res_status, expected_lease_status in status_map.items():
                mapped = sync._map_reservation_status(res_status)
                assert mapped == expected_lease_status


class TestPaymentSync:
    """Tests for payment recording"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_record_payment_when_paid(self, sample_reservation):
        """Test payment recorded for paid reservations"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = AsyncMock()
            sync.pm.record_payment = AsyncMock(return_value={
                "status": "success"
            })

            result = await sync._record_payment(lease_id=100, reservation=sample_reservation)

            assert result is True
            sync.pm.record_payment.assert_called_once()
            call_args = sync.pm.record_payment.call_args[0][0]
            assert call_args["status"] == "paid"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_payment_amount_from_reservation(self, sample_reservation):
        """Test payment records correct amount"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.pm = AsyncMock()
            sync.pm.record_payment = AsyncMock(return_value={
                "status": "success"
            })

            await sync._record_payment(lease_id=100, reservation=sample_reservation)

            call_args = sync.pm.record_payment.call_args[0][0]
            assert float(call_args["amount"]) == 1730.0


class TestBulkSync:
    """Tests for bulk reservation synchronization"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_all_reservations(self):
        """Test syncing all reservations from provider"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry") as mock_registry_class:
            sync = PMSSyncService()

            # Mock provider
            mock_provider = AsyncMock()

            from instruments.custom.pms_hub.canonical_models import Reservation
            reservations = [
                Reservation(
                    provider_id="r1",
                    provider="test",
                    property_provider_id="p1",
                    check_in_date=date(2025, 2, 1),
                    check_out_date=date(2025, 2, 7),
                ),
                Reservation(
                    provider_id="r2",
                    provider="test",
                    property_provider_id="p1",
                    check_in_date=date(2025, 2, 8),
                    check_out_date=date(2025, 2, 15),
                ),
            ]

            mock_provider.get_reservations = AsyncMock(return_value=reservations)

            # Mock provider registry
            sync.registry = AsyncMock()
            sync.registry.get_provider_async = AsyncMock(return_value=mock_provider)

            # Mock sync method
            with patch.object(
                sync,
                "sync_reservation_to_property_manager",
                return_value=(True, 1)
            ):
                synced, errors = await sync.sync_all_reservations("test_provider")

            # Should have synced 2 reservations
            assert synced == 2
            assert errors == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_with_errors(self):
        """Test bulk sync handles errors"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()

            # Mock provider
            mock_provider = AsyncMock()

            from instruments.custom.pms_hub.canonical_models import Reservation
            reservations = [
                Reservation(
                    provider_id="r1",
                    provider="test",
                    property_provider_id="p1",
                    check_in_date=date(2025, 2, 1),
                    check_out_date=date(2025, 2, 7),
                ),
                Reservation(
                    provider_id="r2",
                    provider="test",
                    property_provider_id="p1",
                    check_in_date=date(2025, 2, 8),
                    check_out_date=date(2025, 2, 15),
                ),
            ]

            mock_provider.get_reservations = AsyncMock(return_value=reservations)
            sync.registry = AsyncMock()
            sync.registry.get_provider_async = AsyncMock(return_value=mock_provider)

            # Mock sync - first succeeds, second fails
            with patch.object(
                sync,
                "sync_reservation_to_property_manager",
                side_effect=[(True, 1), (False, None)]
            ):
                synced, errors = await sync.sync_all_reservations("test_provider")

            assert synced == 1
            assert errors == 1


class TestSyncStatus:
    """Tests for sync status reporting"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_sync_status(self):
        """Test getting sync status"""
        with patch("instruments.custom.pms_hub.sync_service.ProviderRegistry"):
            sync = PMSSyncService()
            sync.registry.list_providers = MagicMock(return_value=["p1", "p2"])

            status = await sync.get_sync_status()

            assert "providers" in status
            assert status["providers"] == 2
            assert "providers_enabled" in status
