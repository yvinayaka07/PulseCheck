"""
PulseCheck - Test Suite
Tests for root and health endpoints covering status codes and response shapes.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Root endpoint tests
# ---------------------------------------------------------------------------


class TestRootEndpoint:
    """Tests for GET /"""

    def test_root_returns_200(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_json(self):
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_contains_service_key(self):
        response = client.get("/")
        data = response.json()
        assert "service" in data

    def test_root_contains_status_key(self):
        response = client.get("/")
        data = response.json()
        assert "status" in data

    def test_root_service_value(self):
        response = client.get("/")
        data = response.json()
        assert data["service"] == "PulseCheck"

    def test_root_status_value(self):
        response = client.get("/")
        data = response.json()
        assert data["status"] == "running"


# ---------------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------------


MOCK_HEALTH_REPORT = {
    "status": "healthy",
    "timestamp": "2024-06-01T12:00:00+00:00",
    "cpu_usage_percent": 12.5,
    "memory_usage_percent": 45.0,
    "disk_usage_percent": 60.0,
    "external_api_status": "reachable",
}


class TestHealthEndpoint:
    """Tests for GET /health"""

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_returns_200(self, mock_report):
        response = client.get("/health")
        assert response.status_code == 200

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_returns_json(self, mock_report):
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_status_is_healthy(self, mock_report):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_contains_timestamp(self, mock_report):
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        assert data["timestamp"] != ""

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_contains_cpu_usage(self, mock_report):
        response = client.get("/health")
        data = response.json()
        assert "cpu_usage_percent" in data
        assert isinstance(data["cpu_usage_percent"], (int, float))

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_contains_memory_usage(self, mock_report):
        response = client.get("/health")
        data = response.json()
        assert "memory_usage_percent" in data
        assert isinstance(data["memory_usage_percent"], (int, float))

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_contains_disk_usage(self, mock_report):
        response = client.get("/health")
        data = response.json()
        assert "disk_usage_percent" in data
        assert isinstance(data["disk_usage_percent"], (int, float))

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_contains_external_api_status(self, mock_report):
        response = client.get("/health")
        data = response.json()
        assert "external_api_status" in data
        assert data["external_api_status"] in ("reachable", "unreachable")

    @patch("app.main.build_health_report", side_effect=Exception("boom"))
    def test_health_returns_500_on_exception(self, mock_report):
        response = client.get("/health")
        assert response.status_code == 500

    @patch("app.main.build_health_report", return_value=MOCK_HEALTH_REPORT)
    def test_health_full_schema(self, mock_report):
        """Validate every expected key exists and has the correct type."""
        response = client.get("/health")
        data = response.json()
        required_keys = {
            "status": str,
            "timestamp": str,
            "cpu_usage_percent": (int, float),
            "memory_usage_percent": (int, float),
            "disk_usage_percent": (int, float),
            "external_api_status": str,
        }
        for key, expected_type in required_keys.items():
            assert key in data, f"Missing key: {key}"
            assert isinstance(data[key], expected_type), (
                f"Key '{key}' has wrong type. "
                f"Expected {expected_type}, got {type(data[key])}"
            )


# ---------------------------------------------------------------------------
# Unit tests for health service helpers
# ---------------------------------------------------------------------------


class TestHealthServiceHelpers:
    """Unit tests for individual health.py helpers."""

    @patch("psutil.cpu_percent", return_value=55.5)
    def test_get_cpu_usage(self, mock_cpu):
        from app.health import get_cpu_usage
        result = get_cpu_usage()
        assert result == 55.5

    @patch("psutil.virtual_memory")
    def test_get_memory_usage(self, mock_vm):
        mock_vm.return_value = MagicMock(percent=70.2)
        from app.health import get_memory_usage
        result = get_memory_usage()
        assert result == 70.2

    @patch("psutil.disk_usage")
    def test_get_disk_usage(self, mock_disk):
        mock_disk.return_value = MagicMock(percent=80.0)
        from app.health import get_disk_usage
        result = get_disk_usage()
        assert result == 80.0

    @patch("app.health._build_retry_session")
    def test_check_external_api_reachable(self, mock_session_builder):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_builder.return_value = mock_session

        from app.health import check_external_api
        result = check_external_api()
        assert result == "reachable"

    @patch("app.health._build_retry_session")
    def test_check_external_api_unreachable_on_timeout(self, mock_session_builder):
        import requests as req
        mock_session = MagicMock()
        mock_session.get.side_effect = req.exceptions.Timeout()
        mock_session_builder.return_value = mock_session

        from app.health import check_external_api
        result = check_external_api()
        assert result == "unreachable"
