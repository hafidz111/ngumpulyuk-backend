# NgumpulYuk - Entity Relationship Diagram (ERD)

## Database Schema Design

---

## 📋 Entities & Attributes

### 1. **Users**

Menyimpan data pengguna platform

| Field                  | Type         | Constraint       | Description                           |
| ---------------------- | ------------ | ---------------- | ------------------------------------- |
| `id`                   | UUID         | PRIMARY KEY      | User ID                               |
| `email`                | VARCHAR(255) | UNIQUE, NOT NULL | Email pengguna                        |
| `password_hash`        | VARCHAR(255) | NOT NULL         | Password (hashed)                     |
| `full_name`            | VARCHAR(100) | NOT NULL         | Nama lengkap                          |
| `username`             | VARCHAR(50)  | UNIQUE, NOT NULL | Username unik                         |
| `phone`                | VARCHAR(20)  | NULLABLE         | Nomor telepon                         |
| `date_of_birth`        | DATE         | NOT NULL         | Tanggal lahir                         |
| `gender`               | ENUM         | NOT NULL         | 'male', 'female', 'other'             |
| `bio`                  | TEXT         | NULLABLE         | Bio pengguna                          |
| `profile_picture`      | VARCHAR(255) | NULLABLE         | URL foto profil                       |
| `location`             | VARCHAR(100) | NULLABLE         | Lokasi default (Jakarta Selatan, dll) |
| `onboarding_completed` | BOOLEAN      | DEFAULT FALSE    | Status onboarding                     |
| `is_verified`          | BOOLEAN      | DEFAULT FALSE    | Status verifikasi email               |
| `created_at`           | TIMESTAMP    | DEFAULT NOW()    | Waktu registrasi                      |
| `updated_at`           | TIMESTAMP    | DEFAULT NOW()    | Waktu update terakhir                 |

---

### 2. **Events**

Menyimpan data event/kegiatan

| Field                  | Type          | Constraint              | Description                                     |
| ---------------------- | ------------- | ----------------------- | ----------------------------------------------- |
| `id`                   | UUID          | PRIMARY KEY             | Event ID                                        |
| `creator_id`           | UUID          | FOREIGN KEY → Users(id) | Pembuat event                                   |
| `title`                | VARCHAR(200)  | NOT NULL                | Judul event                                     |
| `description`          | TEXT          | NOT NULL                | Deskripsi event                                 |
| `category`             | VARCHAR(50)   | NOT NULL                | Kategori (Olahraga, Board Game, dll)            |
| `cover_image`          | VARCHAR(255)  | NULLABLE                | URL cover image                                 |
| `event_date`           | DATE          | NOT NULL                | Tanggal event                                   |
| `event_time`           | TIME          | NOT NULL                | Waktu event                                     |
| `location_area`        | VARCHAR(100)  | NOT NULL                | Area (Jakarta Selatan, dll)                     |
| `location_address`     | TEXT          | NOT NULL                | Alamat lengkap                                  |
| `latitude`             | DECIMAL(10,8) | NULLABLE                | Koordinat latitude                              |
| `longitude`            | DECIMAL(11,8) | NULLABLE                | Koordinat longitude                             |
| `max_participants`     | INTEGER       | NOT NULL                | Maksimal peserta                                |
| `current_participants` | INTEGER       | DEFAULT 0               | Jumlah peserta saat ini                         |
| `is_free`              | BOOLEAN       | DEFAULT TRUE            | Event gratis/berbayar                           |
| `price`                | DECIMAL(10,2) | NULLABLE                | Harga jika berbayar                             |
| `is_competition`       | BOOLEAN       | DEFAULT FALSE           | Event kompetisi                                 |
| `difficulty_level`     | ENUM          | NULLABLE                | 'beginner', 'intermediate', 'advanced'          |
| `status`               | ENUM          | DEFAULT 'upcoming'      | 'upcoming', 'ongoing', 'completed', 'cancelled' |
| `created_at`           | TIMESTAMP     | DEFAULT NOW()           | Waktu dibuat                                    |
| `updated_at`           | TIMESTAMP     | DEFAULT NOW()           | Waktu update                                    |

---

### 3. **Event_Participants**

Relasi many-to-many antara Users dan Events

| Field               | Type      | Constraint               | Description                                     |
| ------------------- | --------- | ------------------------ | ----------------------------------------------- |
| `id`                | UUID      | PRIMARY KEY              | Participant record ID                           |
| `event_id`          | UUID      | FOREIGN KEY → Events(id) | Event yang diikuti                              |
| `user_id`           | UUID      | FOREIGN KEY → Users(id)  | User yang join                                  |
| `status`            | ENUM      | DEFAULT 'confirmed'      | 'confirmed', 'waitlist', 'cancelled'            |
| `joined_at`         | TIMESTAMP | DEFAULT NOW()            | Waktu join                                      |
| `attendance_status` | ENUM      | NULLABLE                 | 'attended', 'no_show', null (belum berlangsung) |

**Composite Unique Key**: (event_id, user_id)

---

### 4. **Communities**

Menyimpan data komunitas

| Field          | Type         | Constraint              | Description             |
| -------------- | ------------ | ----------------------- | ----------------------- |
| `id`           | UUID         | PRIMARY KEY             | Community ID            |
| `name`         | VARCHAR(100) | NOT NULL                | Nama komunitas          |
| `description`  | TEXT         | NOT NULL                | Deskripsi komunitas     |
| `category`     | VARCHAR(50)  | NOT NULL                | Kategori komunitas      |
| `cover_image`  | VARCHAR(255) | NULLABLE                | Cover image komunitas   |
| `logo`         | VARCHAR(255) | NULLABLE                | Logo komunitas          |
| `creator_id`   | UUID         | FOREIGN KEY → Users(id) | Pembuat komunitas       |
| `member_count` | INTEGER      | DEFAULT 0               | Jumlah anggota          |
| `is_verified`  | BOOLEAN      | DEFAULT FALSE           | Komunitas terverifikasi |
| `created_at`   | TIMESTAMP    | DEFAULT NOW()           | Waktu dibuat            |
| `updated_at`   | TIMESTAMP    | DEFAULT NOW()           | Waktu update            |

---

### 5. **Community_Members**

Relasi many-to-many antara Users dan Communities

| Field          | Type      | Constraint                    | Description                    |
| -------------- | --------- | ----------------------------- | ------------------------------ |
| `id`           | UUID      | PRIMARY KEY                   | Member record ID               |
| `community_id` | UUID      | FOREIGN KEY → Communities(id) | Community yang diikuti         |
| `user_id`      | UUID      | FOREIGN KEY → Users(id)       | User yang join                 |
| `role`         | ENUM      | DEFAULT 'member'              | 'admin', 'moderator', 'member' |
| `joined_at`    | TIMESTAMP | DEFAULT NOW()                 | Waktu bergabung                |

**Composite Unique Key**: (community_id, user_id)

---

### 6. **Threads**

Post/thread di halaman Community

| Field           | Type         | Constraint                    | Description             |
| --------------- | ------------ | ----------------------------- | ----------------------- |
| `id`            | UUID         | PRIMARY KEY                   | Thread ID               |
| `community_id`  | UUID         | FOREIGN KEY → Communities(id) | Komunitas terkait       |
| `author_id`     | UUID         | FOREIGN KEY → Users(id)       | Pembuat thread          |
| `title`         | VARCHAR(200) | NULLABLE                      | Judul thread (opsional) |
| `content`       | TEXT         | NOT NULL                      | Konten thread           |
| `images`        | JSON         | NULLABLE                      | Array URL gambar        |
| `like_count`    | INTEGER      | DEFAULT 0                     | Jumlah likes            |
| `comment_count` | INTEGER      | DEFAULT 0                     | Jumlah komentar         |
| `is_pinned`     | BOOLEAN      | DEFAULT FALSE                 | Thread di-pin           |
| `created_at`    | TIMESTAMP    | DEFAULT NOW()                 | Waktu dibuat            |
| `updated_at`    | TIMESTAMP    | DEFAULT NOW()                 | Waktu update            |

---

### 7. **Comments**

Komentar pada thread

| Field        | Type      | Constraint                | Description      |
| ------------ | --------- | ------------------------- | ---------------- |
| `id`         | UUID      | PRIMARY KEY               | Comment ID       |
| `thread_id`  | UUID      | FOREIGN KEY → Threads(id) | Thread terkait   |
| `author_id`  | UUID      | FOREIGN KEY → Users(id)   | Pembuat komentar |
| `content`    | TEXT      | NOT NULL                  | Konten komentar  |
| `like_count` | INTEGER   | DEFAULT 0                 | Jumlah likes     |
| `created_at` | TIMESTAMP | DEFAULT NOW()             | Waktu dibuat     |
| `updated_at` | TIMESTAMP | DEFAULT NOW()             | Waktu update     |

---

### 8. **Likes**

Tracking likes untuk threads dan comments

| Field           | Type      | Constraint              | Description            |
| --------------- | --------- | ----------------------- | ---------------------- |
| `id`            | UUID      | PRIMARY KEY             | Like ID                |
| `user_id`       | UUID      | FOREIGN KEY → Users(id) | User yang like         |
| `likeable_type` | ENUM      | NOT NULL                | 'thread', 'comment'    |
| `likeable_id`   | UUID      | NOT NULL                | ID thread atau comment |
| `created_at`    | TIMESTAMP | DEFAULT NOW()           | Waktu like             |

**Composite Unique Key**: (user_id, likeable_type, likeable_id)

---

### 9. **User_Interests**

Minat pengguna (dari onboarding)

| Field           | Type        | Constraint              | Description                            |
| --------------- | ----------- | ----------------------- | -------------------------------------- |
| `id`            | UUID        | PRIMARY KEY             | Interest record ID                     |
| `user_id`       | UUID        | FOREIGN KEY → Users(id) | User terkait                           |
| `interest_name` | VARCHAR(50) | NOT NULL                | Nama minat (Olahraga, Board Game, dll) |
| `created_at`    | TIMESTAMP   | DEFAULT NOW()           | Waktu ditambahkan                      |

**Composite Unique Key**: (user_id, interest_name)

---

### 10. **Event_Tags**

Tag untuk event

| Field        | Type        | Constraint               | Description       |
| ------------ | ----------- | ------------------------ | ----------------- |
| `id`         | UUID        | PRIMARY KEY              | Tag record ID     |
| `event_id`   | UUID        | FOREIGN KEY → Events(id) | Event terkait     |
| `tag_name`   | VARCHAR(50) | NOT NULL                 | Nama tag          |
| `created_at` | TIMESTAMP   | DEFAULT NOW()            | Waktu ditambahkan |

---

### 11. **Notifications**

Notifikasi pengguna

| Field        | Type         | Constraint              | Description                                                                      |
| ------------ | ------------ | ----------------------- | -------------------------------------------------------------------------------- |
| `id`         | UUID         | PRIMARY KEY             | Notification ID                                                                  |
| `user_id`    | UUID         | FOREIGN KEY → Users(id) | Penerima notifikasi                                                              |
| `type`       | ENUM         | NOT NULL                | 'event_reminder', 'new_event', 'event_update', 'community_post', 'comment_reply' |
| `title`      | VARCHAR(200) | NOT NULL                | Judul notifikasi                                                                 |
| `message`    | TEXT         | NOT NULL                | Pesan notifikasi                                                                 |
| `link_url`   | VARCHAR(255) | NULLABLE                | URL tujuan                                                                       |
| `related_id` | UUID         | NULLABLE                | ID event/thread/comment terkait                                                  |
| `is_read`    | BOOLEAN      | DEFAULT FALSE           | Status baca                                                                      |
| `created_at` | TIMESTAMP    | DEFAULT NOW()           | Waktu dibuat                                                                     |

---

### 12. **Activity_History**

Riwayat aktivitas pengguna

| Field           | Type        | Constraint              | Description                                                                       |
| --------------- | ----------- | ----------------------- | --------------------------------------------------------------------------------- |
| `id`            | UUID        | PRIMARY KEY             | Activity ID                                                                       |
| `user_id`       | UUID        | FOREIGN KEY → Users(id) | User terkait                                                                      |
| `activity_type` | ENUM        | NOT NULL                | 'joined_event', 'created_event', 'joined_community', 'posted_thread', 'commented' |
| `description`   | TEXT        | NOT NULL                | Deskripsi aktivitas                                                               |
| `related_type`  | VARCHAR(50) | NULLABLE                | 'event', 'community', 'thread'                                                    |
| `related_id`    | UUID        | NULLABLE                | ID objek terkait                                                                  |
| `created_at`    | TIMESTAMP   | DEFAULT NOW()           | Waktu aktivitas                                                                   |

---

### 13. **User_Preferences**

Preferensi pengguna (dari onboarding)

| Field                  | Type         | Constraint              | Description                                |
| ---------------------- | ------------ | ----------------------- | ------------------------------------------ |
| `id`                   | UUID         | PRIMARY KEY             | Preference ID                              |
| `user_id`              | UUID         | FOREIGN KEY → Users(id) | User terkait                               |
| `preferred_days`       | JSON         | NULLABLE                | Array hari preferensi ['Sabtu', 'Minggu']  |
| `preferred_time`       | ENUM         | NULLABLE                | 'morning', 'afternoon', 'evening', 'night' |
| `preferred_location`   | VARCHAR(100) | NULLABLE                | Lokasi preferensi                          |
| `notification_enabled` | BOOLEAN      | DEFAULT TRUE            | Notifikasi aktif                           |
| `email_notification`   | BOOLEAN      | DEFAULT TRUE            | Notifikasi email                           |
| `push_notification`    | BOOLEAN      | DEFAULT TRUE            | Notifikasi push                            |
| `created_at`           | TIMESTAMP    | DEFAULT NOW()           | Waktu dibuat                               |
| `updated_at`           | TIMESTAMP    | DEFAULT NOW()           | Waktu update                               |

**Unique Key**: user_id (one-to-one dengan Users)

---

### 14. **AI_Recommendations**

Cache rekomendasi AI untuk user

| Field        | Type         | Constraint               | Description                   |
| ------------ | ------------ | ------------------------ | ----------------------------- |
| `id`         | UUID         | PRIMARY KEY              | Recommendation ID             |
| `user_id`    | UUID         | FOREIGN KEY → Users(id)  | User terkait                  |
| `event_id`   | UUID         | FOREIGN KEY → Events(id) | Event yang direkomendasikan   |
| `score`      | DECIMAL(5,2) | NOT NULL                 | Skor matching (0-100)         |
| `reason`     | TEXT         | NULLABLE                 | Alasan rekomendasi            |
| `created_at` | TIMESTAMP    | DEFAULT NOW()            | Waktu dibuat                  |
| `expires_at` | TIMESTAMP    | NOT NULL                 | Waktu expired (refresh cache) |

---

## 🔗 Relationships

### One-to-Many Relationships:

1. **Users → Events**
   - One user can create many events
   - `Events.creator_id` → `Users.id`

2. **Users → Communities**
   - One user can create many communities
   - `Communities.creator_id` → `Users.id`

3. **Users → Threads**
   - One user can create many threads
   - `Threads.author_id` → `Users.id`

4. **Users → Comments**
   - One user can make many comments
   - `Comments.author_id` → `Users.id`

5. **Users → Notifications**
   - One user can have many notifications
   - `Notifications.user_id` → `Users.id`

6. **Communities → Threads**
   - One community can have many threads
   - `Threads.community_id` → `Communities.id`

7. **Threads → Comments**
   - One thread can have many comments
   - `Comments.thread_id` → `Threads.id`

8. **Events → Event_Participants**
   - One event can have many participants
   - `Event_Participants.event_id` → `Events.id`

9. **Events → Event_Tags**
   - One event can have many tags
   - `Event_Tags.event_id` → `Events.id`

### Many-to-Many Relationships:

1. **Users ↔ Events** (through Event_Participants)
   - Users can join many events
   - Events can have many participants

2. **Users ↔ Communities** (through Community_Members)
   - Users can join many communities
   - Communities can have many members

3. **Users ↔ Threads/Comments** (through Likes)
   - Users can like many threads/comments
   - Threads/comments can be liked by many users

### One-to-One Relationships:

1. **Users ↔ User_Preferences**
   - One user has one preference record
   - `User_Preferences.user_id` → `Users.id` (UNIQUE)

---

## 📊 Indexes (for Performance)

```sql
-- Users
CREATE INDEX idx_users_email ON Users(email);
CREATE INDEX idx_users_username ON Users(username);

-- Events
CREATE INDEX idx_events_creator ON Events(creator_id);
CREATE INDEX idx_events_date ON Events(event_date);
CREATE INDEX idx_events_category ON Events(category);
CREATE INDEX idx_events_status ON Events(status);
CREATE INDEX idx_events_location ON Events(location_area);

-- Event_Participants
CREATE INDEX idx_participants_event ON Event_Participants(event_id);
CREATE INDEX idx_participants_user ON Event_Participants(user_id);

-- Communities
CREATE INDEX idx_communities_creator ON Communities(creator_id);
CREATE INDEX idx_communities_category ON Communities(category);

-- Community_Members
CREATE INDEX idx_members_community ON Community_Members(community_id);
CREATE INDEX idx_members_user ON Community_Members(user_id);

-- Threads
CREATE INDEX idx_threads_community ON Threads(community_id);
CREATE INDEX idx_threads_author ON Threads(author_id);
CREATE INDEX idx_threads_created ON Threads(created_at DESC);

-- Comments
CREATE INDEX idx_comments_thread ON Comments(thread_id);
CREATE INDEX idx_comments_author ON Comments(author_id);

-- Notifications
CREATE INDEX idx_notifications_user ON Notifications(user_id);
CREATE INDEX idx_notifications_read ON Notifications(is_read);
CREATE INDEX idx_notifications_created ON Notifications(created_at DESC);

-- AI_Recommendations
CREATE INDEX idx_recommendations_user ON AI_Recommendations(user_id);
CREATE INDEX idx_recommendations_event ON AI_Recommendations(event_id);
CREATE INDEX idx_recommendations_expires ON AI_Recommendations(expires_at);
```

---

## 🎯 Business Rules & Constraints

1. **Event Capacity**:
   - `current_participants` cannot exceed `max_participants`
   - Trigger/check before inserting into Event_Participants

2. **Event Status**:
   - Auto-update status based on event_date and time
   - 'upcoming' → 'ongoing' → 'completed'

3. **Community Members**:
   - Creator automatically becomes admin when community is created
   - At least one admin must exist in each community

4. **Likes**:
   - User cannot like the same thread/comment twice
   - Enforced by composite unique key

5. **Notifications**:
   - Auto-generate notifications for:
     - Event reminder (1 day before)
     - New event matching user interests
     - New thread in joined communities
     - Reply to user's comment

6. **AI Recommendations**:
   - Refresh cache every 24 hours
   - Based on user interests, past events, and preferences

---

## 📈 Sample Queries

### Get user's upcoming events

```sql
SELECT e.*, ep.status, ep.joined_at
FROM Events e
JOIN Event_Participants ep ON e.id = ep.event_id
WHERE ep.user_id = :user_id
  AND e.event_date >= CURRENT_DATE
  AND e.status = 'upcoming'
ORDER BY e.event_date ASC, e.event_time ASC;
```

### Get popular events (most participants)

```sql
SELECT e.*, COUNT(ep.user_id) as participant_count
FROM Events e
LEFT JOIN Event_Participants ep ON e.id = ep.event_id
WHERE e.status = 'upcoming'
GROUP BY e.id
ORDER BY participant_count DESC
LIMIT 10;
```

### Get user's activity history

```sql
SELECT ah.*,
       CASE
         WHEN ah.related_type = 'event' THEN e.title
         WHEN ah.related_type = 'community' THEN c.name
         ELSE NULL
       END as related_name
FROM Activity_History ah
LEFT JOIN Events e ON ah.related_type = 'event' AND ah.related_id = e.id
LEFT JOIN Communities c ON ah.related_type = 'community' AND ah.related_id = c.id
WHERE ah.user_id = :user_id
ORDER BY ah.created_at DESC
LIMIT 20;
```

### Get AI recommendations for user

```sql
SELECT e.*, ar.score, ar.reason
FROM AI_Recommendations ar
JOIN Events e ON ar.event_id = e.id
WHERE ar.user_id = :user_id
  AND ar.expires_at > NOW()
  AND e.status = 'upcoming'
  AND e.current_participants < e.max_participants
ORDER BY ar.score DESC
LIMIT 10;
```

---

## 🔄 Data Flow Examples

### User Registration Flow:

1. Insert into `Users` (onboarding_completed = false)
2. Redirect to onboarding
3. Insert into `User_Interests` (multiple records)
4. Insert into `User_Preferences` (one record)
5. Update `Users.onboarding_completed = true`

### Event Creation Flow:

1. Insert into `Events` (creator_id = current_user)
2. Insert into `Event_Tags` (optional, multiple)
3. Insert into `Event_Participants` (creator auto-joins)
4. Generate notifications for users with matching interests
5. Insert into `Activity_History`

### Join Event Flow:

1. Check `Events.current_participants < max_participants`
2. Insert into `Event_Participants`
3. Update `Events.current_participants += 1`
4. Insert into `Activity_History`
5. Generate notification for event creator

---

## 🚀 Future Enhancements

1. **Event_Reviews**: Rating & review setelah event selesai
2. **User_Follows**: Follow system antar users
3. **Event_Categories**: Separate table untuk kategori dinamis
4. **Payment_Transactions**: Tracking pembayaran event berbayar
5. **Chat_Messages**: In-app messaging antar users
6. **Event_Photos**: Gallery foto setelah event
7. **Achievements**: Gamification dengan badges

---

**Generated for**: NgumpulYuk Platform
**Date**: April 2026
**Version**: 1.0
