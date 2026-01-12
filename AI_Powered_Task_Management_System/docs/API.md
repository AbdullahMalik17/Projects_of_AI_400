# API Reference

**Base URL**: `http://localhost:8000/api/v1`
**Version**: 1.0
**Format**: JSON

---

## Authentication

*Currently, the system operates in single-user mode. Authentication headers are prepared for future implementation.*

**Future Header**: `Authorization: Bearer <token>`

---

## Tasks

### Create Task
Create a new task with structured data.

- **Endpoint**: `POST /tasks`
- **Body**:
  ```json
  {
    "title": "string",
    "description": "string",
    "priority": "low" | "medium" | "high",
    "due_date": "ISO8601 string",
    "estimated_duration": integer (minutes)
  }
  ```
- **Response**: `201 Created` - Returns created task object.

### Create Task (Natural Language)
Create a task by describing it in plain English. The AI will parse details like date, priority, and description.

- **Endpoint**: `POST /tasks/nl-create`
- **Body**:
  ```json
  {
    "message": "Remind me to email Sarah about the presentation by Friday at 2pm",
    "context": {
      "timezone": "America/New_York"
    }
  }
  ```
- **Response**: `201 Created` - Returns created task object.

### List Tasks
Retrieve a list of tasks with optional filtering and pagination.

- **Endpoint**: `GET /tasks`
- **Query Parameters**:
  - `status`: `todo`, `in_progress`, `completed`
  - `priority`: `low`, `medium`, `high`
  - `skip`: Number of records to skip (default: 0)
  - `limit`: Max records to return (default: 50)
  - `include_subtasks`: `true` (default) or `false`
- **Response**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "tasks": [...],
      "total": 10,
      "page": 1,
      "has_more": false
    }
  }
  ```

### Get Task Details
Retrieve full details for a specific task, including subtasks and tags.

- **Endpoint**: `GET /tasks/{id}`
- **Response**: `200 OK` - Returns task object.

### Update Task
Update specific fields of an existing task.

- **Endpoint**: `PUT /tasks/{id}`
- **Body**: (Partial object)
  ```json
  {
    "status": "in_progress",
    "actual_duration": 45
  }
  ```
- **Response**: `200 OK` - Returns updated task.

### Delete Task
Delete a task.

- **Endpoint**: `DELETE /tasks/{id}`
- **Query Parameters**:
  - `cascade_subtasks`: `true` or `false` (default: `false`)
- **Response**: `200 OK`

### Complete Task
Mark a task as completed, optionally recording the actual duration.

- **Endpoint**: `POST /tasks/{id}/complete`
- **Query Parameters**:
  - `actual_duration`: Integer (minutes)
- **Response**: `200 OK`

---

## Task Intelligence & Operations

### Task Breakdown
Use AI to suggest subtasks for a complex task.

- **Endpoint**: `POST /tasks/{id}/breakdown`
- **Response**: `200 OK` - Returns list of created subtasks.

### Task Insights
Get AI-generated analysis and recommendations for a specific task.

- **Endpoint**: `GET /tasks/{id}/insights`
- **Response**: `200 OK`
  ```json
  {
    "suggested_priority": "high",
    "estimated_duration_minutes": 60,
    "recommendations": ["..."]
  }
  ```

### Productivity Insights
Get high-level productivity metrics and advice based on your task history.

- **Endpoint**: `GET /tasks/insights/productivity`
- **Response**: `200 OK`
  ```json
  {
    "insights": ["Completion rate is up 10%"],
    "recommendations": ["Try tackling high priority tasks in the morning"]
  }
  ```

### Search Tasks
Search tasks by title or description.

- **Endpoint**: `GET /tasks/search`
- **Query Parameters**:
  - `q`: Search query (min 2 chars)
- **Response**: `200 OK` - List of matching tasks.

### Get Overdue Tasks
Retrieve tasks that are past their due date and incomplete.

- **Endpoint**: `GET /tasks/overdue`
- **Response**: `200 OK` - List of overdue tasks.

### Get Upcoming Tasks
Retrieve tasks due within the specified number of days.

- **Endpoint**: `GET /tasks/upcoming`
- **Query Parameters**:
  - `days`: Number of days to look ahead (default: 7)
- **Response**: `200 OK` - List of upcoming tasks.

### Get Statistics
Get count of tasks by status and other metrics.

- **Endpoint**: `GET /tasks/statistics`
- **Response**: `200 OK`
  ```json
  {
    "total": 50,
    "todo": 20,
    "completed": 30,
    "overdue": 5
  }
  ```

---

## System

### Health Check
Check if the API is running.

- **Endpoint**: `GET /health`
- **Response**: `200 OK`
  ```json
  {
    "status": "healthy",
    "version": "0.1.0"
  }
  ```

### Root
Basic API info.

- **Endpoint**: `GET /`
- **Response**: `200 OK`
