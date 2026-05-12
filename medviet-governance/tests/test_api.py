import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.access.rbac import MOCK_USERS


client = TestClient(app)


class TestAPIEndpoints:
    """Test FastAPI endpoints with RBAC"""

    def test_health_check(self):
        """Test health endpoint (no auth required)"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "MedViet Data API"

    class TestRawPatientsEndpoint:
        """GET /api/patients/raw - Admin only"""

        def test_admin_can_access(self):
            """Test admin role can access raw data"""
            token = "Bearer token-alice"  # alice = admin
            headers = {"Authorization": token}
            response = client.get("/api/patients/raw", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 10

        def test_ml_engineer_denied(self):
            """Test ml_engineer role denied access to raw data"""
            token = "Bearer token-bob"  # bob = ml_engineer
            headers = {"Authorization": token}
            response = client.get("/api/patients/raw", headers=headers)
            assert response.status_code == 403

        def test_data_analyst_denied(self):
            """Test data_analyst role denied access to raw data"""
            token = "Bearer token-carol"  # carol = data_analyst
            headers = {"Authorization": token}
            response = client.get("/api/patients/raw", headers=headers)
            assert response.status_code == 403

        def test_intern_denied(self):
            """Test intern role denied access to raw data"""
            token = "Bearer token-dave"  # dave = intern
            headers = {"Authorization": token}
            response = client.get("/api/patients/raw", headers=headers)
            assert response.status_code == 403

        def test_no_token_unauthorized(self):
            """Test missing token returns 401"""
            response = client.get("/api/patients/raw")
            assert response.status_code == 401

        def test_invalid_token_unauthorized(self):
            """Test invalid token returns 401"""
            headers = {"Authorization": "Bearer invalid_token"}
            response = client.get("/api/patients/raw", headers=headers)
            assert response.status_code == 401

    class TestAnonymizedPatientsEndpoint:
        """GET /api/patients/anonymized - ml_engineer + admin"""

        def test_admin_can_access(self):
            """Test admin can access anonymized data"""
            token = "Bearer token-alice"
            headers = {"Authorization": token}
            response = client.get("/api/patients/anonymized", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

        def test_ml_engineer_can_access(self):
            """Test ml_engineer can access anonymized data"""
            token = "Bearer token-bob"
            headers = {"Authorization": token}
            response = client.get("/api/patients/anonymized", headers=headers)
            assert response.status_code == 200

        def test_data_analyst_denied(self):
            """Test data_analyst cannot access training data"""
            token = "Bearer token-carol"
            headers = {"Authorization": token}
            response = client.get("/api/patients/anonymized", headers=headers)
            assert response.status_code == 403

        def test_intern_denied(self):
            """Test intern cannot access training data"""
            token = "Bearer token-dave"
            headers = {"Authorization": token}
            response = client.get("/api/patients/anonymized", headers=headers)
            assert response.status_code == 403

    class TestAggregatedMetricsEndpoint:
        """GET /api/metrics/aggregated - data_analyst + ml_engineer + admin"""

        def test_admin_can_access(self):
            """Test admin can access metrics"""
            token = "Bearer token-alice"
            headers = {"Authorization": token}
            response = client.get("/api/metrics/aggregated", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data
            assert isinstance(data["metrics"], list)

        def test_ml_engineer_can_access(self):
            """Test ml_engineer can access metrics"""
            token = "Bearer token-bob"
            headers = {"Authorization": token}
            response = client.get("/api/metrics/aggregated", headers=headers)
            assert response.status_code == 200

        def test_data_analyst_can_access(self):
            """Test data_analyst can access metrics"""
            token = "Bearer token-carol"
            headers = {"Authorization": token}
            response = client.get("/api/metrics/aggregated", headers=headers)
            assert response.status_code == 200

        def test_intern_denied(self):
            """Test intern cannot access metrics"""
            token = "Bearer token-dave"
            headers = {"Authorization": token}
            response = client.get("/api/metrics/aggregated", headers=headers)
            assert response.status_code == 403

    class TestDeletePatientEndpoint:
        """DELETE /api/patients/{patient_id} - Admin only"""

        def test_admin_can_delete(self):
            """Test admin can delete patient"""
            token = "Bearer token-alice"
            headers = {"Authorization": token}
            response = client.delete("/api/patients/P123", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"

        def test_ml_engineer_denied(self):
            """Test ml_engineer cannot delete"""
            token = "Bearer token-bob"
            headers = {"Authorization": token}
            response = client.delete("/api/patients/P123", headers=headers)
            assert response.status_code == 403

        def test_data_analyst_denied(self):
            """Test data_analyst cannot delete"""
            token = "Bearer token-carol"
            headers = {"Authorization": token}
            response = client.delete("/api/patients/P123", headers=headers)
            assert response.status_code == 403

        def test_intern_denied(self):
            """Test intern cannot delete"""
            token = "Bearer token-dave"
            headers = {"Authorization": token}
            response = client.delete("/api/patients/P123", headers=headers)
            assert response.status_code == 403


class TestRBACRoles:
    """Test RBAC role matrix"""

    ROLE_PERMISSIONS = {
        "admin": {
            "/api/patients/raw": 200,
            "/api/patients/anonymized": 200,
            "/api/metrics/aggregated": 200,
            "/api/patients/P123 DELETE": 200,
        },
        "ml_engineer": {
            "/api/patients/raw": 403,
            "/api/patients/anonymized": 200,
            "/api/metrics/aggregated": 200,
            "/api/patients/P123 DELETE": 403,
        },
        "data_analyst": {
            "/api/patients/raw": 403,
            "/api/patients/anonymized": 403,
            "/api/metrics/aggregated": 200,
            "/api/patients/P123 DELETE": 403,
        },
        "intern": {
            "/api/patients/raw": 403,
            "/api/patients/anonymized": 403,
            "/api/metrics/aggregated": 403,
            "/api/patients/P123 DELETE": 403,
        },
    }

    def test_rbac_matrix(self):
        """Verify complete RBAC role matrix"""
        token_map = {
            "admin": "Bearer token-alice",
            "ml_engineer": "Bearer token-bob",
            "data_analyst": "Bearer token-carol",
            "intern": "Bearer token-dave",
        }

        for role, permissions in self.ROLE_PERMISSIONS.items():
            token = token_map[role]
            headers = {"Authorization": token}

            # Test GET /api/patients/raw
            response = client.get("/api/patients/raw", headers=headers)
            expected = permissions["/api/patients/raw"]
            assert response.status_code == expected, \
                f"{role} on /api/patients/raw: got {response.status_code}, expected {expected}"

            # Test GET /api/patients/anonymized
            response = client.get("/api/patients/anonymized", headers=headers)
            expected = permissions["/api/patients/anonymized"]
            assert response.status_code == expected, \
                f"{role} on /api/patients/anonymized: got {response.status_code}, expected {expected}"

            # Test GET /api/metrics/aggregated
            response = client.get("/api/metrics/aggregated", headers=headers)
            expected = permissions["/api/metrics/aggregated"]
            assert response.status_code == expected, \
                f"{role} on /api/metrics/aggregated: got {response.status_code}, expected {expected}"

            # Test DELETE /api/patients/P123
            response = client.delete("/api/patients/P123", headers=headers)
            expected = permissions["/api/patients/P123 DELETE"]
            assert response.status_code == expected, \
                f"{role} on DELETE /api/patients/P123: got {response.status_code}, expected {expected}"
