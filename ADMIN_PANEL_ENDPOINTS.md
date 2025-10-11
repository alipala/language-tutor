# Admin Panel API Endpoints

## Complete List of Endpoints Used by Language Tutor Admin Panel

This document lists all API endpoints that the admin panel (`language-tutor-admin`) calls to the backend.

---

## 🔐 Authentication Endpoints

### 1. Admin Login
- **Endpoint**: `POST /api/admin/login`
- **Purpose**: Authenticate admin users
- **Request Body**:
  ```json
  {
    "email": "admin@example.com",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "jwt_token_here",
    "token_type": "bearer",
    "user": {
      "id": "user_id",
      "name": "Admin Name",
      "email": "admin@example.com",
      "role": "admin",
      "permissions": ["read:users", "write:users", ...]
    }
  }
  ```
- **Used By**: Login page, authService.login()

### 2. Admin Health Check
- **Endpoint**: `GET /api/admin/health`
- **Purpose**: Verify admin API is operational
- **Response**:
  ```json
  {
    "status": "ok",
    "timestamp": "2025-01-10T23:00:00Z"
  }
  ```
- **Used By**: Health monitoring, connection verification

---

## 📊 Dashboard Endpoints

### 3. Dashboard Metrics
- **Endpoint**: `GET /api/admin/dashboard`
- **Purpose**: Fetch dashboard statistics and metrics
- **Query Parameters**: 
  - `t` (timestamp) - cache busting
  - `r` (random) - cache busting
- **Response**:
  ```json
  {
    "total_users": 1250,
    "active_users": 450,
    "verified_users": 1100,
    "total_conversations": 5600,
    "total_assessments": 890,
    "total_learning_plans": 320
  }
  ```
- **Used By**: Dashboard component

---

## 👥 User Management Endpoints

### 4. List Users
- **Endpoint**: `GET /api/admin/users`
- **Purpose**: Get paginated list of users
- **Query Parameters**:
  - `page` - Page number (default: 1)
  - `per_page` - Items per page (default: 25)
  - `sort_field` - Field to sort by (default: 'id')
  - `sort_order` - Sort direction ('asc' or 'desc')
  - Additional filter parameters
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "user_id",
        "email": "user@example.com",
        "name": "User Name",
        "created_at": "2025-01-01T00:00:00Z",
        "subscription_status": "active",
        ...
      }
    ],
    "total": 1250
  }
  ```
- **Used By**: UserList component

### 5. Get Single User
- **Endpoint**: `GET /api/admin/users/{id}`
- **Purpose**: Get detailed information about a specific user
- **Response**:
  ```json
  {
    "data": {
      "id": "user_id",
      "email": "user@example.com",
      "name": "User Name",
      "created_at": "2025-01-01T00:00:00Z",
      "subscription_status": "active",
      "learning_plans": [...],
      "assessments": [...],
      ...
    }
  }
  ```
- **Used By**: UserShow component

### 6. Update User
- **Endpoint**: `PUT /api/admin/users/{id}`
- **Purpose**: Update user information
- **Request Body**:
  ```json
  {
    "name": "Updated Name",
    "email": "updated@example.com",
    "subscription_status": "active",
    ...
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "id": "user_id",
      "name": "Updated Name",
      ...
    }
  }
  ```
- **Used By**: UserEdit component

### 7. Create User
- **Endpoint**: `POST /api/admin/users`
- **Purpose**: Create a new user
- **Request Body**:
  ```json
  {
    "email": "newuser@example.com",
    "name": "New User",
    "password": "password123",
    ...
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "id": "new_user_id",
      "email": "newuser@example.com",
      ...
    }
  }
  ```
- **Used By**: UserCreate component

### 8. Delete User
- **Endpoint**: `DELETE /api/admin/users/{id}`
- **Purpose**: Delete a user
- **Response**:
  ```json
  {
    "data": {
      "id": "deleted_user_id"
    }
  }
  ```
- **Used By**: UserList component (delete action)

---

## 💬 Conversation Management Endpoints

### 9. List Conversations
- **Endpoint**: `GET /api/admin/conversation_sessions`
- **Purpose**: Get paginated list of conversation sessions
- **Query Parameters**: Same as List Users
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "session_id",
        "user_id": "user_id",
        "language": "english",
        "level": "B1",
        "duration": 300,
        "created_at": "2025-01-10T12:00:00Z",
        ...
      }
    ],
    "total": 5600
  }
  ```
- **Used By**: ConversationList component

### 10. Get Single Conversation
- **Endpoint**: `GET /api/admin/conversation_sessions/{id}`
- **Purpose**: Get detailed conversation session information
- **Response**:
  ```json
  {
    "data": {
      "id": "session_id",
      "user_id": "user_id",
      "transcript": "...",
      "analysis": {...},
      ...
    }
  }
  ```
- **Used By**: ConversationShow component

---

## 📈 User Statistics Endpoints

### 11. List User Statistics
- **Endpoint**: `GET /api/admin/user_stats`
- **Purpose**: Get user statistics and analytics
- **Query Parameters**: Same as List Users
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "stat_id",
        "user_id": "user_id",
        "total_sessions": 45,
        "total_minutes": 2250,
        "average_score": 85.5,
        ...
      }
    ],
    "total": 1250
  }
  ```
- **Used By**: UserStatsList component

---

## 🏆 Badge System Endpoints

### 12. List Badges
- **Endpoint**: `GET /api/admin/badges`
- **Purpose**: Get badge system data
- **Query Parameters**: Same as List Users
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "badge_id",
        "user_id": "user_id",
        "badge_type": "streak_7_days",
        "earned_at": "2025-01-10T00:00:00Z",
        ...
      }
    ],
    "total": 450
  }
  ```
- **Used By**: BadgesList component

---

## 📝 Assessment History Endpoints

### 13. List Assessment History
- **Endpoint**: `GET /api/admin/assessment_history`
- **Purpose**: Get assessment records
- **Query Parameters**: Same as List Users
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "assessment_id",
        "user_id": "user_id",
        "language": "english",
        "overall_score": 85,
        "pronunciation": 88,
        "grammar": 82,
        "created_at": "2025-01-10T12:00:00Z",
        ...
      }
    ],
    "total": 890
  }
  ```
- **Used By**: AssessmentHistoryList component

---

## 📚 Learning Plans Endpoints

### 14. List Learning Plans
- **Endpoint**: `GET /api/admin/learning_plans`
- **Purpose**: Get learning plan records
- **Query Parameters**: Same as List Users
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "plan_id",
        "user_id": "user_id",
        "language": "english",
        "proficiency_level": "B1",
        "completed_sessions": 5,
        "total_sessions": 48,
        "progress_percentage": 10.4,
        ...
      }
    ],
    "total": 320
  }
  ```
- **Used By**: LearningPlansList component

---

## 🔔 Notification Endpoints

### 15. List Notifications
- **Endpoint**: `GET /api/admin/notifications`
- **Purpose**: Get notification records
- **Query Parameters**: Same as List Users
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "notification_id",
        "title": "System Update",
        "message": "New features available",
        "type": "info",
        "created_at": "2025-01-10T12:00:00Z",
        ...
      }
    ],
    "total": 150
  }
  ```
- **Used By**: NotificationList component

### 16. Get Single Notification
- **Endpoint**: `GET /api/admin/notifications/{id}`
- **Purpose**: Get detailed notification information
- **Response**:
  ```json
  {
    "data": {
      "id": "notification_id",
      "title": "System Update",
      "message": "New features available",
      "recipients": [...],
      ...
    }
  }
  ```
- **Used By**: NotificationShow component

### 17. Create Notification
- **Endpoint**: `POST /api/admin/notifications`
- **Purpose**: Create and send a new notification
- **Request Body**:
  ```json
  {
    "title": "New Notification",
    "message": "Notification content",
    "type": "info",
    "target_users": ["user_id_1", "user_id_2"],
    ...
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "id": "new_notification_id",
      "title": "New Notification",
      ...
    }
  }
  ```
- **Used By**: NotificationCreate component

---

## 🎁 Promotion Endpoints

### 18. List Promotions
- **Endpoint**: `GET /api/admin/promotions`
- **Purpose**: Get promotional campaign records
- **Query Parameters**: Same as List Users
- **Response**:
  ```json
  {
    "data": [
      {
        "id": "promo_id",
        "code": "NEWYEAR2025",
        "discount_percentage": 20,
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_until": "2025-01-31T23:59:59Z",
        "active": true,
        ...
      }
    ],
    "total": 25
  }
  ```
- **Used By**: PromotionList component

### 19. Get Single Promotion
- **Endpoint**: `GET /api/admin/promotions/{id}`
- **Purpose**: Get detailed promotion information
- **Response**:
  ```json
  {
    "data": {
      "id": "promo_id",
      "code": "NEWYEAR2025",
      "usage_count": 45,
      ...
    }
  }
  ```
- **Used By**: PromotionShow component

### 20. Create Promotion
- **Endpoint**: `POST /api/admin/promotions`
- **Purpose**: Create a new promotional campaign
- **Request Body**:
  ```json
  {
    "code": "SPRING2025",
    "discount_percentage": 15,
    "valid_from": "2025-03-01T00:00:00Z",
    "valid_until": "2025-03-31T23:59:59Z",
    "max_uses": 100,
    ...
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "id": "new_promo_id",
      "code": "SPRING2025",
      ...
    }
  }
  ```
- **Used By**: PromotionCreate component

### 21. Update Promotion
- **Endpoint**: `PUT /api/admin/promotions/{id}`
- **Purpose**: Update promotion details
- **Request Body**:
  ```json
  {
    "discount_percentage": 25,
    "active": false,
    ...
  }
  ```
- **Response**:
  ```json
  {
    "data": {
      "id": "promo_id",
      "discount_percentage": 25,
      ...
    }
  }
  ```
- **Used By**: PromotionEdit component

---

## 🔄 Generic CRUD Operations

The admin panel uses a generic data provider that automatically constructs endpoints for all resources following this pattern:

### Standard Resource Endpoints Pattern:
- **List**: `GET /api/admin/{resource}`
- **Get One**: `GET /api/admin/{resource}/{id}`
- **Create**: `POST /api/admin/{resource}`
- **Update**: `PUT /api/admin/{resource}/{id}`
- **Delete**: `DELETE /api/admin/{resource}/{id}`

Where `{resource}` can be:
- `users`
- `conversation_sessions`
- `user_stats`
- `badges`
- `assessment_history`
- `learning_plans`
- `notifications`
- `promotions`

---

## 📋 Query Parameters (Common Across List Endpoints)

All list endpoints support these query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number for pagination |
| `per_page` | integer | 25 | Number of items per page |
| `sort_field` | string | 'id' | Field to sort by |
| `sort_order` | string | 'asc' | Sort direction ('asc' or 'desc') |
| Additional filters | various | - | Resource-specific filter parameters |

---

## 🔒 Authentication

All admin endpoints (except `/api/admin/login`) require authentication:

**Header Required**:
```
Authorization: Bearer {jwt_token}
```

The JWT token is obtained from the login endpoint and stored in localStorage under the key `admin_token`.

---

## 📊 Response Format

All endpoints follow a consistent response format:

### Success Response:
```json
{
  "data": {...} or [...],
  "total": 100,  // For list endpoints
  "message": "Success message"  // Optional
}
```

### Error Response:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

## 🎯 Summary

**Total Endpoints Used**: 21+ (including generic CRUD operations)

**Endpoint Categories**:
- Authentication: 2 endpoints
- Dashboard: 1 endpoint
- User Management: 5 endpoints
- Conversations: 2 endpoints
- User Statistics: 1 endpoint
- Badges: 1 endpoint
- Assessment History: 1 endpoint
- Learning Plans: 1 endpoint
- Notifications: 3 endpoints
- Promotions: 4 endpoints

**Base URL**: Configured via `VITE_API_URL` environment variable
- Development: `http://localhost:8000`
- Production: `https://mytacoai.com`

---

**Last Updated**: January 10, 2025
**Admin Panel Version**: 3.1.1
