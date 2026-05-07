import sys
import traceback
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
try:
    response = client.post("/auth/signup", json={"email": "test@example.com", "username": "testuser", "password": "testpass"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
    traceback.print_exc()
