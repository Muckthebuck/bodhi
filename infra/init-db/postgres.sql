-- ============================================================
-- Bodhi — PostgreSQL Init Script
-- Runs once on first container start.
-- ============================================================

-- gen_random_uuid() is built-in from PG 13+; pgcrypto provides it
-- on older versions and is a no-op on 13+.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── Memory System ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS memories (
    memory_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content      TEXT NOT NULL,
    summary      TEXT,
    embedding    BYTEA,                          -- fallback if qdrant unavailable
    importance   FLOAT NOT NULL DEFAULT 0.5,
    memory_type  VARCHAR(20) NOT NULL DEFAULT 'episodic', -- episodic | semantic | working
    session_id   VARCHAR(100) NOT NULL DEFAULT '',
    source       VARCHAR(50),                    -- 'conversation', 'observation', 'skill_execution'
    emotion      JSONB,                          -- {valence, arousal} at time of creation
    metadata     JSONB NOT NULL DEFAULT '{}',
    tags         TEXT[],
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ                     -- NULL = permanent
);

CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags);

-- ── Skill System ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS skills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id        VARCHAR(100) UNIQUE NOT NULL,   -- e.g. 'web_search_v2'
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    version         VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    status          VARCHAR(20) NOT NULL DEFAULT 'active', -- active | deprecated | experimental
    competency      FLOAT NOT NULL DEFAULT 0.0,     -- 0.0 to 1.0
    xp              INTEGER NOT NULL DEFAULT 0,
    execution_count INTEGER NOT NULL DEFAULT 0,
    success_count   INTEGER NOT NULL DEFAULT 0,
    avg_latency_ms  FLOAT,
    last_executed_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skill_executions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id    VARCHAR(100) NOT NULL REFERENCES skills(skill_id),
    status      VARCHAR(20) NOT NULL,               -- success | failure | timeout | cancelled
    latency_ms  INTEGER,
    input_hash  VARCHAR(64),                        -- SHA256 of inputs (for dedup)
    error       TEXT,
    user_rating SMALLINT,                           -- 1-5 if user rated
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skill_executions_skill ON skill_executions(skill_id, created_at DESC);

-- ── Tool Permission System ────────────────────────────────────

CREATE TABLE IF NOT EXISTS tool_permissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id     VARCHAR(100) NOT NULL,
    action      VARCHAR(100) NOT NULL,
    scope       VARCHAR(20) NOT NULL DEFAULT 'session', -- session | permanent | once
    granted     BOOLEAN NOT NULL,
    risk_score  FLOAT,
    context     TEXT,
    granted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ,
    UNIQUE(tool_id, action, scope)
);

CREATE TABLE IF NOT EXISTS tool_audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id     VARCHAR(100) NOT NULL,
    action      VARCHAR(100) NOT NULL,
    status      VARCHAR(20) NOT NULL,               -- executed | blocked | failed
    risk_score  FLOAT,
    sandbox     VARCHAR(30),
    duration_ms INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_tool ON tool_audit_log(tool_id, created_at DESC);

-- ── Personality & Settings ────────────────────────────────────

CREATE TABLE IF NOT EXISTS settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO settings (key, value) VALUES
    ('emotion.personality', '{
        "openness": 0.7,
        "conscientiousness": 0.8,
        "extraversion": 0.6,
        "agreeableness": 0.8,
        "neuroticism": 0.3
    }'),
    ('voice', '{"enabled": false, "model": "en_US-lessac-medium", "wake_word": "hey bodhi"}'),
    ('screen', '{"enabled": true, "mode": "active_window", "client_side_processing": true}'),
    ('character', '{"enabled": true, "style": "2d_skeletal", "position": "bottom_right"}')
ON CONFLICT (key) DO NOTHING;

-- ── Conversation History ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  VARCHAR(100) NOT NULL,
    role        VARCHAR(20) NOT NULL,               -- 'user' | 'bodhi'
    content     TEXT NOT NULL,
    tokens      INTEGER,
    emotion     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id, created_at ASC);
