// ============================================================
// Bodhi — Neo4j Init Script (Cypher)
// Creates constraints and seed skill tree structure.
// Safe to re-run: constraints use IF NOT EXISTS, data uses
// MERGE on unique keys + SET for all other properties.
// ============================================================

// ── Constraints ──────────────────────────────────────────────

CREATE CONSTRAINT skill_id_unique IF NOT EXISTS
FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE;

CREATE CONSTRAINT skill_category_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;

// ── Indexes ───────────────────────────────────────────────────

CREATE INDEX skill_status IF NOT EXISTS
FOR (s:Skill) ON (s.status);

CREATE INDEX skill_competency IF NOT EXISTS
FOR (s:Skill) ON (s.competency);

// ── Root Skill Categories ─────────────────────────────────────
// MERGE only on the constrained key (name); SET description so
// re-runs update the value rather than creating duplicate nodes.

MERGE (c:Category {name: 'Communication'})  SET c.description = 'Language, conversation, writing';
MERGE (c:Category {name: 'Knowledge'})      SET c.description = 'Research, search, recall';
MERGE (c:Category {name: 'Productivity'})   SET c.description = 'Tasks, calendar, notes, email';
MERGE (c:Category {name: 'Code'})           SET c.description = 'Programming, debugging, review';
MERGE (c:Category {name: 'Creative'})       SET c.description = 'Brainstorming, writing, art';
MERGE (c:Category {name: 'System'})         SET c.description = 'File management, processes, monitoring';
MERGE (c:Category {name: 'Social'})         SET c.description = 'Emotional support, companionship';

// ── Seed Core Skills ──────────────────────────────────────────
// MERGE on skill_id (unique constraint); SET all mutable fields.

MERGE (s:Skill {skill_id: 'conversation'})
SET s.name        = 'Conversation',
    s.description = 'Basic conversational interaction',
    s.version     = '1.0.0',
    s.status      = 'active',
    s.is_core     = true
WITH s
MATCH (c:Category {name: 'Communication'})
MERGE (s)-[:BELONGS_TO]->(c);

MERGE (s:Skill {skill_id: 'memory_recall'})
SET s.name        = 'Memory Recall',
    s.description = 'Retrieve relevant memories to inform responses',
    s.version     = '1.0.0',
    s.status      = 'active',
    s.is_core     = true
WITH s
MATCH (c:Category {name: 'Knowledge'})
MERGE (s)-[:BELONGS_TO]->(c);

MERGE (s:Skill {skill_id: 'web_search'})
SET s.name        = 'Web Search',
    s.description = 'Search the internet for information',
    s.version     = '1.0.0',
    s.status      = 'active'
WITH s
MATCH (c:Category {name: 'Knowledge'})
MERGE (s)-[:BELONGS_TO]->(c);

MERGE (s:Skill {skill_id: 'task_planning'})
SET s.name        = 'Task Planning',
    s.description = 'Break down complex goals into actionable steps',
    s.version     = '1.0.0',
    s.status      = 'active'
WITH s
MATCH (c:Category {name: 'Productivity'})
MERGE (s)-[:BELONGS_TO]->(c);

// ── Prerequisite relationships ────────────────────────────────

MATCH (conv:Skill {skill_id: 'conversation'}),
      (recall:Skill {skill_id: 'memory_recall'})
MERGE (recall)-[:REQUIRES]->(conv);

MATCH (plan:Skill {skill_id: 'task_planning'}),
      (recall:Skill {skill_id: 'memory_recall'})
MERGE (plan)-[:REQUIRES]->(recall);
