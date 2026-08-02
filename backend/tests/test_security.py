import pytest
from fastapi.testclient import TestClient
from app.main import app
import asyncio
from app.db.session import AsyncSessionLocal
from app.db.crud import create_api_key
from sqlalchemy import select, delete
from app.models.api_key import APIKey

client = TestClient(app)


class TestSecurity:
    """Test security middleware."""

    @pytest.fixture(autouse=True)
    def setup_test_key(self):
        """Create a clean test API key before tests."""
        async def _create_clean_key():
            async with AsyncSessionLocal() as db:
                # Önce tüm test-key'leri temizle
                await db.execute(delete(APIKey).where(APIKey.name == "test-key"))
                await db.commit()
                
                # Yeni key oluştur
                key_obj = await create_api_key(db, name="test-key", rate_limit="10/minute")
                print(f"Created fresh API key: {key_obj.key[:8]}...")
                return key_obj.key
        
        self.test_key = asyncio.run(_create_clean_key())
        yield
        # Test sonrası temizlik yapılabilir

    def test_health_public(self):
        """Test public health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_upload_without_api_key(self):
        """Test upload without API key."""
        response = client.post("/api/v1/upload/")
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]

    def test_upload_with_invalid_api_key(self):
        """Test upload with invalid API key."""
        headers = {"X-API-Key": "invalid-key"}
        response = client.post("/api/v1/upload/", headers=headers)
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_upload_with_valid_api_key(self):
        """Test upload with valid API key."""
        headers = {"X-API-Key": self.test_key}
        
        # Test dosyası oluştur
        import io
        from PIL import Image
        
        img = Image.new('RGB', (100, 100), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        response = client.post(
            "/api/v1/upload/",
            headers=headers,
            files={"file": ("test.jpg", img_byte_arr.getvalue(), "image/jpeg")}
        )
        
        # 202 (Accepted) veya 429 (Rate limit) beklenir
        assert response.status_code in [202, 429]

    def test_rate_limiting(self):
        """Test rate limiting."""
        headers = {"X-API-Key": self.test_key}
        rate_limited = False
        
        # Test dosyası oluştur
        import io
        from PIL import Image
        
        for i in range(15):
            img = Image.new('RGB', (100, 100), color='red')
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            
            response = client.post(
                "/api/v1/upload/",
                headers=headers,
                files={"file": ("test.jpg", img_byte_arr.getvalue(), "image/jpeg")}
            )
            if response.status_code == 429:
                rate_limited = True
                break
            assert response.status_code in [202, 429]
        
        assert rate_limited, "Rate limiting did not trigger"