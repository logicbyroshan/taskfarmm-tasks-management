# 🔌 API Documentation

API endpoints and integration guide for TaskMitra.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Task Endpoints](#task-endpoints)
- [Category Endpoints](#category-endpoints)
- [External Auth Integration](#external-auth-integration)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## 🌐 Overview

TaskMitra provides AJAX-based API endpoints for task and category management, along with prepared endpoints for external authentication integration.

### **Base URL**
```
http://127.0.0.1:8000
```

### **Content Type**
```
Content-Type: application/json
```

### **CSRF Protection**
All POST, PUT, DELETE requests require a CSRF token:
```javascript
headers: {
    'X-CSRFToken': getCookie('csrftoken'),
    'Content-Type': 'application/json'
}
```

---

## 🔐 Authentication

### **Current Implementation: Demo Auth**

The application currently uses `DemoAuthMiddleware` that automatically logs in users as `demo_user`. No authentication is required for development.

```python
# Middleware auto-creates/logs in user
username: demo_user
email: demo@taskmitra.com
```

### **Future: External Authentication**

Prepared endpoints for JWT-based external authentication:

#### **Verify Token**
```http
POST /api/auth/verify/
```

**Request Body:**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
    "valid": true,
    "user_id": 1,
    "username": "demo_user"
}
```

#### **Get User Info**
```http
GET /api/auth/user-info/
```

**Response:**
```json
{
    "id": 1,
    "username": "demo_user",
    "email": "demo@taskflix.com",
    "first_name": "Demo",
    "last_name": "User"
}
```

---

## 🤖 AI Assistant Endpoints

### **AI Suggest Task & Plan**

```http
POST /api/ai/suggest/
```

**Request Body:**
```json
{
    "prompt": "Create a website launch strategy with subtasks"
}
```

**Response:**
```json
{
    "success": true,
    "title": "Launch Strategy & Production Readiness",
    "suggestion": "1. Finalize DNS records & SSL certificate configuration.\n2. Run cross-browser compatibility and lighthouse performance audit.\n3. Execute production database migrations.",
    "description": "1. Finalize DNS records & SSL certificate configuration...",
    "prompt": "Create a website launch strategy with subtasks"
}
```

---

## 📝 Task Endpoints

### **1. Create Task**

```http
POST /task/add/
```

**Request Body:**
```json
{
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation",
    "category": 2,
    "priority": "high",
    "status": "in_progress",
    "due_date": "2025-11-20T15:30:00"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Task created successfully",
    "task_id": 15
}
```

**JavaScript Example:**
```javascript
async function addTask() {
    const formData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        category: document.getElementById('task-category').value,
        priority: document.getElementById('task-priority').value,
        status: document.getElementById('task-status').value,
        due_date: document.getElementById('task-due-date').value
    };

    const response = await fetch('/task/add/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    const data = await response.json();
    if (data.success) {
        console.log('Task created:', data.task_id);
        location.reload();
    }
}
```

---

### **2. Update Task**

```http
POST /task/update/<task_id>/
```

**Request Body:**
```json
{
    "title": "Updated task title",
    "description": "Updated description",
    "category": 3,
    "priority": "medium",
    "status": "completed",
    "due_date": "2025-11-25T10:00:00"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Task updated successfully"
}
```

**JavaScript Example:**
```javascript
async function updateTask(taskId) {
    const formData = {
        title: document.getElementById('edit-task-title').value,
        description: document.getElementById('edit-task-description').value,
        category: document.getElementById('edit-task-category').value,
        priority: document.getElementById('edit-task-priority').value,
        status: document.getElementById('edit-task-status').value,
        due_date: document.getElementById('edit-task-due-date').value
    };

    const response = await fetch(`/task/update/${taskId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    const data = await response.json();
    if (data.success) {
        location.reload();
    }
}
```

---

### **3. Delete Task**

```http
POST /task/delete/<task_id>/
```

**Response:**
```json
{
    "success": true,
    "message": "Task deleted successfully"
}
```

**JavaScript Example:**
```javascript
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }

    const response = await fetch(`/task/delete/${taskId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    });

    const data = await response.json();
    if (data.success) {
        location.reload();
    }
}
```

---

## 🏷️ Category Endpoints

### **1. Create Category**

```http
POST /category/add/
```

**Request Body:**
```json
{
    "name": "Work Projects",
    "color": "#2e86de"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Category created successfully",
    "category_id": 5
}
```

**JavaScript Example:**
```javascript
async function addCategory() {
    const formData = {
        name: document.getElementById('category-name').value,
        color: document.getElementById('category-color').value
    };

    const response = await fetch('/category/add/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    const data = await response.json();
    if (data.success) {
        location.reload();
    }
}
```

---

### **2. Update Category**

```http
POST /category/update/<category_id>/
```

**Request Body:**
```json
{
    "name": "Updated Category Name",
    "color": "#e74c3c"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Category updated successfully"
}
```

---

### **3. Delete Category**

```http
POST /category/delete/<category_id>/
```

**Response:**
```json
{
    "success": true,
    "message": "Category deleted successfully"
}
```

---

## 🔗 External Auth Integration

### **Integration Steps**

#### **1. Disable Demo Auth Middleware**

Remove from `config/settings.py`:
```python
MIDDLEWARE = [
    # ...
    # 'todo.middleware.DemoAuthMiddleware',  # REMOVE THIS
]
```

#### **2. Implement Token Verification**

Update `todo/api_auth.py`:
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
import jwt

@api_view(['POST'])
def verify_token(request):
    """Verify JWT token from external auth service"""
    token = request.data.get('token')
    
    try:
        # Verify token with your auth service
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=decoded['email'],
            defaults={
                'username': decoded['username'],
                'first_name': decoded.get('first_name', ''),
                'last_name': decoded.get('last_name', '')
            }
        )
        
        # Log in user
        login(request, user)
        
        return Response({
            'valid': True,
            'user_id': user.id,
            'username': user.username
        })
    except jwt.ExpiredSignatureError:
        return Response({'valid': False, 'error': 'Token expired'}, status=401)
    except jwt.InvalidTokenError:
        return Response({'valid': False, 'error': 'Invalid token'}, status=401)
```

#### **3. Frontend Token Handling**

```javascript
// Store token from external auth
localStorage.setItem('auth_token', token);

// Verify token on page load
async function verifyAuth() {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    const response = await fetch('/api/auth/verify/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
    });
    
    const data = await response.json();
    
    if (!data.valid) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', verifyAuth);
```

---

## ⚠️ Error Handling

### **Error Response Format**

```json
{
    "success": false,
    "error": "Error message here",
    "details": "Additional error details"
}
```

### **Common HTTP Status Codes**

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | CSRF token missing/invalid |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |

### **Error Handling Example**

```javascript
async function handleApiCall(url, options) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Operation failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        alert(`Error: ${error.message}`);
        return null;
    }
}

// Usage
const result = await handleApiCall('/task/add/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(taskData)
});

if (result) {
    console.log('Success:', result);
}
```

---

## 📚 Data Models

### **Task Model**

```json
{
    "id": 1,
    "user": 1,
    "title": "Task title",
    "description": "Task description",
    "category": 2,
    "priority": "high",        // "high", "medium", "low"
    "status": "in_progress",   // "not_started", "in_progress", "completed"
    "due_date": "2025-11-20T15:30:00",
    "created_at": "2025-11-15T10:00:00",
    "updated_at": "2025-11-15T14:30:00"
}
```

### **Category Model**

```json
{
    "id": 1,
    "user": 1,
    "name": "Work",
    "color": "#2e86de",
    "created_at": "2025-11-15T10:00:00"
}
```

---

## 🔧 CSRF Token Helper

### **Get CSRF Token Function**

```javascript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

---

## 🧪 Testing API Endpoints

### **Using cURL**

```bash
# Create task
curl -X POST http://127.0.0.1:8000/task/add/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "title": "Test Task",
    "description": "Testing API",
    "priority": "high",
    "status": "not_started"
  }'

# Update task
curl -X POST http://127.0.0.1:8000/task/update/1/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -d '{
    "title": "Updated Task",
    "status": "completed"
  }'

# Delete task
curl -X POST http://127.0.0.1:8000/task/delete/1/ \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN"
```

### **Using Postman**

1. Set request method (POST)
2. Set URL (e.g., `http://127.0.0.1:8000/task/add/`)
3. Add headers:
   - `Content-Type: application/json`
   - `X-CSRFToken: YOUR_CSRF_TOKEN`
4. Add JSON body
5. Send request

---

## 📖 Additional Resources

- **Django REST Framework**: For building full REST APIs
- **JWT Authentication**: For token-based auth
- **Django CORS Headers**: For cross-origin requests

---

<div align="center">
  <p>🔌 For more information, see <a href="README.md">README</a> and <a href="SECURITY.md">SECURITY</a></p>
</div>
