# NgumpulYuk - API Documentation

---

## Authentication

All authenticated endpoints require a Bearer token in the header:

```
Authorization: Bearer {access_token}
```

---

## 📋 Table of Contents

1. [Authentication](#authentication-endpoints)
2. [Users](#users-endpoints)
3. [Events](#events-endpoints)
4. [Communities](#communities-endpoints)
5. [Threads & Comments](#threads--comments-endpoints)
6. [Notifications](#notifications-endpoints)
7. [AI Recommendations](#ai-recommendations-endpoints)

---

## Authentication Endpoints

### POST /auth/register

Register a new user account

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "full_name": "John Doe",
  "username": "johndoe"
}
```

**Response (201):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "username": "johndoe",
      "full_name": "John Doe",
      "onboarding_completed": false
    },
    "access_token": "jwt_token",
    "refresh_token": "refresh_token"
  }
}
```

---

### POST /auth/login

Login existing user

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "username": "johndoe",
      "onboarding_completed": true
    },
    "access_token": "jwt_token",
    "refresh_token": "refresh_token"
  }
}
```

---

### POST /auth/refresh

Refresh access token

**Request Body:**

```json
{
  "refresh_token": "refresh_token"
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "access_token": "new_jwt_token"
  }
}
```

---

### POST /auth/logout

Logout user (invalidate tokens)

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## Users Endpoints

### GET /users/me

Get current user profile

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe",
    "phone": "+62812345678",
    "date_of_birth": "1998-05-15",
    "gender": "male",
    "bio": "Love board games!",
    "profile_picture": "https://...",
    "location": "Jakarta Selatan",
    "onboarding_completed": true,
    "is_verified": true,
    "created_at": "2026-01-01T00:00:00Z",
    "stats": {
      "events_joined": 12,
      "events_created": 3,
      "communities_joined": 5
    }
  }
}
```

---

### PUT /users/me

Update current user profile

**Headers:** `Authorization: Bearer {token}`

**Request Body:**

```json
{
  "full_name": "John Doe Updated",
  "bio": "New bio text",
  "phone": "+62812345678",
  "location": "Jakarta Pusat"
}
```

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "full_name": "John Doe Updated",
    "bio": "New bio text",
    ...
  }
}
```

---

### POST /users/onboarding

Complete user onboarding

**Headers:** `Authorization: Bearer {token}`

**Request Body:**

```json
{
    "personal_data": {
  "date_of_birth": "1998-05-15",
  "gender": "male"
    }
  "interests": ["Olahraga", "Board Game", "Esports"],
  "preferences": {
    "preferred_days": ["Sabtu", "Minggu"],
    "preferred_time": "evening",
    "preferred_location": "Jakarta Selatan"
  }
}
```

**Response (200):**

```json
{
  "success": true,
  "message": "Onboarding completed",
  "data": {
    "onboarding_completed": true
  }
}
```

---

### GET /users/:username

Get user profile by username

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "johndoe",
    "full_name": "John Doe",
    "bio": "Love board games!",
    "profile_picture": "https://...",
    "location": "Jakarta Selatan",
    "created_at": "2026-01-01T00:00:00Z",
    "stats": {
      "events_joined": 12,
      "events_created": 3,
      "communities_joined": 5
    }
  }
}
```

---

### GET /users/me/activity-history

Get current user's activity history

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**

- `limit` (optional, default: 20)
- `offset` (optional, default: 0)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "id": "uuid",
        "activity_type": "joined_event",
        "description": "Joined event: Morning Run Sudirman",
        "related_type": "event",
        "related_id": "uuid",
        "created_at": "2026-04-01T10:00:00Z"
      }
    ],
    "total": 45,
    "limit": 20,
    "offset": 0
  }
}
```

---

## Events Endpoints

### GET /events

Get list of events

**Query Parameters:**

- `category` (optional): Filter by category
- `location` (optional): Filter by location area
- `status` (optional): upcoming/ongoing/completed
- `search` (optional): Search query
- `date_from` (optional): YYYY-MM-DD
- `date_to` (optional): YYYY-MM-DD
- `limit` (optional, default: 20)
- `offset` (optional, default: 0)
- `sort` (optional): date_asc/date_desc/popular/newest

**Response (200):**

```json
{
  "success": true,
  "data": {
    "events": [
      {
        "id": "uuid",
        "title": "Morning Run Sudirman",
        "description": "...",
        "category": "Olahraga",
        "cover_image": "https://...",
        "event_date": "2026-04-05",
        "event_time": "06:00:00",
        "location_area": "Jakarta Pusat",
        "location_address": "Gelora Bung Karno",
        "max_participants": 50,
        "current_participants": 23,
        "status": "upcoming",
        "creator": {
          "id": "uuid",
          "username": "aldi",
          "full_name": "Aldi Pratama",
          "profile_picture": "https://..."
        },
        "tags": ["morning", "fitness", "beginner-friendly"],
        "created_at": "2026-03-20T00:00:00Z"
      }
    ],
    "total": 48,
    "limit": 20,
    "offset": 0
  }
}
```

---

### GET /events/:id

Get event details

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Morning Run Sudirman",
    "description": "Full description...",
    "category": "Olahraga",
    "cover_image": "https://...",
    "event_date": "2026-04-05",
    "event_time": "06:00:00",
    "location_area": "Jakarta Pusat",
    "location_address": "Gelora Bung Karno, Gate 1",
    "latitude": -6.2182,
    "longitude": 106.8019,
    "max_participants": 50,
    "current_participants": 23,
    "is_competition": false,
    "difficulty_level": "beginner",
    "status": "upcoming",
    "creator": {
      "id": "uuid",
      "username": "aldi",
      "full_name": "Aldi Pratama",
      "profile_picture": "https://...",
      "bio": "..."
    },
    "tags": ["morning", "fitness", "beginner-friendly"],
    "participants": [
      {
        "id": "uuid",
        "username": "sarah",
        "full_name": "Sarah Wijaya",
        "profile_picture": "https://..."
      }
    ],
    "is_joined": false,
    "created_at": "2026-03-20T00:00:00Z",
    "updated_at": "2026-03-20T00:00:00Z"
  }
}
```

---

### POST /events

Create new event

**Headers:** `Authorization: Bearer {token}`

**Request Body:**

```json
{
  "title": "Morning Run Sudirman",
  "description": "Join us for a morning run...",
  "category": "Olahraga",
  "cover_image": "https://...",
  "event_date": "2026-04-05",
  "event_time": "06:00",
  "location_area": "Jakarta Pusat",
  "location_address": "Gelora Bung Karno, Gate 1",
  "latitude": -6.2182,
  "longitude": 106.8019,
  "max_participants": 50,
  "is_competition": false,
  "difficulty_level": "beginner",
  "tags": ["morning", "fitness", "beginner-friendly"]
}
```

**Response (201):**

```json
{
  "success": true,
  "message": "Event created successfully",
  "data": {
    "id": "uuid",
    "title": "Morning Run Sudirman",
    ...
  }
}
```

---

### PUT /events/:id

Update event (creator only)

**Headers:** `Authorization: Bearer {token}`

**Request Body:** Same as POST /events

**Response (200):**

```json
{
  "success": true,
  "message": "Event updated successfully",
  "data": { ... }
}
```

---

### DELETE /events/:id

Delete event (creator only)

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Event deleted successfully"
}
```

---

### POST /events/:id/join

Join an event

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Successfully joined event",
  "data": {
    "event_id": "uuid",
    "user_id": "uuid",
    "status": "confirmed",
    "joined_at": "2026-04-01T10:00:00Z"
  }
}
```

**Error (400) - Event Full:**

```json
{
  "success": false,
  "error": {
    "code": "EVENT_FULL",
    "message": "Event has reached maximum participants"
  }
}
```

---

### DELETE /events/:id/leave

Leave an event

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Successfully left event"
}
```

---

### GET /events/:id/participants

Get event participants list

**Query Parameters:**

- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "participants": [
      {
        "user_id": "uuid",
        "username": "aldi",
        "full_name": "Aldi Pratama",
        "profile_picture": "https://...",
        "status": "confirmed",
        "joined_at": "2026-03-25T10:00:00Z"
      }
    ],
    "total": 23,
    "limit": 50,
    "offset": 0
  }
}
```

---

## Communities Endpoints

### GET /communities

Get list of communities

**Query Parameters:**

- `category` (optional)
- `search` (optional)
- `verified` (optional): true/false
- `limit` (optional, default: 20)
- `offset` (optional, default: 0)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "communities": [
      {
        "id": "uuid",
        "name": "Jakarta Runners",
        "description": "Komunitas lari Jakarta",
        "category": "Olahraga",
        "cover_image": "https://...",
        "logo": "https://...",
        "member_count": 234,
        "is_verified": true,
        "creator": {
          "id": "uuid",
          "username": "aldi"
        },
        "is_member": false,
        "created_at": "2026-01-01T00:00:00Z"
      }
    ],
    "total": 45,
    "limit": 20,
    "offset": 0
  }
}
```

---

### GET /communities/:id

Get community details

**Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Jakarta Runners",
    "description": "Komunitas lari Jakarta...",
    "category": "Olahraga",
    "cover_image": "https://...",
    "logo": "https://...",
    "member_count": 234,
    "is_verified": true,
    "creator": {
      "id": "uuid",
      "username": "aldi",
      "full_name": "Aldi Pratama"
    },
    "is_member": false,
    "user_role": null,
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

---

### POST /communities

Create new community

**Headers:** `Authorization: Bearer {token}`

**Request Body:**

```json
{
  "name": "Jakarta Runners",
  "description": "Komunitas lari Jakarta",
  "category": "Olahraga",
  "cover_image": "https://...",
  "logo": "https://..."
}
```

**Response (201):**

```json
{
  "success": true,
  "message": "Community created successfully",
  "data": { ... }
}
```

---

### POST /communities/:id/join

Join a community

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Successfully joined community"
}
```

---

### DELETE /communities/:id/leave

Leave a community

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Successfully left community"
}
```

---

### GET /communities/:id/members

Get community members

**Query Parameters:**

- `role` (optional): admin/moderator/member
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "members": [
      {
        "user_id": "uuid",
        "username": "aldi",
        "full_name": "Aldi Pratama",
        "profile_picture": "https://...",
        "role": "admin",
        "joined_at": "2026-01-01T00:00:00Z"
      }
    ],
    "total": 234,
    "limit": 50,
    "offset": 0
  }
}
```

---

## Threads & Comments Endpoints

### GET /communities/:id/threads

Get community threads

**Query Parameters:**

- `limit` (optional, default: 20)
- `offset` (optional, default: 0)
- `sort` (optional): latest/popular

**Response (200):**

```json
{
  "success": true,
  "data": {
    "threads": [
      {
        "id": "uuid",
        "community_id": "uuid",
        "title": "Weekly meetup update",
        "content": "Hey everyone...",
        "images": ["https://...", "https://..."],
        "like_count": 15,
        "comment_count": 8,
        "is_pinned": false,
        "author": {
          "id": "uuid",
          "username": "aldi",
          "full_name": "Aldi Pratama",
          "profile_picture": "https://..."
        },
        "is_liked": false,
        "created_at": "2026-04-01T10:00:00Z"
      }
    ],
    "total": 89,
    "limit": 20,
    "offset": 0
  }
}
```

---

### POST /communities/:id/threads

Create thread in community

**Headers:** `Authorization: Bearer {token}`

**Request Body:**

```json
{
  "title": "Weekly meetup update",
  "content": "Hey everyone, here's the update...",
  "images": ["https://...", "https://..."]
}
```

**Response (201):**

```json
{
  "success": true,
  "message": "Thread created successfully",
  "data": { ... }
}
```

---

### GET /threads/:id/comments

Get thread comments

**Query Parameters:**

- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "comments": [
      {
        "id": "uuid",
        "thread_id": "uuid",
        "content": "Great idea!",
        "like_count": 3,
        "author": {
          "id": "uuid",
          "username": "sarah",
          "full_name": "Sarah Wijaya",
          "profile_picture": "https://..."
        },
        "is_liked": false,
        "created_at": "2026-04-01T11:00:00Z"
      }
    ],
    "total": 8,
    "limit": 50,
    "offset": 0
  }
}
```

---

### POST /threads/:id/comments

Add comment to thread

**Headers:** `Authorization: Bearer {token}`

**Request Body:**

```json
{
  "content": "Great idea! Count me in!"
}
```

**Response (201):**

```json
{
  "success": true,
  "message": "Comment added successfully",
  "data": { ... }
}
```

---

### POST /threads/:id/like

Like a thread

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Thread liked"
}
```

---

### DELETE /threads/:id/like

Unlike a thread

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Thread unliked"
}
```

---

### POST /comments/:id/like

Like a comment

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Comment liked"
}
```

---

## Notifications Endpoints

### GET /notifications

Get user notifications

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**

- `is_read` (optional): true/false
- `type` (optional): event_reminder/new_event/etc
- `limit` (optional, default: 20)
- `offset` (optional, default: 0)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "uuid",
        "type": "event_reminder",
        "title": "Event Tomorrow!",
        "message": "Morning Run Sudirman starts tomorrow at 06:00",
        "link_url": "/event/uuid",
        "related_id": "uuid",
        "is_read": false,
        "created_at": "2026-04-01T10:00:00Z"
      }
    ],
    "unread_count": 5,
    "total": 45,
    "limit": 20,
    "offset": 0
  }
}
```

---

### PUT /notifications/:id/read

Mark notification as read

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

---

### PUT /notifications/read-all

Mark all notifications as read

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "All notifications marked as read"
}
```

---

## AI Recommendations Endpoints

### GET /recommendations/events

Get AI-recommended events

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**

- `limit` (optional, default: 10)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "event": {
          "id": "uuid",
          "title": "Morning Run Sudirman",
          ...
        },
        "score": 95.5,
        "reason": "Matches your interest in Olahraga and preferred time"
      }
    ]
  }
}
```

---

### POST /recommendations/refresh

Force refresh AI recommendations

**Headers:** `Authorization: Bearer {token}`

**Response (200):**

```json
{
  "success": true,
  "message": "Recommendations refreshed",
  "data": {
    "count": 10
  }
}
```

---

## Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

### Common Error Codes:

- `UNAUTHORIZED` (401): Invalid or missing token
- `FORBIDDEN` (403): No permission
- `NOT_FOUND` (404): Resource not found
- `VALIDATION_ERROR` (422): Invalid input
- `EVENT_FULL` (400): Event capacity reached
- `ALREADY_JOINED` (400): User already joined
- `INTERNAL_ERROR` (500): Server error

---

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Authenticated**: 500 requests per minute per user
- **Headers**:
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

---

## Pagination

All list endpoints support pagination with:

- `limit`: Number of items (max: 100)
- `offset`: Skip N items

Response includes:

```json
{
  "data": [...],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

---

**API Version**: v1.0  
**Last Updated**: April 2026  
**For**: NgumpulYuk Platform
