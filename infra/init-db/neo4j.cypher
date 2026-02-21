// ============================================================
// Bodhi — Neo4j Init Script (Cypher)
// Creates constraints and seed skill tree structure.
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

MERGE (:Category {name: 'Communication',  description: 'Language, conversation, writing'})
MERGE (:Category {name: 'Knowledge',      description: 'Research, search, recall'})
MERGE (:Category {name: 'Productivity',   description: 'Tasks, calendar, notes, email'})
MERGE (:Category {name: 'Code',           description: 'Programming, debugging, review'})
MERGE (:Category {name: 'Creative',       description: 'Brainstorming, writing, art'})
MERGE (:Category {name: 'System',         description: 'File management, processes, monitoring'})
MERGE (:Category {name: 'Social',         description: 'Emotional support, companionship'})

// ── Seed Core Skills ──────────────────────────────────────────

MERGE (s1:Skill {
    skill_id: 'conversation',
    name: 'Conversation',
    description: 'Basic conversational interaction',
    version: '1.0.0',
    status: 'active',
    competency: 0.0,
    xp: 0,
    is_core: true
})
WITH s1
MATCH (c:Category {name: 'Communication'})
MERGE (s1)-[:BELONGS_TO]->(c);

MERGE (s2:Skill {
    skill_id: 'memory_recall',
    name: 'Memory Recall',
    description: 'Retrieve relevant memories to inform responses',
    version: '1.0.0',
    status: 'active',
    competency: 0.0,
    xp: 0,
    is_core: true
})
WITH s2
MATCH (c:Category {name: 'Knowledge'})
MERGE (s2)-[:BELONGS_TO]->(c);

MERGE (s3:Skill {
    skill_id: 'web_search',
    name: 'Web Search',
    description: 'Search the internet for information',
    version: '1.0.0',
    status: 'active',
    competency: 0.0,
    xp: 0
})
WITH s3
MATCH (c:Category {name: 'Knowledge'})
MERGE (s3)-[:BELONGS_TO]->(c);

MERGE (s4:Skill {
    skill_id: 'task_planning',
    name: 'Task Planning',
    description: 'Break down complex goals into actionable steps',
    version: '1.0.0',
    status: 'active',
    competency: 0.0,
    xp: 0
})
WITH s4
MATCH (c:Category {name: 'Productivity'})
MERGE (s4)-[:BELONGS_TO]->(c);

// Prerequisite relationships
MATCH (conv:Skill {skill_id: 'conversation'}),
      (recall:Skill {skill_id: 'memory_recall'})
MERGE (recall)-[:REQUIRES]->(conv);

MATCH (plan:Skill {skill_id: 'task_planning'}),
      (recall:Skill {skill_id: 'memory_recall'})
MERGE (plan)-[:REQUIRES]->(recall);
