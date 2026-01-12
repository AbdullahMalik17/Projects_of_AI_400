from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models.task import Task, TaskStatus, Priority

def test_create_task(client: TestClient):
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "priority": "medium",
            "due_date": None,
            "estimated_duration": 60
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Test Task"
    assert data["data"]["priority"] == "medium"
    assert data["data"]["user_id"] == 1

def test_read_tasks(client: TestClient):
    # Create a task first
    client.post(
        "/api/v1/tasks",
        json={"title": "Task 1", "priority": "high"}
    )
    client.post(
        "/api/v1/tasks",
        json={"title": "Task 2", "priority": "low"}
    )

    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["tasks"]) >= 2

def test_update_task(client: TestClient):
    # Create task
    create_res = client.post(
        "/api/v1/tasks",
        json={"title": "Original Title"}
    )
    task_id = create_res.json()["data"]["id"]

    # Update task
    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated Title", "status": "in_progress"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Updated Title"
    assert data["data"]["status"] == "in_progress"

def test_delete_task(client: TestClient):
    # Create task
    create_res = client.post(
        "/api/v1/tasks",
        json={"title": "To Delete"}
    )
    task_id = create_res.json()["data"]["id"]

    # Delete task
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    
    # Verify deletion
    get_res = client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 404  # Assuming get_task raises 404 if not found
    # Or if your API returns null, check that. 
    # Based on standard FastAPI patterns, 404 is expected.

def test_search_tasks(client: TestClient):
    client.post(
        "/api/v1/tasks",
        json={"title": "Buy Groceries", "description": "Milk and eggs"}
    )
    
    response = client.get("/api/v1/tasks/search?q=Milk")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert data["data"][0]["title"] == "Buy Groceries"

def test_complete_task(client: TestClient):
    create_res = client.post(
        "/api/v1/tasks",
        json={"title": "Complete Me"}
    )
    task_id = create_res.json()["data"]["id"]
    
    response = client.post(f"/api/v1/tasks/{task_id}/complete?actual_duration=30")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "completed"
    assert data["data"]["completed_at"] is not None
