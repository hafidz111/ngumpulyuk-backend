# NgumpulYuk - ERD Visual Diagram

## Entity Relationship Diagram (Visual)

```mermaid
erDiagram
    %% Core Entities
    USERS ||--o{ EVENTS : creates
    USERS ||--o{ COMMUNITIES : creates
    USERS ||--o{ THREADS : creates
    USERS ||--o{ COMMENTS : writes
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ ACTIVITY_HISTORY : has
    USERS ||--|| USER_PREFERENCES : has
    USERS ||--o{ USER_INTERESTS : has

    %% Many-to-Many through junction tables
    USERS ||--o{ EVENT_PARTICIPANTS : "joins via"
    EVENTS ||--o{ EVENT_PARTICIPANTS : "has via"

    USERS ||--o{ COMMUNITY_MEMBERS : "joins via"
    COMMUNITIES ||--o{ COMMUNITY_MEMBERS : "has via"

    %% Event related
    EVENTS ||--o{ EVENT_TAGS : has
    EVENTS ||--o{ AI_RECOMMENDATIONS : "featured in"
    USERS ||--o{ AI_RECOMMENDATIONS : receives

    %% Community related
    COMMUNITIES ||--o{ THREADS : contains
    THREADS ||--o{ COMMENTS : has

    %% Likes (polymorphic)
    USERS ||--o{ LIKES : gives
    THREADS ||--o{ LIKES : receives
    COMMENTS ||--o{ LIKES : receives

    %% Entity Definitions
    USERS {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        string username UK
        string phone
        date date_of_birth
        enum gender
        text bio
        string profile_picture
        string location
        boolean onboarding_completed
        boolean is_verified
        timestamp created_at
        timestamp updated_at
    }

    EVENTS {
        uuid id PK
        uuid creator_id FK
        string title
        text description
        string category
        string cover_image
        date event_date
        time event_time
        string location_area
        text location_address
        decimal latitude
        decimal longitude
        integer max_participants
        integer current_participants
        boolean is_free
        decimal price
        boolean is_competition
        enum difficulty_level
        enum status
        timestamp created_at
        timestamp updated_at
    }

    EVENT_PARTICIPANTS {
        uuid id PK
        uuid event_id FK
        uuid user_id FK
        enum status
        timestamp joined_at
        enum attendance_status
    }

    COMMUNITIES {
        uuid id PK
        string name
        text description
        string category
        string cover_image
        string logo
        uuid creator_id FK
        integer member_count
        boolean is_verified
        timestamp created_at
        timestamp updated_at
    }

    COMMUNITY_MEMBERS {
        uuid id PK
        uuid community_id FK
        uuid user_id FK
        enum role
        timestamp joined_at
    }

    THREADS {
        uuid id PK
        uuid community_id FK
        uuid author_id FK
        string title
        text content
        json images
        integer like_count
        integer comment_count
        boolean is_pinned
        timestamp created_at
        timestamp updated_at
    }

    COMMENTS {
        uuid id PK
        uuid thread_id FK
        uuid author_id FK
        text content
        integer like_count
        timestamp created_at
        timestamp updated_at
    }

    LIKES {
        uuid id PK
        uuid user_id FK
        enum likeable_type
        uuid likeable_id
        timestamp created_at
    }

    USER_INTERESTS {
        uuid id PK
        uuid user_id FK
        string interest_name
        timestamp created_at
    }

    EVENT_TAGS {
        uuid id PK
        uuid event_id FK
        string tag_name
        timestamp created_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        enum type
        string title
        text message
        string link_url
        uuid related_id
        boolean is_read
        timestamp created_at
    }

    ACTIVITY_HISTORY {
        uuid id PK
        uuid user_id FK
        enum activity_type
        text description
        string related_type
        uuid related_id
        timestamp created_at
    }

    USER_PREFERENCES {
        uuid id PK
        uuid user_id FK
        json preferred_days
        enum preferred_time
        string preferred_location
        boolean notification_enabled
        boolean email_notification
        boolean push_notification
        timestamp created_at
        timestamp updated_at
    }

    AI_RECOMMENDATIONS {
        uuid id PK
        uuid user_id FK
        uuid event_id FK
        decimal score
        text reason
        timestamp created_at
        timestamp expires_at
    }
```

---

## Simplified ERD (Core Relationships)

```mermaid
erDiagram
    USERS ||--o{ EVENTS : "1:N - creates"
    USERS }o--o{ EVENTS : "M:N - participates"
    USERS ||--o{ COMMUNITIES : "1:N - creates"
    USERS }o--o{ COMMUNITIES : "M:N - member of"
    COMMUNITIES ||--o{ THREADS : "1:N - contains"
    THREADS ||--o{ COMMENTS : "1:N - has"
    USERS ||--o{ THREADS : "1:N - posts"
    USERS ||--o{ COMMENTS : "1:N - writes"
    USERS ||--|| USER_PREFERENCES : "1:1 - has"
    USERS ||--o{ NOTIFICATIONS : "1:N - receives"
```

---

## Database Relationship Types Summary

### One-to-Many (1:N)

- 1 User → Many Events (created)
- 1 User → Many Communities (created)
- 1 User → Many Threads
- 1 User → Many Comments
- 1 User → Many Notifications
- 1 Community → Many Threads
- 1 Thread → Many Comments
- 1 Event → Many Participants
- 1 Event → Many Tags

### Many-to-Many (M:N)

- Users ↔ Events (through EVENT_PARTICIPANTS)
- Users ↔ Communities (through COMMUNITY_MEMBERS)
- Users ↔ Threads/Comments (through LIKES)

### One-to-One (1:1)

- User ↔ User_Preferences

---

## Key Junction Tables

### EVENT_PARTICIPANTS

**Purpose**: Connect users with events they join  
**Key Fields**: event_id, user_id, status, joined_at  
**Composite Unique**: (event_id, user_id)

### COMMUNITY_MEMBERS

**Purpose**: Connect users with communities they join  
**Key Fields**: community_id, user_id, role  
**Composite Unique**: (community_id, user_id)

### LIKES

**Purpose**: Track likes on threads and comments (polymorphic)  
**Key Fields**: user_id, likeable_type, likeable_id  
**Composite Unique**: (user_id, likeable_type, likeable_id)

---

## Database Normalization Level

**Current Design**: 3NF (Third Normal Form)

✅ **1NF**: All attributes contain atomic values  
✅ **2NF**: No partial dependencies  
✅ **3NF**: No transitive dependencies

**Benefits**:

- Eliminates data redundancy
- Ensures data integrity
- Optimized for read/write operations
- Scalable for future features

---

## Cardinality Summary

```
Users (1) ────────── (N) Events
Users (1) ────────── (N) Communities
Users (N) ─┐    ┌─ (N) Events
           └─(M)─┘
         EVENT_PARTICIPANTS

Users (N) ─┐    ┌─ (N) Communities
           └─(M)─┘
       COMMUNITY_MEMBERS

Communities (1) ── (N) Threads
Threads (1) ─────── (N) Comments
Users (1) ────────── (N) Threads
Users (1) ────────── (N) Comments
Users (1) ────────── (1) User_Preferences
```

---

## Implementation Notes

### PostgreSQL Recommended

- Native UUID support
- JSON/JSONB for flexible fields
- Full-text search capabilities
- Strong ACID compliance
- Excellent performance with indexes

### Supabase Integration

All tables can be created in Supabase with:

- Row Level Security (RLS) policies
- Real-time subscriptions
- Auto-generated REST API
- Built-in authentication integration

### Example RLS Policies

```sql
-- Users can only read their own data
CREATE POLICY "Users can view own profile"
ON users FOR SELECT
USING (auth.uid() = id);

-- Users can join public events
CREATE POLICY "Users can join events"
ON event_participants FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Only event creators can update events
CREATE POLICY "Creators can update events"
ON events FOR UPDATE
USING (auth.uid() = creator_id);
```

---

**Diagram Generated**: April 2026  
**For**: NgumpulYuk Platform  
**Database**: PostgreSQL / Supabase
