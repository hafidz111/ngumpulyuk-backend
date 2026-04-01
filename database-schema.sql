-- ============================================
-- NgumpulYuk Database Schema
-- PostgreSQL / Supabase Implementation
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. USERS TABLE
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    bio TEXT,
    profile_picture VARCHAR(255),
    location VARCHAR(100),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- ============================================
-- 2. USER_PREFERENCES TABLE
-- ============================================
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preferred_days JSONB, -- ["Sabtu", "Minggu"]
    preferred_time VARCHAR(20) CHECK (preferred_time IN ('morning', 'afternoon', 'evening', 'night')),
    preferred_location VARCHAR(100),
    notification_enabled BOOLEAN DEFAULT TRUE,
    email_notification BOOLEAN DEFAULT TRUE,
    push_notification BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for preferences
CREATE INDEX idx_preferences_user ON user_preferences(user_id);

-- ============================================
-- 3. USER_INTERESTS TABLE
-- ============================================
CREATE TABLE user_interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interest_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, interest_name)
);

-- Index for interests
CREATE INDEX idx_interests_user ON user_interests(user_id);
CREATE INDEX idx_interests_name ON user_interests(interest_name);

-- ============================================
-- 4. EVENTS TABLE
-- ============================================
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    cover_image VARCHAR(255),
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    location_area VARCHAR(100) NOT NULL,
    location_address TEXT NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    max_participants INTEGER NOT NULL CHECK (max_participants > 0),
    current_participants INTEGER DEFAULT 0 CHECK (current_participants >= 0),
    is_free BOOLEAN DEFAULT TRUE,
    price DECIMAL(10, 2) CHECK (price >= 0),
    is_competition BOOLEAN DEFAULT FALSE,
    difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'ongoing', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT check_participants CHECK (current_participants <= max_participants),
    CONSTRAINT check_price CHECK ((is_free = TRUE AND price IS NULL) OR (is_free = FALSE AND price IS NOT NULL))
);

-- Indexes for events
CREATE INDEX idx_events_creator ON events(creator_id);
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_events_category ON events(category);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_location ON events(location_area);
CREATE INDEX idx_events_created_at ON events(created_at DESC);

-- ============================================
-- 5. EVENT_PARTICIPANTS TABLE
-- ============================================
CREATE TABLE event_participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'waitlist', 'cancelled')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    attendance_status VARCHAR(20) CHECK (attendance_status IN ('attended', 'no_show', NULL)),
    UNIQUE(event_id, user_id)
);

-- Indexes for participants
CREATE INDEX idx_participants_event ON event_participants(event_id);
CREATE INDEX idx_participants_user ON event_participants(user_id);
CREATE INDEX idx_participants_status ON event_participants(status);

-- ============================================
-- 6. EVENT_TAGS TABLE
-- ============================================
CREATE TABLE event_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    tag_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for tags
CREATE INDEX idx_tags_event ON event_tags(event_id);
CREATE INDEX idx_tags_name ON event_tags(tag_name);

-- ============================================
-- 7. COMMUNITIES TABLE
-- ============================================
CREATE TABLE communities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    cover_image VARCHAR(255),
    logo VARCHAR(255),
    creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    member_count INTEGER DEFAULT 0 CHECK (member_count >= 0),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for communities
CREATE INDEX idx_communities_creator ON communities(creator_id);
CREATE INDEX idx_communities_category ON communities(category);
CREATE INDEX idx_communities_verified ON communities(is_verified);

-- ============================================
-- 8. COMMUNITY_MEMBERS TABLE
-- ============================================
CREATE TABLE community_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member' CHECK (role IN ('admin', 'moderator', 'member')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(community_id, user_id)
);

-- Indexes for community members
CREATE INDEX idx_members_community ON community_members(community_id);
CREATE INDEX idx_members_user ON community_members(user_id);
CREATE INDEX idx_members_role ON community_members(role);

-- ============================================
-- 9. THREADS TABLE
-- ============================================
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    content TEXT NOT NULL,
    images JSONB, -- Array of image URLs
    like_count INTEGER DEFAULT 0 CHECK (like_count >= 0),
    comment_count INTEGER DEFAULT 0 CHECK (comment_count >= 0),
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for threads
CREATE INDEX idx_threads_community ON threads(community_id);
CREATE INDEX idx_threads_author ON threads(author_id);
CREATE INDEX idx_threads_created_at ON threads(created_at DESC);
CREATE INDEX idx_threads_pinned ON threads(is_pinned, created_at DESC);

-- ============================================
-- 10. COMMENTS TABLE
-- ============================================
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0 CHECK (like_count >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for comments
CREATE INDEX idx_comments_thread ON comments(thread_id);
CREATE INDEX idx_comments_author ON comments(author_id);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);

-- ============================================
-- 11. LIKES TABLE
-- ============================================
CREATE TABLE likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    likeable_type VARCHAR(20) NOT NULL CHECK (likeable_type IN ('thread', 'comment')),
    likeable_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, likeable_type, likeable_id)
);

-- Indexes for likes
CREATE INDEX idx_likes_user ON likes(user_id);
CREATE INDEX idx_likes_target ON likes(likeable_type, likeable_id);

-- ============================================
-- 12. NOTIFICATIONS TABLE
-- ============================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('event_reminder', 'new_event', 'event_update', 'community_post', 'comment_reply', 'new_member', 'event_full')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    link_url VARCHAR(255),
    related_id UUID,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for notifications
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

-- ============================================
-- 13. ACTIVITY_HISTORY TABLE
-- ============================================
CREATE TABLE activity_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN ('joined_event', 'created_event', 'joined_community', 'created_community', 'posted_thread', 'commented')),
    description TEXT NOT NULL,
    related_type VARCHAR(50),
    related_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for activity history
CREATE INDEX idx_activity_user ON activity_history(user_id);
CREATE INDEX idx_activity_created_at ON activity_history(created_at DESC);
CREATE INDEX idx_activity_type ON activity_history(activity_type);

-- ============================================
-- 14. AI_RECOMMENDATIONS TABLE
-- ============================================
CREATE TABLE ai_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    score DECIMAL(5, 2) NOT NULL CHECK (score >= 0 AND score <= 100),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Indexes for AI recommendations
CREATE INDEX idx_recommendations_user ON ai_recommendations(user_id);
CREATE INDEX idx_recommendations_event ON ai_recommendations(event_id);
CREATE INDEX idx_recommendations_expires ON ai_recommendations(expires_at);
CREATE INDEX idx_recommendations_score ON ai_recommendations(user_id, score DESC);

-- ============================================
-- TRIGGERS
-- ============================================

-- Trigger: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communities_updated_at BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_threads_updated_at BEFORE UPDATE ON threads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================

-- Trigger: Increment event participants
CREATE OR REPLACE FUNCTION increment_event_participants()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'confirmed' THEN
        UPDATE events 
        SET current_participants = current_participants + 1
        WHERE id = NEW.event_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_increment_participants
AFTER INSERT ON event_participants
FOR EACH ROW EXECUTE FUNCTION increment_event_participants();

-- ============================================

-- Trigger: Decrement event participants on cancel
CREATE OR REPLACE FUNCTION decrement_event_participants()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'confirmed' AND NEW.status = 'cancelled' THEN
        UPDATE events 
        SET current_participants = current_participants - 1
        WHERE id = OLD.event_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_decrement_participants
AFTER UPDATE ON event_participants
FOR EACH ROW EXECUTE FUNCTION decrement_event_participants();

-- ============================================

-- Trigger: Update community member count
CREATE OR REPLACE FUNCTION update_community_member_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE communities 
        SET member_count = member_count + 1
        WHERE id = NEW.community_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE communities 
        SET member_count = member_count - 1
        WHERE id = OLD.community_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_community_member_count
AFTER INSERT OR DELETE ON community_members
FOR EACH ROW EXECUTE FUNCTION update_community_member_count();

-- ============================================

-- Trigger: Update thread like count
CREATE OR REPLACE FUNCTION update_like_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.likeable_type = 'thread' THEN
            UPDATE threads SET like_count = like_count + 1 WHERE id = NEW.likeable_id;
        ELSIF NEW.likeable_type = 'comment' THEN
            UPDATE comments SET like_count = like_count + 1 WHERE id = NEW.likeable_id;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.likeable_type = 'thread' THEN
            UPDATE threads SET like_count = like_count - 1 WHERE id = OLD.likeable_id;
        ELSIF OLD.likeable_type = 'comment' THEN
            UPDATE comments SET like_count = like_count - 1 WHERE id = OLD.likeable_id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_like_count
AFTER INSERT OR DELETE ON likes
FOR EACH ROW EXECUTE FUNCTION update_like_count();

-- ============================================

-- Trigger: Update thread comment count
CREATE OR REPLACE FUNCTION update_comment_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE threads SET comment_count = comment_count + 1 WHERE id = NEW.thread_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE threads SET comment_count = comment_count - 1 WHERE id = OLD.thread_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_comment_count
AFTER INSERT OR DELETE ON comments
FOR EACH ROW EXECUTE FUNCTION update_comment_count();

-- ============================================

-- Trigger: Auto-add creator as community admin
CREATE OR REPLACE FUNCTION add_creator_as_admin()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO community_members (community_id, user_id, role)
    VALUES (NEW.id, NEW.creator_id, 'admin');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_add_creator_admin
AFTER INSERT ON communities
FOR EACH ROW EXECUTE FUNCTION add_creator_as_admin();

-- ============================================

-- Trigger: Log activity history on event join
CREATE OR REPLACE FUNCTION log_event_join()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'confirmed' THEN
        INSERT INTO activity_history (user_id, activity_type, description, related_type, related_id)
        SELECT NEW.user_id, 'joined_event', 'Joined event: ' || e.title, 'event', NEW.event_id
        FROM events e WHERE e.id = NEW.event_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_event_join
AFTER INSERT ON event_participants
FOR EACH ROW EXECUTE FUNCTION log_event_join();

-- ============================================
-- VIEWS
-- ============================================

-- View: Upcoming events with participant info
CREATE VIEW v_upcoming_events AS
SELECT 
    e.*,
    u.username as creator_username,
    u.full_name as creator_name,
    u.profile_picture as creator_picture,
    ROUND((e.current_participants::DECIMAL / e.max_participants) * 100, 0) as fill_percentage
FROM events e
JOIN users u ON e.creator_id = u.id
WHERE e.status = 'upcoming' 
  AND e.event_date >= CURRENT_DATE
ORDER BY e.event_date ASC, e.event_time ASC;

-- ============================================

-- View: User profile with stats
CREATE VIEW v_user_profiles AS
SELECT 
    u.*,
    COUNT(DISTINCT ep.event_id) as events_joined,
    COUNT(DISTINCT ec.id) as events_created,
    COUNT(DISTINCT cm.community_id) as communities_joined,
    COUNT(DISTINCT cc.id) as communities_created
FROM users u
LEFT JOIN event_participants ep ON u.id = ep.user_id AND ep.status = 'confirmed'
LEFT JOIN events ec ON u.id = ec.creator_id
LEFT JOIN community_members cm ON u.id = cm.user_id
LEFT JOIN communities cc ON u.id = cc.creator_id
GROUP BY u.id;

-- ============================================

-- View: Popular events (most participants)
CREATE VIEW v_popular_events AS
SELECT 
    e.*,
    u.username as creator_username,
    e.current_participants,
    e.max_participants,
    ROUND((e.current_participants::DECIMAL / e.max_participants) * 100, 0) as fill_percentage
FROM events e
JOIN users u ON e.creator_id = u.id
WHERE e.status = 'upcoming'
ORDER BY e.current_participants DESC, e.created_at DESC;

-- ============================================
-- SAMPLE DATA
-- ============================================

-- Insert sample user
INSERT INTO users (email, password_hash, full_name, username, date_of_birth, gender, location, onboarding_completed, is_verified)
VALUES 
    ('aldi@example.com', '$2b$10$hashedpassword', 'Aldi Pratama', 'aldi', '1998-05-15', 'male', 'Jakarta Selatan', TRUE, TRUE),
    ('sarah@example.com', '$2b$10$hashedpassword', 'Sarah Wijaya', 'sarah', '1999-08-22', 'female', 'Jakarta Pusat', TRUE, TRUE),
    ('budi@example.com', '$2b$10$hashedpassword', 'Budi Santoso', 'budi', '1997-03-10', 'male', 'Jakarta Barat', TRUE, TRUE);

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE users IS 'Stores user account information and profile data';
COMMENT ON TABLE events IS 'Stores event information created by users';
COMMENT ON TABLE communities IS 'Stores community groups';
COMMENT ON TABLE event_participants IS 'Junction table for user-event relationships';
COMMENT ON TABLE community_members IS 'Junction table for user-community relationships';
COMMENT ON TABLE notifications IS 'User notifications for various activities';
COMMENT ON TABLE ai_recommendations IS 'AI-generated event recommendations for users';

-- ============================================
-- END OF SCHEMA
-- ============================================
