# Skill Tree System - Detailed Design

**Date:** 2026-02-14  
**Status:** Detailed Design Complete  
**Dependencies:** Neo4j, PostgreSQL, NetworkX (Python)

---

## 1. Architecture Overview

### 1.1 Hybrid Storage Strategy

**Neo4j (Graph Database):**
- Skill relationships: composition, prerequisites, inheritance
- Graph traversal queries: skill paths, dependency chains
- Visual representation for debugging

**PostgreSQL (Relational Database):**
- Skill metadata: names, descriptions, configurations
- Execution statistics: success rates, usage counts, satisfaction scores
- Versioning: skill history, rollback data
- Heavy analytical queries

**In-Memory Cache (Python):**
- Frequently accessed skills (top 20-50)
- Loaded models (lazy + preload hybrid)
- Execution results (TTL-based cache)

### 1.2 Data Flow

```
Central Agent Decision
    ↓
Query Neo4j (graph traversal: find skill path)
    ↓ (skill IDs)
Load Metadata from PostgreSQL (cached)
    ↓ (skill configs)
Load Models (hybrid: preload + lazy)
    ↓
Execute Skill (Dataflow DAG)
    ↓
Update Stats (async to PostgreSQL)
    ↓
Publish Event (Redis: skill execution log)
```

---

## 2. Neo4j Graph Schema

### 2.1 Node Types

**Skill Node:**
```cypher
CREATE CONSTRAINT skill_id_unique ON (s:Skill) ASSERT s.id IS UNIQUE;

(:Skill {
  id: "skill_categorize_email_v2",
  name: "Categorize Email",
  domain: "email_management",
  version: 2,
  current_version: true,  // Only latest version marked true
  created_at: timestamp(),
  deprecated: false
})
```

### 2.2 Relationship Types

**COMPOSED_OF (Hierarchical Structure):**
```cypher
(:Skill {name: "Manage Email"})
  -[:COMPOSED_OF {order: 1, optional: false}]->
(:Skill {name: "Categorize Email"})
```

**REQUIRES (Prerequisites):**
```cypher
(:Skill {name: "Draft Reply"})
  -[:REQUIRES {strength: "hard"}]->  // hard = mandatory, soft = recommended
(:Skill {name: "Read Email"})
```

**SHARES_SUBSKILL (Cross-Domain Reuse):**
```cypher
(:Skill {name: "Categorize Email", domain: "email"})
  -[:SHARES_SUBSKILL {reuse_factor: 0.8}]->
(:Skill {name: "Classify Text", domain: "general"})
```

**SUPERSEDES (Versioning):**
```cypher
(:Skill {name: "Categorize Email", version: 2})
  -[:SUPERSEDES {reason: "Improved accuracy"}]->
(:Skill {name: "Categorize Email", version: 1})
```

**SYNTHESIZED_FROM (Skill Synthesis):**
```cypher
(:Skill {name: "Prioritize Inbox"})
  -[:SYNTHESIZED_FROM {confidence: 0.7}]->
(:Skill {name: "Categorize Email"})

(:Skill {name: "Prioritize Inbox"})
  -[:SYNTHESIZED_FROM {confidence: 0.7}]->
(:Skill {name: "Estimate Urgency"})
```

### 2.3 Example Graph Queries

**Find all sub-skills for composite:**
```cypher
MATCH (parent:Skill {id: $skill_id})-[:COMPOSED_OF*]->(child:Skill)
WHERE child.current_version = true
RETURN child
ORDER BY depth
```

**Check prerequisites satisfied:**
```cypher
MATCH (skill:Skill {id: $skill_id})-[:REQUIRES]->(prereq:Skill)
WHERE NOT EXISTS(
  (user:User {id: $user_id})-[:HAS_MASTERED]->(prereq)
)
RETURN prereq.name AS missing_prerequisite
```

**Find skill synthesis opportunities:**
```cypher
// Find skills that share multiple sub-skills (potential for new composite)
MATCH (s1:Skill)-[:COMPOSED_OF]->(shared:Skill)<-[:COMPOSED_OF]-(s2:Skill)
WHERE s1.id < s2.id  // Avoid duplicates
WITH s1, s2, count(shared) AS shared_count
WHERE shared_count >= 2
RETURN s1.name, s2.name, shared_count
ORDER BY shared_count DESC
LIMIT 10
```

---

## 3. PostgreSQL Schema

### 3.1 Skills Table (Metadata)

```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(100),
    skill_type VARCHAR(50) NOT NULL,  -- 'neural', 'procedural', 'composite'
    version INTEGER NOT NULL DEFAULT 1,
    current_version BOOLEAN DEFAULT true,
    
    -- Execution configuration
    executor_type VARCHAR(50),  -- 'model', 'function', 'dataflow'
    executor_config JSONB NOT NULL,
    
    -- Competency metrics
    level INTEGER DEFAULT 0,  -- 0=novice, 1=competent, 2=expert, 3=master
    xp INTEGER DEFAULT 0,  -- Experience points (for UI display)
    success_rate FLOAT DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    user_satisfaction FLOAT DEFAULT 0.0,
    
    -- Metadata
    description TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    deprecated BOOLEAN DEFAULT false,
    
    CONSTRAINT version_check CHECK (version > 0),
    CONSTRAINT level_check CHECK (level >= 0 AND level <= 3),
    CONSTRAINT success_rate_check CHECK (success_rate >= 0.0 AND success_rate <= 1.0)
);

CREATE INDEX idx_skills_domain ON skills(domain);
CREATE INDEX idx_skills_current ON skills(current_version) WHERE current_version = true;
CREATE INDEX idx_skills_level ON skills(level);
CREATE INDEX idx_skills_type ON skills(skill_type);
CREATE INDEX idx_skills_tags ON skills USING GIN(tags);
```

### 3.2 Skill Executions Table (Statistics)

```sql
CREATE TABLE skill_executions (
    id BIGSERIAL PRIMARY KEY,
    skill_id UUID REFERENCES skills(id),
    skill_version INTEGER NOT NULL,
    
    -- Execution context
    context_hash VARCHAR(64),  -- Hash of input context (for deduplication)
    invoked_by VARCHAR(100),   -- Which agent invoked
    
    -- Results
    success BOOLEAN NOT NULL,
    execution_time_ms INTEGER,
    confidence FLOAT,
    user_feedback INTEGER,  -- -1=negative, 0=neutral, 1=positive, NULL=no feedback
    
    -- Error tracking
    error_type VARCHAR(100),
    error_message TEXT,
    
    -- Metadata
    executed_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT confidence_check CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0))
);

CREATE INDEX idx_executions_skill ON skill_executions(skill_id);
CREATE INDEX idx_executions_time ON skill_executions(executed_at);
CREATE INDEX idx_executions_success ON skill_executions(success);

-- Partitioning by month for performance (optional, for production)
-- CREATE TABLE skill_executions_2026_02 PARTITION OF skill_executions
-- FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### 3.3 Skill Versions Table (Rollback Support)

```sql
CREATE TABLE skill_versions (
    id BIGSERIAL PRIMARY KEY,
    skill_id UUID REFERENCES skills(id),
    version INTEGER NOT NULL,
    
    -- Snapshot of config at this version
    executor_config JSONB NOT NULL,
    model_checkpoint_path TEXT,  -- Path to model weights for this version
    
    -- Performance comparison
    baseline_success_rate FLOAT,
    baseline_latency_ms INTEGER,
    
    -- Change tracking
    change_reason TEXT,
    changed_by VARCHAR(100),  -- 'user', 'trainer_agent', 'auto_optimization'
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    deprecated_at TIMESTAMP,
    
    UNIQUE(skill_id, version)
);

CREATE INDEX idx_versions_skill ON skill_versions(skill_id);
```

### 3.4 Skill Synthesis Candidates Table

```sql
CREATE TABLE skill_synthesis_candidates (
    id BIGSERIAL PRIMARY KEY,
    
    -- Proposed new skill
    candidate_name VARCHAR(255) NOT NULL,
    candidate_domain VARCHAR(100),
    confidence FLOAT,  -- How confident we are this is useful
    
    -- Composition (JSON array of skill IDs)
    component_skills JSONB NOT NULL,  -- ["skill_id_1", "skill_id_2"]
    synthesis_method VARCHAR(50),  -- 'pattern_detection', 'llm_suggestion', 'user_request'
    
    -- Validation
    reviewed_by_user BOOLEAN DEFAULT false,
    approved BOOLEAN,
    rejection_reason TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

CREATE INDEX idx_synthesis_reviewed ON skill_synthesis_candidates(reviewed_by_user);
```

---

## 4. Skill Executor Engine (Python)

### 4.1 Core Executor Class

```python
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import psycopg2
from neo4j import GraphDatabase

class SkillType(Enum):
    NEURAL = "neural"
    PROCEDURAL = "procedural"
    COMPOSITE = "composite"

class ExecutorType(Enum):
    MODEL = "model"
    FUNCTION = "function"
    DATAFLOW = "dataflow"

@dataclass
class ExecutionResult:
    success: bool
    output: Any
    confidence: float
    execution_time_ms: int
    error: Optional[str] = None

class SkillExecutor:
    def __init__(self, pg_conn, neo4j_driver, model_cache):
        self.pg = pg_conn
        self.neo4j = neo4j_driver
        self.model_cache = model_cache
        self.execution_stats_queue = asyncio.Queue()  # Async stats updates
        
        # Hybrid loading: preload top skills
        self._preload_frequent_skills()
    
    def _preload_frequent_skills(self):
        """Load top 20 most-used skills into memory at startup."""
        query = """
            SELECT id, executor_config
            FROM skills
            WHERE current_version = true
            ORDER BY usage_count DESC
            LIMIT 20
        """
        cursor = self.pg.cursor()
        cursor.execute(query)
        
        for skill_id, config in cursor.fetchall():
            if config['executor_type'] == 'model':
                self.model_cache.load(skill_id, config['model_path'])
    
    async def execute(self, skill_id: str, context: Dict[str, Any]) -> ExecutionResult:
        """Main execution entry point."""
        start_time = time.time()
        
        # 1. Load skill metadata (cached)
        skill = self._load_skill_metadata(skill_id)
        
        # 2. Check prerequisites (Neo4j query)
        if not self._check_prerequisites(skill_id, context):
            return ExecutionResult(
                success=False,
                output=None,
                confidence=0.0,
                execution_time_ms=0,
                error="Prerequisites not met"
            )
        
        # 3. Check permissions (if skill requires tool access)
        if skill['requires_permission']:
            if not await self._check_permission(skill, context):
                return ExecutionResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    execution_time_ms=0,
                    error="Permission denied"
                )
        
        # 4. Execute based on type
        try:
            if skill['executor_type'] == ExecutorType.MODEL.value:
                result = await self._execute_model(skill, context)
            elif skill['executor_type'] == ExecutorType.FUNCTION.value:
                result = await self._execute_function(skill, context)
            elif skill['executor_type'] == ExecutorType.DATAFLOW.value:
                result = await self._execute_dataflow(skill, context)
            else:
                raise ValueError(f"Unknown executor type: {skill['executor_type']}")
        
        except Exception as e:
            result = ExecutionResult(
                success=False,
                output=None,
                confidence=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
                error=str(e)
            )
            
            # Critical skill: retry with fallback
            if skill.get('critical', False):
                result = await self._retry_with_fallback(skill, context, e)
        
        # 5. Async stats update (non-blocking)
        execution_time_ms = int((time.time() - start_time) * 1000)
        result.execution_time_ms = execution_time_ms
        await self._queue_stats_update(skill_id, result, context)
        
        # 6. Check for level up (async)
        asyncio.create_task(self._check_level_up(skill_id))
        
        return result
    
    async def _execute_dataflow(self, skill: dict, context: Dict[str, Any]) -> ExecutionResult:
        """Execute composite skill as dataflow DAG."""
        # Load composition graph from Neo4j
        dag = self._load_composition_dag(skill['id'])
        
        # Topological sort for execution order
        execution_order = self._topological_sort(dag)
        
        # Execute nodes (can parallelize independent nodes)
        outputs = {}
        for node in execution_order:
            # Get dependencies
            dependencies = dag.predecessors(node)
            inputs = {dep: outputs[dep] for dep in dependencies}
            
            # Execute child skill
            child_result = await self.execute(node, {**context, **inputs})
            
            if not child_result.success:
                # Dataflow fails if any node fails
                return ExecutionResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    execution_time_ms=0,
                    error=f"Child skill {node} failed: {child_result.error}"
                )
            
            outputs[node] = child_result.output
        
        # Return output of final node
        final_node = execution_order[-1]
        return ExecutionResult(
            success=True,
            output=outputs[final_node],
            confidence=min([outputs[n].confidence for n in outputs]),  # Min confidence
            execution_time_ms=0  # Will be set by caller
        )
    
    def _load_composition_dag(self, skill_id: str):
        """Load DAG from Neo4j."""
        query = """
        MATCH (parent:Skill {id: $skill_id})-[:COMPOSED_OF*]->(child:Skill)
        WHERE child.current_version = true
        RETURN parent.id AS parent, child.id AS child
        """
        with self.neo4j.session() as session:
            result = session.run(query, skill_id=skill_id)
            
            # Build NetworkX DAG
            import networkx as nx
            dag = nx.DiGraph()
            for record in result:
                dag.add_edge(record['parent'], record['child'])
            
            return dag
    
    async def _queue_stats_update(self, skill_id: str, result: ExecutionResult, context: dict):
        """Queue stats update for async processing."""
        await self.execution_stats_queue.put({
            'skill_id': skill_id,
            'success': result.success,
            'execution_time_ms': result.execution_time_ms,
            'confidence': result.confidence,
            'context_hash': self._hash_context(context),
            'error_type': type(result.error).__name__ if result.error else None,
            'error_message': result.error
        })
    
    async def _stats_update_worker(self):
        """Background worker to process stats updates."""
        while True:
            stats = await self.execution_stats_queue.get()
            
            # Insert execution log
            cursor = self.pg.cursor()
            cursor.execute("""
                INSERT INTO skill_executions 
                (skill_id, skill_version, context_hash, invoked_by, success, 
                 execution_time_ms, confidence, error_type, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                stats['skill_id'],
                self._get_skill_version(stats['skill_id']),
                stats['context_hash'],
                'central_agent',  # TODO: Pass actual agent
                stats['success'],
                stats['execution_time_ms'],
                stats['confidence'],
                stats['error_type'],
                stats['error_message']
            ))
            
            # Update aggregated stats (success rate, usage count)
            cursor.execute("""
                UPDATE skills
                SET usage_count = usage_count + 1,
                    last_used = NOW(),
                    success_rate = (
                        SELECT AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END)
                        FROM skill_executions
                        WHERE skill_id = %s
                    )
                WHERE id = %s
            """, (stats['skill_id'], stats['skill_id']))
            
            self.pg.commit()
```

### 4.2 Model Loading Strategy

```python
class HybridModelCache:
    """Hybrid model cache: preload frequent, lazy-load others."""
    
    def __init__(self, max_cache_size_mb=500):
        self.cache = {}  # skill_id -> loaded model
        self.max_size_mb = max_cache_size_mb
        self.current_size_mb = 0
        self.access_counts = {}  # LRU tracking
    
    def load(self, skill_id: str, model_path: str):
        """Load model, evicting LRU if needed."""
        if skill_id in self.cache:
            self.access_counts[skill_id] += 1
            return self.cache[skill_id]
        
        # Load model
        import onnxruntime as ort
        model = ort.InferenceSession(model_path)
        model_size_mb = os.path.getsize(model_path) / (1024 * 1024)
        
        # Evict LRU if over budget
        while self.current_size_mb + model_size_mb > self.max_size_mb:
            lru_skill = min(self.access_counts, key=self.access_counts.get)
            self._evict(lru_skill)
        
        # Add to cache
        self.cache[skill_id] = model
        self.current_size_mb += model_size_mb
        self.access_counts[skill_id] = 1
        
        return model
    
    def _evict(self, skill_id: str):
        """Remove skill from cache."""
        if skill_id in self.cache:
            del self.cache[skill_id]
            # Approximate size reduction (could track exact sizes)
            self.current_size_mb *= 0.9  # Heuristic
            del self.access_counts[skill_id]
```

---

## 5. Skill Synthesis System

### 5.1 Pattern-Based Synthesis

```python
class SkillSynthesizer:
    """Identifies opportunities to create new composite skills."""
    
    def __init__(self, neo4j_driver, pg_conn):
        self.neo4j = neo4j_driver
        self.pg = pg_conn
    
    def find_synthesis_opportunities(self):
        """Run daily to discover new skill combinations."""
        
        # 1. Find frequently co-executed skills
        co_execution_candidates = self._find_co_executed_skills()
        
        # 2. Find skills that share sub-skills (could be combined)
        shared_subskill_candidates = self._find_shared_subskill_patterns()
        
        # 3. Identify skill gaps (user repeatedly does manual sequence)
        gap_candidates = self._find_skill_gaps()
        
        # 4. Store candidates for user review
        all_candidates = co_execution_candidates + shared_subskill_candidates + gap_candidates
        self._store_candidates(all_candidates)
        
        return all_candidates
    
    def _find_co_executed_skills(self):
        """Find skills frequently executed together in sequence."""
        query = """
        WITH skill_sequences AS (
            SELECT 
                skill_id,
                LAG(skill_id) OVER (ORDER BY executed_at) AS prev_skill_id,
                executed_at
            FROM skill_executions
            WHERE executed_at > NOW() - INTERVAL '7 days'
        )
        SELECT 
            prev_skill_id,
            skill_id,
            COUNT(*) AS co_occurrence_count
        FROM skill_sequences
        WHERE prev_skill_id IS NOT NULL
        GROUP BY prev_skill_id, skill_id
        HAVING COUNT(*) > 10  -- Threshold: 10+ times
        ORDER BY co_occurrence_count DESC
        LIMIT 20
        """
        
        cursor = self.pg.cursor()
        cursor.execute(query)
        
        candidates = []
        for prev_skill, skill, count in cursor.fetchall():
            candidates.append({
                'candidate_name': f"Auto-combined: {prev_skill} + {skill}",
                'component_skills': [prev_skill, skill],
                'confidence': min(count / 50.0, 1.0),  # Cap at 50 occurrences = 100% confidence
                'synthesis_method': 'pattern_detection'
            })
        
        return candidates
    
    def _find_shared_subskill_patterns(self):
        """Neo4j query: skills that share multiple sub-skills."""
        query = """
        MATCH (s1:Skill)-[:COMPOSED_OF]->(shared:Skill)<-[:COMPOSED_OF]-(s2:Skill)
        WHERE s1.id < s2.id AND s1.current_version = true AND s2.current_version = true
        WITH s1, s2, collect(shared.name) AS shared_skills, count(shared) AS shared_count
        WHERE shared_count >= 2
        RETURN s1.id, s1.name, s2.id, s2.name, shared_skills, shared_count
        ORDER BY shared_count DESC
        LIMIT 10
        """
        
        with self.neo4j.session() as session:
            result = session.run(query)
            
            candidates = []
            for record in result:
                candidates.append({
                    'candidate_name': f"Hybrid: {record['s1.name']} + {record['s2.name']}",
                    'component_skills': [record['s1.id'], record['s2.id']],
                    'confidence': min(record['shared_count'] / 5.0, 1.0),
                    'synthesis_method': 'shared_subskill_pattern'
                })
            
            return candidates
    
    def _find_skill_gaps(self):
        """Analyze execution logs to find repeated manual actions (gaps)."""
        # TODO: More sophisticated gap analysis
        # For now, placeholder
        return []
```

---

## 6. Skill Leveling System

### 6.1 Competency Formula (TODO: Refine)

```python
def calculate_competency_level(skill_stats: dict) -> int:
    """
    Calculate skill level based on multiple factors.
    
    Formula (v1 - needs refinement):
    - 50% weight: success_rate
    - 20% weight: usage_count (capped at 100)
    - 20% weight: user_satisfaction
    - 10% weight: recency bonus
    
    Returns: 0=novice, 1=competent, 2=expert, 3=master
    
    TODO:
    - Add domain-specific weighting (critical skills need higher bar)
    - Consider variance (consistent vs lucky high success rate)
    - Time decay (old successes count less)
    - Comparative ranking (relative to other skills in domain)
    """
    success_rate = skill_stats['success_rate']
    usage_count = skill_stats['usage_count']
    user_satisfaction = skill_stats.get('user_satisfaction', 0.5)  # Default neutral
    last_used = skill_stats['last_used']
    
    # Normalize usage count (cap at 100 uses = 1.0)
    normalized_usage = min(usage_count / 100.0, 1.0)
    
    # Recency bonus (used in last 7 days = +0.1, else 0)
    days_since_use = (datetime.now() - last_used).days
    recency_bonus = 0.1 if days_since_use <= 7 else 0.0
    
    # Weighted score
    score = (
        0.5 * success_rate +
        0.2 * normalized_usage +
        0.2 * user_satisfaction +
        0.1 * recency_bonus
    )
    
    # Map to levels
    if score < 0.5:
        return 0  # Novice
    elif score < 0.75:
        return 1  # Competent
    elif score < 0.90:
        return 2  # Expert
    else:
        return 3  # Master

def calculate_xp(skill_stats: dict) -> int:
    """
    Calculate XP for UI display (gamification).
    
    XP = base_xp_per_use * usage_count * success_multiplier * satisfaction_multiplier
    
    Level thresholds:
    - Novice: 0-99 XP
    - Competent: 100-499 XP
    - Expert: 500-1999 XP
    - Master: 2000+ XP
    """
    base_xp = 10  # XP per use
    usage_count = skill_stats['usage_count']
    success_rate = skill_stats['success_rate']
    user_satisfaction = skill_stats.get('user_satisfaction', 0.5)
    
    # Multipliers
    success_multiplier = 0.5 + success_rate  # 0.5x to 1.5x
    satisfaction_multiplier = 0.5 + user_satisfaction  # 0.5x to 1.5x
    
    xp = int(base_xp * usage_count * success_multiplier * satisfaction_multiplier)
    return xp
```

---

## 7. Versioning & Rollback

### 7.1 Creating New Version

```python
def create_skill_version(skill_id: str, changes: dict, reason: str) -> int:
    """Create new version of skill, preserving old version."""
    
    cursor = pg.cursor()
    
    # 1. Get current version
    cursor.execute("SELECT version, executor_config FROM skills WHERE id = %s", (skill_id,))
    current_version, old_config = cursor.fetchone()
    
    # 2. Archive current version
    cursor.execute("""
        INSERT INTO skill_versions (skill_id, version, executor_config, change_reason, changed_by)
        VALUES (%s, %s, %s, %s, %s)
    """, (skill_id, current_version, old_config, reason, 'trainer_agent'))
    
    # 3. Mark current version as non-current
    cursor.execute("""
        UPDATE skills SET current_version = false WHERE id = %s
    """, (skill_id,))
    
    # 4. Create new version
    new_version = current_version + 1
    new_config = {**old_config, **changes}
    
    cursor.execute("""
        INSERT INTO skills (id, name, domain, skill_type, version, current_version, executor_type, executor_config)
        SELECT id, name, domain, skill_type, %s, true, executor_type, %s
        FROM skills
        WHERE id = %s AND version = %s
    """, (new_version, new_config, skill_id, current_version))
    
    # 5. Update Neo4j (create SUPERSEDES relationship)
    with neo4j.session() as session:
        session.run("""
            MATCH (old:Skill {id: $skill_id, version: $old_version})
            CREATE (new:Skill {id: $skill_id, version: $new_version, name: old.name, current_version: true})
            CREATE (new)-[:SUPERSEDES {reason: $reason}]->(old)
            SET old.current_version = false
        """, skill_id=skill_id, old_version=current_version, new_version=new_version, reason=reason)
    
    pg.commit()
    return new_version
```

### 7.2 Rollback to Previous Version

```python
def rollback_skill(skill_id: str, target_version: int) -> bool:
    """Rollback skill to previous version (regression detected)."""
    
    cursor = pg.cursor()
    
    # 1. Load target version config
    cursor.execute("""
        SELECT executor_config FROM skill_versions
        WHERE skill_id = %s AND version = %s
    """, (skill_id, target_version))
    
    row = cursor.fetchone()
    if not row:
        return False  # Version not found
    
    target_config = row[0]
    
    # 2. Create new version (rollback is actually a new version pointing to old config)
    cursor.execute("SELECT MAX(version) FROM skills WHERE id = %s", (skill_id,))
    current_version = cursor.fetchone()[0]
    new_version = current_version + 1
    
    cursor.execute("""
        UPDATE skills SET current_version = false WHERE id = %s
    """, (skill_id,))
    
    cursor.execute("""
        INSERT INTO skills (id, name, domain, skill_type, version, current_version, executor_type, executor_config)
        SELECT id, name, domain, skill_type, %s, true, executor_type, %s
        FROM skills
        WHERE id = %s AND version = %s
    """, (new_version, target_config, skill_id, current_version))
    
    # 3. Log rollback reason
    cursor.execute("""
        INSERT INTO skill_versions (skill_id, version, executor_config, change_reason, changed_by)
        VALUES (%s, %s, %s, %s, %s)
    """, (skill_id, new_version, target_config, f"Rollback to v{target_version}", 'evaluation_agent'))
    
    pg.commit()
    return True
```

### 7.3 Regression Detection

```python
def detect_skill_regression(skill_id: str) -> Optional[int]:
    """
    Check if skill performance degraded compared to previous version.
    Returns: target version to rollback to, or None if no regression.
    """
    cursor = pg.cursor()
    
    # Get current and previous version stats
    cursor.execute("""
        WITH version_stats AS (
            SELECT 
                sv.version,
                sv.baseline_success_rate,
                AVG(CASE WHEN se.success THEN 1.0 ELSE 0.0 END) AS current_success_rate,
                COUNT(*) AS sample_size
            FROM skill_versions sv
            LEFT JOIN skill_executions se ON se.skill_id = sv.skill_id AND se.skill_version = sv.version
            WHERE sv.skill_id = %s
            GROUP BY sv.version, sv.baseline_success_rate
        )
        SELECT 
            version,
            current_success_rate,
            baseline_success_rate,
            sample_size
        FROM version_stats
        WHERE sample_size > 20  -- Minimum samples for statistical significance
        ORDER BY version DESC
        LIMIT 2
    """, (skill_id,))
    
    rows = cursor.fetchall()
    if len(rows) < 2:
        return None  # Not enough data
    
    current_version, current_rate, _, _ = rows[0]
    prev_version, prev_rate, _, _ = rows[1]
    
    # Regression threshold: 5% drop in success rate
    if current_rate < prev_rate - 0.05:
        print(f"REGRESSION DETECTED: {skill_id} v{current_version} ({current_rate:.2%}) < v{prev_version} ({prev_rate:.2%})")
        return prev_version
    
    return None
```

---

## 8. Example: End-to-End Skill Execution

### Scenario: User receives email, companion categorizes it

```python
# 1. User receives email (sensory event)
context = {
    "email_id": "msg_12345",
    "from": "boss@company.com",
    "subject": "Q1 Report Deadline",
    "body": "Please submit the Q1 report by Friday...",
    "timestamp": "2026-02-14T10:30:00Z"
}

# 2. Central Agent decides to categorize
skill_id = "skill_categorize_email_v2"

# 3. Execute skill
result = await skill_executor.execute(skill_id, context)

# Behind the scenes:
# a. Load skill metadata from PostgreSQL (5ms, cached)
# b. Check prerequisites via Neo4j:
#    - "Read Email" skill already executed ✓
# c. Load model from cache (1ms, already preloaded)
# d. Run inference:
#    - Input: email subject + body
#    - Model: email_classifier_v2.onnx (100ms)
#    - Output: {"category": "work", "urgency": "high"}
# e. Async stats update queued (non-blocking)
# f. Check level up (async background task)

# 4. Result returned to Central Agent
print(result)
# ExecutionResult(
#     success=True,
#     output={"category": "work", "urgency": "high"},
#     confidence=0.95,
#     execution_time_ms=106
# )

# 5. Stats updated in background (~50ms later):
#    - skill_executions table: INSERT new row
#    - skills table: UPDATE usage_count, success_rate
#    - XP calculated: +10 XP (new total: 487 uses × 10 = 4870 XP → Master level)

# 6. Level up check (async):
#    - Fetch stats, calculate competency: 0.92 success rate → Expert level
#    - But XP already at Master (4870 > 2000) → Display Master in UI
```

---

## 9. TODOs & Future Enhancements

### Phase 1 (MVP):
- [ ] Implement basic PostgreSQL + Neo4j schema
- [ ] Build SkillExecutor with dataflow execution
- [ ] Hybrid model cache with LRU eviction
- [ ] Async stats updates via queue
- [ ] Basic leveling (formula v1)

### Phase 2 (Refinements):
- [ ] **TODO: Refine competency formula** (see section 6.1)
  - Add domain-specific weighting
  - Consider variance (consistent vs lucky)
  - Time decay for old successes
  - Comparative ranking within domain
- [ ] Skill synthesis system (pattern detection)
- [ ] LLM-based planning for creative tasks
- [ ] Versioning UI (show version history to user)
- [ ] Regression detection automation

### Phase 3 (Advanced):
- [ ] Skill synthesis: LLM-suggested combinations
- [ ] A/B testing: Run v1 vs v2 in parallel, compare
- [ ] Federated learning: Share skills across devices (anonymized)
- [ ] Skill marketplace: User-contributed skills
- [ ] Visual skill tree editor (Neo4j Browser integration)

---

## 10. Performance Targets

| Metric | Target | Acceptable | Critical |
|--------|--------|-----------|----------|
| Skill lookup (metadata) | <5ms | <10ms | <20ms |
| Model load (cached) | <1ms | <5ms | <10ms |
| Model load (cold) | <100ms | <500ms | <1s |
| Dataflow execution (3-node) | <200ms | <500ms | <1s |
| Stats update (async) | <50ms | <100ms | <200ms |
| Level up check | <10ms | <50ms | <100ms |
| Neo4j graph query | <20ms | <50ms | <100ms |

**Total latency for typical skill execution: ~100-200ms**

---

## 11. Storage Estimates (1000 Skills)

| Component | Size per Skill | Total (1000 skills) |
|-----------|----------------|---------------------|
| PostgreSQL metadata | 1 KB | 1 MB |
| Neo4j graph nodes | 500 bytes | 500 KB |
| Neo4j relationships | 200 bytes × 3 avg | 600 KB |
| Model weights (30% neural) | 5 MB avg | 1.5 GB |
| Execution logs (1M rows) | 200 bytes | 200 MB |
| Version snapshots (5 versions avg) | 1 MB | 5 GB |
| **Total** | | **~7 GB** |

**Fits comfortably on RPi5 with 32GB+ storage.**

---

**Document Status:** Skill Tree System design complete. Ready for implementation.
