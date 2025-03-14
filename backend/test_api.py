import requests
import json

def test_health_endpoint():
    response = requests.get("http://localhost:3001/api/health")
    print(f"Health endpoint: {response.status_code}")
    print(response.json())
    
def test_connection_endpoint():
    response = requests.get("http://localhost:3001/api/test")
    print(f"Test connection endpoint: {response.status_code}")
    print(response.json())
    
def test_mock_token_endpoint():
    response = requests.post("http://localhost:3001/api/mock-token")
    print(f"Mock token endpoint: {response.status_code}")
    print(response.json())
    
if __name__ == "__main__":
    print("Testing FastAPI backend endpoints...")
    test_health_endpoint()
    test_connection_endpoint()
    test_mock_token_endpoint()
    print("Tests completed.")
