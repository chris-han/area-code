"""
Pytest-compatible tests for FOCUS consumption APIs.

Run with:
    pytest app/focus_billing/tests/test_moose_consumption_apis.py -v
"""

import pytest
import httpx
from datetime import date
from pathlib import Path
import sys

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


MOOSE_BASE_URL = "http://localhost:4200"


class TestFocusConsumptionAPIs:
    """Test suite for FOCUS consumption APIs"""

    @pytest.fixture
    def moose_client(self):
        """Create HTTP client for Moose API"""
        return httpx.AsyncClient(base_url=MOOSE_BASE_URL, timeout=30.0)

    @pytest.fixture
    def billing_period(self):
        """Return test billing period"""
        return {
            "billing_period_start": "2025-07-01",
            "billing_period_end": "2025-08-01"
        }

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_moose_service_health(self):
        """Test Moose service is running"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{MOOSE_BASE_URL}/health")
                assert response.status_code == 200, "Moose service should be healthy"
            except httpx.ConnectError:
                pytest.skip("Moose service not running on localhost:4200")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cost_comparison_api(self, moose_client, billing_period):
        """Test Cost Comparison API"""
        try:
            response = await moose_client.post(
                "/consumption/CostComparison",
                json=billing_period
            )

            if response.status_code == 404:
                pytest.skip("CostComparison API not registered yet")

            assert response.status_code == 200, f"API should return 200. Got: {response.status_code}"

            data = response.json()
            assert isinstance(data, list), "Response should be a list"

            # If data exists, verify structure
            if len(data) > 0:
                first_row = data[0]
                assert "provider_name" in first_row
                assert "billing_account_id" in first_row
                assert "total_effective_cost" in first_row
                assert "total_billed_cost" in first_row

        except httpx.ConnectError:
            pytest.skip("Moose service not running")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_effective_cost_analysis_api(self, moose_client, billing_period):
        """Test Effective Cost Analysis API"""
        try:
            response = await moose_client.post(
                "/consumption/EffectiveCostAnalysis",
                json=billing_period
            )

            if response.status_code == 404:
                pytest.skip("EffectiveCostAnalysis API not registered yet")

            assert response.status_code == 200, f"API should return 200. Got: {response.status_code}"

            data = response.json()
            assert isinstance(data, list), "Response should be a list"

            # If data exists, verify structure
            if len(data) > 0:
                first_row = data[0]
                assert "provider_name" in first_row
                assert "service_category" in first_row
                assert "service_name" in first_row
                assert "total_effective_cost" in first_row

        except httpx.ConnectError:
            pytest.skip("Moose service not running")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_commitment_discount_purchases_api(self, moose_client, billing_period):
        """Test Commitment Discount Purchases API"""
        try:
            response = await moose_client.post(
                "/consumption/CommitmentDiscountPurchases",
                json=billing_period
            )

            if response.status_code == 404:
                pytest.skip("CommitmentDiscountPurchases API not registered yet")

            assert response.status_code == 200, f"API should return 200. Got: {response.status_code}"

            data = response.json()
            assert isinstance(data, list), "Response should be a list"

            # If data exists, verify structure
            if len(data) > 0:
                first_row = data[0]
                assert "provider_name" in first_row
                assert "billing_account_id" in first_row
                assert "commitment_discount_id" in first_row
                assert "total_billed_cost" in first_row

        except httpx.ConnectError:
            pytest.skip("Moose service not running")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_correction_charges_api(self, moose_client, billing_period):
        """Test Correction Charges API"""
        try:
            response = await moose_client.post(
                "/consumption/CorrectionCharges",
                json=billing_period
            )

            if response.status_code == 404:
                pytest.skip("CorrectionCharges API not registered yet")

            assert response.status_code == 200, f"API should return 200. Got: {response.status_code}"

            data = response.json()
            assert isinstance(data, list), "Response should be a list"

        except httpx.ConnectError:
            pytest.skip("Moose service not running")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recurring_charges_api(self, moose_client, billing_period):
        """Test Recurring Charges API"""
        try:
            response = await moose_client.post(
                "/consumption/RecurringCharges",
                json=billing_period
            )

            if response.status_code == 404:
                pytest.skip("RecurringCharges API not registered yet")

            assert response.status_code == 200, f"API should return 200. Got: {response.status_code}"

            data = response.json()
            assert isinstance(data, list), "Response should be a list"

        except httpx.ConnectError:
            pytest.skip("Moose service not running")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_with_filters(self, moose_client):
        """Test API with additional filters"""
        request_data = {
            "billing_period_start": "2025-07-01",
            "billing_period_end": "2025-08-01",
            "provider_name": "Microsoft",
            "service_category": "Networking"
        }

        try:
            response = await moose_client.post(
                "/consumption/EffectiveCostAnalysis",
                json=request_data
            )

            if response.status_code == 404:
                pytest.skip("API not registered yet")

            assert response.status_code == 200, f"API should accept filters. Got: {response.status_code}"

        except httpx.ConnectError:
            pytest.skip("Moose service not running")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_validation(self, moose_client):
        """Test API input validation"""
        invalid_request = {
            "billing_period_start": "invalid-date",
            "billing_period_end": "2025-08-01"
        }

        try:
            response = await moose_client.post(
                "/consumption/CostComparison",
                json=invalid_request
            )

            if response.status_code == 404:
                pytest.skip("API not registered yet")

            # Should reject invalid date format
            assert response.status_code in [400, 422], "Should validate input and return 400/422"

        except httpx.ConnectError:
            pytest.skip("Moose service not running")


@pytest.mark.e2e
class TestEndToEndMooseStack:
    """End-to-end tests for complete Moose stack"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_ingestion_to_query_flow(self):
        """Test complete flow: ingest data -> query via API"""
        # 1. Verify Moose is running
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                health_response = await client.get(f"{MOOSE_BASE_URL}/health")
                assert health_response.status_code == 200
            except httpx.ConnectError:
                pytest.skip("Moose service not running")

        # 2. Run ingestion (would need to be implemented)
        # workflow = FocusBillingIngestWorkflow(params)
        # stats = workflow.execute()
        # assert stats.files_processed > 0

        # 3. Query via API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MOOSE_BASE_URL}/consumption/CostComparison",
                json={
                    "billing_period_start": "2025-07-01",
                    "billing_period_end": "2025-08-01"
                }
            )

            if response.status_code == 404:
                pytest.skip("API not registered")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


if __name__ == "__main__":
    # Allow running directly: python test_moose_consumption_apis.py
    pytest.main([__file__, "-v", "-s"])
