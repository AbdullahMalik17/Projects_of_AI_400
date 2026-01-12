from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.models.task import Task, TaskStatus

def test_nl_create_task(client: TestClient):
    # Mock the Gemini API response
    mock_response = MagicMock()
    mock_response.text = '''
    {
        "title": "Call John",
        "description": "Call John tomorrow at 2pm",
        "due_date": "2024-01-20T14:00:00",
        "priority": "high",
        "tags": ["communication"],
        "estimated_duration": 15
    }
    '''
    
    # Patch the GenerativeModel.generate_content_async method
    with patch("google.generativeai.GenerativeModel.generate_content_async", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response
        
        response = client.post(
            "/api/v1/tasks/nl-create",
            json={
                "message": "Call John tomorrow at 2pm",
                "context": {"timezone": "UTC"}
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Call John"
        assert data["data"]["priority"] == "high"
        # Check if tags were created/linked (this depends on if tags exist, implementation might skip if tag "communication" doesn't exist or auto-create)
        # The parser returns 'tags' list of strings. The service layer handles creation.
        
def test_task_breakdown(client: TestClient):
    # First create a task
    create_res = client.post(
        "/api/v1/tasks",
        json={"title": "Big Project"}
    )
    task_id = create_res.json()["data"]["id"]

    # Mock Gemini response for breakdown
    mock_response = MagicMock()
    mock_response.text = '["Step 1", "Step 2", "Step 3"]'

    with patch("google.generativeai.GenerativeModel.generate_content_async", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_response

        response = client.post(f"/api/v1/tasks/{task_id}/breakdown")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3
        assert data["data"][0]["title"] == "Step 1"
        assert data["data"][0]["parent_task_id"] == task_id
