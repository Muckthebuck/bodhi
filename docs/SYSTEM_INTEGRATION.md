# System Integration Design

**Last Updated:** 2026-02-21  
**Status:** Design Complete  
**Target Platform:** RPi5 Host + Client Devices

---

## 1. Overview & Philosophy

System Integration defines how all components of the Bodhi work together as a cohesive system. This includes containerization, networking, configuration management, monitoring, and deployment strategies.

### Design Principles

1. **Containerized from Day 1:** Everything runs in Docker containers
2. **Multi-Architecture:** Support x86_64 (development) and ARM64 (production)
3. **Service-Oriented:** Each major component is a separate service
4. **Observable:** Comprehensive monitoring and logging
5. **Resilient:** Automatic recovery from failures
6. **Configurable:** Environment-based configuration

---

## 2. Docker Compose Architecture

### 2.1 Service Topology

```yaml
# docker-compose.yml - Main orchestration file

version: '3.8'

services:
  # ===== Infrastructure Services =====
  
  redis:
    image: redis:7-alpine
    container_name: companion-redis
    restart: unless-stopped
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
  
  postgres:
    image: postgres:15-alpine
    container_name: companion-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: companion
      POSTGRES_USER: companion
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U companion"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
  
  neo4j:
    image: neo4j:5-community
    container_name: companion-neo4j
    restart: unless-stopped
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_server_memory_heap_max__size: 512m
      NEO4J_server_memory_pagecache_size: 256m
    ports:
      - "127.0.0.1:7474:7474"  # HTTP
      - "127.0.0.1:7687:7687"  # Bolt
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
  
  qdrant:
    image: qdrant/qdrant:latest
    container_name: companion-qdrant
    restart: unless-stopped
    ports:
      - "127.0.0.1:6333:6333"  # HTTP API
      - "127.0.0.1:6334:6334"  # gRPC
    volumes:
      - qdrant-data:/qdrant/storage
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
  
  # ===== Core Services =====
  
  central-agent:
    build:
      context: ./services/central-agent
      dockerfile: Dockerfile
      args:
        - ARCH=${ARCH:-arm64}
    image: companion/central-agent:${VERSION:-latest}
    container_name: companion-central-agent
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://companion:${POSTGRES_PASSWORD}@postgres:5432/companion
      - NEO4J_URL=bolt://neo4j:7687
      - QDRANT_URL=http://qdrant:6333
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - PERSONALITY_PROFILE=${PERSONALITY_PROFILE:-default}
    volumes:
      - ./config:/app/config:ro
      - ./models:/app/models:ro
      - agent-state:/app/state
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.5'
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  visual-agent:
    build:
      context: ./services/visual-agent
      dockerfile: Dockerfile
    image: companion/visual-agent:${VERSION:-latest}
    container_name: companion-visual-agent
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      central-agent:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
  
  auditory-agent:
    build:
      context: ./services/auditory-agent
      dockerfile: Dockerfile
    image: companion/auditory-agent:${VERSION:-latest}
    container_name: companion-auditory-agent
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      central-agent:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
  
  language-center:
    build:
      context: ./services/language-center
      dockerfile: Dockerfile
    image: companion/language-center:${VERSION:-latest}
    container_name: companion-language-center
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - MODEL_PATH=/app/models/distilbert-tiny
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./models:/app/models:ro
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '1.0'
  
  emotion-regulator:
    build:
      context: ./services/emotion-regulator
      dockerfile: Dockerfile
    image: companion/emotion-regulator:${VERSION:-latest}
    container_name: companion-emotion-regulator
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 64M
          cpus: '0.25'
  
  skill-executor:
    build:
      context: ./services/skill-executor
      dockerfile: Dockerfile
    image: companion/skill-executor:${VERSION:-latest}
    container_name: companion-skill-executor
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      postgres:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - NEO4J_URL=bolt://neo4j:7687
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - POSTGRES_URL=postgresql://companion:${POSTGRES_PASSWORD}@postgres:5432/companion
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./models:/app/models:ro
      - skill-cache:/app/cache
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.5'
  
  memory-manager:
    build:
      context: ./services/memory-manager
      dockerfile: Dockerfile
    image: companion/memory-manager:${VERSION:-latest}
    container_name: companion-memory-manager
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://companion:${POSTGRES_PASSWORD}@postgres:5432/companion
      - QDRANT_URL=http://qdrant:6333
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./models:/app/models:ro
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 384M
          cpus: '1.0'
  
  voice-synthesizer:
    build:
      context: ./services/voice-synthesizer
      dockerfile: Dockerfile
    image: companion/voice-synthesizer:${VERSION:-latest}
    container_name: companion-voice-synthesizer
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - VOICE_MODEL_PATH=/app/models/piper
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./models:/app/models:ro
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 384M
          cpus: '1.5'
  
  motor-controller:
    build:
      context: ./services/motor-controller
      dockerfile: Dockerfile
    image: companion/motor-controller:${VERSION:-latest}
    container_name: companion-motor-controller
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 64M
          cpus: '0.25'
  
  tool-coordinator:
    build:
      context: ./services/tool-coordinator
      dockerfile: Dockerfile
    image: companion/tool-coordinator:${VERSION:-latest}
    container_name: companion-tool-coordinator
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://companion:${POSTGRES_PASSWORD}@postgres:5432/companion
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./tools:/app/tools:ro
      - /var/run/docker.sock:/var/run/docker.sock  # For tool sandboxing
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '1.0'
    privileged: true  # Needed for Docker-in-Docker
  
  # ===== API Gateway =====
  
  api-gateway:
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    image: companion/api-gateway:${VERSION:-latest}
    container_name: companion-api-gateway
    restart: unless-stopped
    depends_on:
      - central-agent
    ports:
      - "0.0.0.0:8080:8080"  # External API
    environment:
      - REDIS_URL=redis://redis:6379
      - CENTRAL_AGENT_URL=http://central-agent:8000
      - TLS_CERT_PATH=/app/certs/server.crt
      - TLS_KEY_PATH=/app/certs/server.key
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./certs:/app/certs:ro
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
  
  # ===== Monitoring & Observability =====
  
  prometheus:
    image: prom/prometheus:latest
    container_name: companion-prometheus
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
  
  grafana:
    image: grafana/grafana:latest
    container_name: companion-grafana
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana-datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.5'
  
  loki:
    image: grafana/loki:latest
    container_name: companion-loki
    restart: unless-stopped
    ports:
      - "127.0.0.1:3100:3100"
    volumes:
      - ./monitoring/loki-config.yml:/etc/loki/config.yml:ro
      - loki-data:/loki
    command: -config.file=/etc/loki/config.yml
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
  
  promtail:
    image: grafana/promtail:latest
    container_name: companion-promtail
    restart: unless-stopped
    volumes:
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - companion-network
    deploy:
      resources:
        limits:
          memory: 64M
          cpus: '0.25'

# ===== Networks =====

networks:
  companion-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

# ===== Volumes =====

volumes:
  redis-data:
  postgres-data:
  neo4j-data:
  neo4j-logs:
  qdrant-data:
  prometheus-data:
  grafana-data:
  loki-data:
  agent-state:
  skill-cache:
```

### 2.2 Multi-Architecture Support

```dockerfile
# Example Dockerfile with multi-arch support
# services/central-agent/Dockerfile

ARG ARCH=arm64

FROM --platform=linux/${ARCH} python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run
CMD ["python", "main.py"]
```

---

## 3. gRPC Communication

### 3.1 Service Definitions

```protobuf
// protos/companion.proto - Main gRPC service definitions

syntax = "proto3";

package companion;

// ===== Client-Host Communication =====

service ClientService {
  // Screen capture
  rpc CaptureScreen(ScreenCaptureRequest) returns (ScreenCaptureResponse);
  
  // Voice input
  rpc SendVoiceTranscript(VoiceTranscriptRequest) returns (AckResponse);
  
  // Play audio output
  rpc PlayAudio(AudioPlaybackRequest) returns (AckResponse);
  
  // Control character
  rpc ControlCharacter(CharacterControlRequest) returns (AckResponse);
  
  // Bidirectional streaming for real-time updates
  rpc StreamEvents(stream ClientEvent) returns (stream HostEvent);
}

// Screen capture request
message ScreenCaptureRequest {
  string mode = 1;  // 'full_screen', 'active_window', 'region', 'smart_areas'
  string query = 2;  // Optional: user's query for context
}

message ScreenCaptureResponse {
  string timestamp = 1;
  AppContext app_context = 2;
  string activity = 3;
  string scene_type = 4;
  TextContent text_content = 5;
  ScreenInsights insights = 6;
  Privacy privacy = 7;
}

message AppContext {
  string app_name = 1;
  string window_title = 2;
  int32 process_id = 3;
}

message TextContent {
  repeated TextBlock blocks = 1;
  string full_text = 2;
}

message TextBlock {
  string text = 1;
  BoundingBox bbox = 2;
  float confidence = 3;
}

message BoundingBox {
  int32 x = 1;
  int32 y = 2;
  int32 width = 3;
  int32 height = 4;
}

message ScreenInsights {
  int32 unread_count = 1;
  string primary_action = 2;
  repeated string notable_items = 3;
}

message Privacy {
  int32 redactions_applied = 1;
  repeated string sensitive_types = 2;
}

// Voice transcript
message VoiceTranscriptRequest {
  string transcript = 1;
  float confidence = 2;
  string timestamp = 3;
}

// Audio playback
message AudioPlaybackRequest {
  bytes audio_data = 1;
  int32 sample_rate = 2;
  repeated Phoneme phonemes = 3;
  float duration = 4;
}

message Phoneme {
  string sound = 1;
  float start_time = 2;
  float duration = 3;
  string mouth_shape = 4;
}

// Character control
message CharacterControlRequest {
  string command_type = 1;  // 'play_animation', 'point_at', 'speak', etc.
  map<string, string> parameters = 2;
}

// Acknowledgment
message AckResponse {
  bool success = 1;
  string message = 2;
}

// Event streaming
message ClientEvent {
  string event_type = 1;
  string timestamp = 2;
  map<string, string> data = 3;
}

message HostEvent {
  string event_type = 1;
  string timestamp = 2;
  map<string, string> data = 3;
}

// ===== Internal Agent Communication =====

service AgentService {
  // Query an agent
  rpc Query(AgentQueryRequest) returns (AgentQueryResponse);
  
  // Execute action
  rpc ExecuteAction(ActionRequest) returns (ActionResponse);
  
  // Get agent status
  rpc GetStatus(StatusRequest) returns (StatusResponse);
}

message AgentQueryRequest {
  string agent_id = 1;
  string query_type = 2;
  map<string, string> parameters = 3;
  string request_id = 4;
}

message AgentQueryResponse {
  string request_id = 1;
  bool success = 2;
  map<string, string> result = 3;
  string error = 4;
}

message ActionRequest {
  string agent_id = 1;
  string action_type = 2;
  map<string, string> parameters = 3;
}

message ActionResponse {
  bool success = 1;
  string result = 2;
  string error = 3;
}

message StatusRequest {
  string agent_id = 1;
}

message StatusResponse {
  string agent_id = 1;
  string state = 2;  // 'active', 'idle', 'error'
  float cpu_usage = 3;
  int64 memory_mb = 4;
  string last_activity = 5;
}
```

### 3.2 Python gRPC Server Example

```python
# services/central-agent/grpc_server.py

import grpc
from concurrent import futures
import companion_pb2
import companion_pb2_grpc

class AgentServiceServicer(companion_pb2_grpc.AgentServiceServicer):
    """gRPC server for agent communication."""
    
    def __init__(self, agent_manager):
        self.agent_manager = agent_manager
    
    async def Query(self, request, context):
        """Handle agent query."""
        agent_id = request.agent_id
        query_type = request.query_type
        params = dict(request.parameters)
        
        # Forward to agent
        try:
            result = await self.agent_manager.query_agent(
                agent_id,
                query_type,
                params
            )
            
            return companion_pb2.AgentQueryResponse(
                request_id=request.request_id,
                success=True,
                result=result
            )
        
        except Exception as e:
            return companion_pb2.AgentQueryResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )
    
    async def ExecuteAction(self, request, context):
        """Handle action execution."""
        agent_id = request.agent_id
        action_type = request.action_type
        params = dict(request.parameters)
        
        try:
            result = await self.agent_manager.execute_action(
                agent_id,
                action_type,
                params
            )
            
            return companion_pb2.ActionResponse(
                success=True,
                result=result
            )
        
        except Exception as e:
            return companion_pb2.ActionResponse(
                success=False,
                error=str(e)
            )
    
    async def GetStatus(self, request, context):
        """Get agent status."""
        agent_id = request.agent_id
        
        status = await self.agent_manager.get_agent_status(agent_id)
        
        return companion_pb2.StatusResponse(
            agent_id=agent_id,
            state=status['state'],
            cpu_usage=status['cpu_usage'],
            memory_mb=status['memory_mb'],
            last_activity=status['last_activity']
        )


async def serve():
    """Start gRPC server."""
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )
    
    companion_pb2_grpc.add_AgentServiceServicer_to_server(
        AgentServiceServicer(agent_manager),
        server
    )
    
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()
```

---

## 4. Configuration Management

### 4.1 Environment-Based Configuration

```bash
# .env.example - Environment variables template

# ===== Infrastructure =====
POSTGRES_PASSWORD=changeme_strong_password
NEO4J_PASSWORD=changeme_strong_password
GRAFANA_PASSWORD=changeme_admin_password

# ===== Application =====
VERSION=latest
ARCH=arm64  # or amd64 for development
LOG_LEVEL=INFO
PERSONALITY_PROFILE=default

# ===== Client Configuration =====
CLIENT_DEVICE_ID=client001
CLIENT_TLS_CERT=/path/to/client.crt
CLIENT_TLS_KEY=/path/to/client.key

# ===== Feature Flags =====
VOICE_ENABLED=false
SCREEN_CAPTURE_ENABLED=true
CHARACTER_ANIMATION_ENABLED=true

# ===== Performance Tuning =====
MEMORY_BUDGET_MB=6000
MAX_ACTIVE_MODULES=8
CONSOLIDATION_INTERVAL_SECONDS=900

# ===== Cloud Integration (Optional) =====
OPENAI_API_KEY=
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
```

### 4.2 Configuration Files

```yaml
# config/companion.yaml - Main configuration file

system:
  name: "Bodhi"
  version: "0.1.0"
  environment: "production"  # development, staging, production

host:
  device_id: "rpi5_001"
  hostname: "companion-host"
  max_memory_mb: 6000
  max_cpu_percent: 80

personality:
  profile: "default"
  big_five:
    openness: 0.7
    conscientiousness: 0.8
    extraversion: 0.6
    agreeableness: 0.8
    neuroticism: 0.3
  voice: "auto"  # auto-select based on personality
  animation_style: "2d_skeletal"

memory:
  redis_ttl_min: 5
  redis_ttl_max: 60
  consolidation_schedule: "*/15 * * * *"  # Every 15 minutes
  importance_threshold: 0.3
  retention_days:
    short_term: 7
    medium_term: 30
    long_term: 365

modules:
  activation_strategy: "weighted_lru"
  preload_threshold: 0.7
  power_aware: true
  minimum_active_set:
    - central_agent
    - working_memory_manager
    - event_bus

tools:
  sandbox_type: "docker"
  permission_mode: "risk_based"
  blacklisted_apps:
    - "1Password"
    - "Bitwarden"
    - "Chase"
    - "PayPal"

monitoring:
  prometheus_enabled: true
  metrics_port: 9100
  log_level: "INFO"
  log_format: "json"

security:
  tls_enabled: true
  cert_path: "/app/certs/server.crt"
  key_path: "/app/certs/server.key"
  client_auth_required: true
```

---

## 5. Monitoring & Observability

### 5.1 Prometheus Metrics

```yaml
# monitoring/prometheus.yml - Prometheus configuration

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Central Agent
  - job_name: 'central-agent'
    static_configs:
      - targets: ['central-agent:9100']
  
  # Visual Agent
  - job_name: 'visual-agent'
    static_configs:
      - targets: ['visual-agent:9100']
  
  # Language Center
  - job_name: 'language-center'
    static_configs:
      - targets: ['language-center:9100']
  
  # Skill Executor
  - job_name: 'skill-executor'
    static_configs:
      - targets: ['skill-executor:9100']
  
  # Infrastructure
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/alerts.yml'
```

### 5.2 Key Metrics to Track

```python
# services/central-agent/metrics.py - Prometheus metrics

from prometheus_client import Counter, Gauge, Histogram, Summary

# Request metrics
request_total = Counter(
    'companion_requests_total',
    'Total number of requests',
    ['agent', 'endpoint', 'status']
)

request_duration = Histogram(
    'companion_request_duration_seconds',
    'Request duration in seconds',
    ['agent', 'endpoint']
)

# Agent metrics
agent_state = Gauge(
    'companion_agent_state',
    'Agent state (0=unloaded, 1=hibernated, 2=standby, 3=active)',
    ['agent_id']
)

agent_memory_mb = Gauge(
    'companion_agent_memory_mb',
    'Agent memory usage in MB',
    ['agent_id']
)

agent_cpu_percent = Gauge(
    'companion_agent_cpu_percent',
    'Agent CPU usage percentage',
    ['agent_id']
)

# Memory system metrics
memory_events_stored = Counter(
    'companion_memory_events_stored_total',
    'Total memory events stored',
    ['tier']  # redis, qdrant, postgres
)

memory_retrieval_latency = Histogram(
    'companion_memory_retrieval_seconds',
    'Memory retrieval latency',
    ['tier', 'query_type']
)

memory_consolidation_duration = Summary(
    'companion_memory_consolidation_seconds',
    'Memory consolidation duration'
)

# Skill execution metrics
skill_executions = Counter(
    'companion_skill_executions_total',
    'Total skill executions',
    ['skill_id', 'status']
)

skill_latency = Histogram(
    'companion_skill_latency_seconds',
    'Skill execution latency',
    ['skill_id']
)

skill_competency = Gauge(
    'companion_skill_competency',
    'Skill competency level (0-1)',
    ['skill_id']
)

# Tool plugin metrics
tool_executions = Counter(
    'companion_tool_executions_total',
    'Total tool executions',
    ['tool_id', 'status']
)

tool_permission_requests = Counter(
    'companion_tool_permission_requests_total',
    'Tool permission requests',
    ['tool_id', 'action', 'result']
)

# Voice pipeline metrics
voice_transcriptions = Counter(
    'companion_voice_transcriptions_total',
    'Total voice transcriptions',
    ['status']
)

voice_synthesis = Counter(
    'companion_voice_synthesis_total',
    'Total voice synthesis operations',
    ['voice', 'status']
)

# Emotional state
emotion_state = Gauge(
    'companion_emotion_valence',
    'Current emotional valence (-1 to 1)',
    []
)

emotion_arousal = Gauge(
    'companion_emotion_arousal',
    'Current arousal level (0 to 1)',
    []
)
```

### 5.3 Grafana Dashboards

```json
// monitoring/grafana-dashboards/companion-overview.json
{
  "dashboard": {
    "title": "Bodhi - Overview",
    "panels": [
      {
        "title": "Active Agents",
        "type": "stat",
        "targets": [
          {
            "expr": "count(companion_agent_state > 0)"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(companion_agent_memory_mb) by (agent_id)"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(companion_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Skill Execution Success Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(rate(companion_skill_executions_total{status='success'}[5m])) / sum(rate(companion_skill_executions_total[5m]))"
          }
        ]
      },
      {
        "title": "Emotional State",
        "type": "gauge",
        "targets": [
          {
            "expr": "companion_emotion_valence"
          },
          {
            "expr": "companion_emotion_arousal"
          }
        ]
      },
      {
        "title": "Top Skills by Usage",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, sum(rate(companion_skill_executions_total[1h])) by (skill_id))"
          }
        ]
      }
    ]
  }
}
```

---

## 6. Deployment Strategies

### 6.1 Initial Setup Script

```bash
#!/bin/bash
# setup.sh - Initial system setup

set -e

echo "🤖 Setting up Bodhi..."

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    export ARCH=arm64
elif [ "$ARCH" = "x86_64" ]; then
    export ARCH=amd64
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

echo "✓ Architecture: $ARCH"

# Check system requirements
echo "Checking system requirements..."

# RAM check (need at least 6GB free)
FREE_RAM=$(free -m | awk '/^Mem:/{print $7}')
if [ "$FREE_RAM" -lt 6000 ]; then
    echo "⚠️  Warning: Less than 6GB free RAM available ($FREE_RAM MB)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Disk check (need at least 20GB free)
FREE_DISK=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$FREE_DISK" -lt 20 ]; then
    echo "❌ Error: Less than 20GB free disk space"
    exit 1
fi

echo "✓ System requirements met"

# Install dependencies
echo "Installing dependencies..."

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
    echo "✓ Docker Compose installed"
else
    echo "✓ Docker Compose already installed"
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p models/{piper,whisper,distilbert-tiny}
mkdir -p tools
mkdir -p certs
mkdir -p config
mkdir -p logs
echo "✓ Directories created"

# Generate TLS certificates
echo "Generating TLS certificates..."
if [ ! -f certs/server.crt ]; then
    openssl req -x509 -newkey rsa:4096 -nodes \
        -keyout certs/server.key \
        -out certs/server.crt \
        -days 365 \
        -subj "/CN=bodhi"
    echo "✓ TLS certificates generated"
else
    echo "✓ TLS certificates already exist"
fi

# Create .env file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate random passwords
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    NEO4J_PASSWORD=$(openssl rand -hex 16)
    GRAFANA_PASSWORD=$(openssl rand -hex 16)
    
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
    sed -i "s/NEO4J_PASSWORD=.*/NEO4J_PASSWORD=$NEO4J_PASSWORD/" .env
    sed -i "s/GRAFANA_PASSWORD=.*/GRAFANA_PASSWORD=$GRAFANA_PASSWORD/" .env
    sed -i "s/ARCH=.*/ARCH=$ARCH/" .env
    
    echo "✓ .env file created with generated passwords"
else
    echo "✓ .env file already exists"
fi

# Download models
echo "Downloading AI models..."
./scripts/download-models.sh

# Initialize databases
echo "Initializing databases..."
docker-compose up -d postgres neo4j qdrant
sleep 10
docker-compose run --rm central-agent python scripts/init-db.py

# Build images
echo "Building Docker images..."
docker-compose build

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review and customize config/companion.yaml"
echo "2. Start the system: docker-compose up -d"
echo "3. View logs: docker-compose logs -f"
echo "4. Access Grafana: http://localhost:3000 (username: admin, password: $GRAFANA_PASSWORD)"
```

### 6.2 Update Script

```bash
#!/bin/bash
# update.sh - Update system to latest version

set -e

echo "🔄 Updating Bodhi..."

# Pull latest code
git pull origin main

# Pull latest images
docker-compose pull

# Rebuild custom images
docker-compose build

# Run database migrations
docker-compose run --rm central-agent python scripts/migrate-db.py

# Restart services with zero downtime
echo "Restarting services..."
docker-compose up -d --no-deps --build central-agent
sleep 5
docker-compose up -d --no-deps --build visual-agent
sleep 5
docker-compose up -d --no-deps --build language-center
sleep 5
# ... etc for other services

echo "✅ Update complete!"
```

### 6.3 Backup Script

```bash
#!/bin/bash
# backup.sh - Backup system data

set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR..."

# Backup databases
echo "Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U companion companion > "$BACKUP_DIR/postgres.sql"

echo "Backing up Neo4j..."
docker-compose exec -T neo4j neo4j-admin dump --to=/tmp/neo4j-backup.dump
docker cp companion-neo4j:/tmp/neo4j-backup.dump "$BACKUP_DIR/neo4j.dump"

echo "Backing up Qdrant..."
docker cp companion-qdrant:/qdrant/storage "$BACKUP_DIR/qdrant-data"

# Backup Redis (if needed for long-term)
echo "Backing up Redis..."
docker-compose exec -T redis redis-cli SAVE
docker cp companion-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

# Backup configuration
echo "Backing up configuration..."
cp -r config "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/"

# Compress
echo "Compressing backup..."
tar -czf "$BACKUP_DIR.tar.gz" -C "$BACKUP_DIR" .
rm -rf "$BACKUP_DIR"

echo "✅ Backup complete: $BACKUP_DIR.tar.gz"
echo "Size: $(du -h $BACKUP_DIR.tar.gz | cut -f1)"
```

---

## 7. Development vs Production

### 7.1 Development Environment

```yaml
# docker-compose.dev.yml - Development overrides

version: '3.8'

services:
  central-agent:
    build:
      args:
        - ARCH=amd64  # Development on x86_64
    volumes:
      - ./services/central-agent:/app  # Mount source for hot reload
    environment:
      - LOG_LEVEL=DEBUG
      - RELOAD=true  # Enable auto-reload
    ports:
      - "8000:8000"  # Expose for debugging
  
  # ... similar overrides for other services
  
  # Development tools
  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@companion.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    networks:
      - companion-network
```

Run development environment:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 7.2 Production Hardening

```yaml
# docker-compose.prod.yml - Production overrides

version: '3.8'

services:
  # All services: read-only root filesystem
  central-agent:
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
  
  # Limit log size
  x-logging: &default-logging
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  
  # Apply logging to all services
  central-agent:
    logging: *default-logging
  
  # ... etc
```

---

## 8. Health Checks & Recovery

### 8.1 Service Health Checks

```python
# services/central-agent/health.py

from fastapi import FastAPI, Response, status
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns 200 if healthy, 503 if unhealthy.
    """
    checks = {
        'redis': await check_redis(),
        'postgres': await check_postgres(),
        'agents': await check_agents()
    }
    
    if all(checks.values()):
        return {
            'status': 'healthy',
            'checks': checks
        }
    else:
        return Response(
            content={'status': 'unhealthy', 'checks': checks},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns 200 if ready to serve traffic.
    """
    # Check if all critical agents are loaded
    if await agents_ready():
        return {'status': 'ready'}
    else:
        return Response(
            content={'status': 'not_ready'},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@app.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Returns 200 if process is alive (lightweight check).
    """
    return {'status': 'alive'}
```

### 8.2 Automatic Recovery

```yaml
# docker-compose.yml - Restart policies

services:
  central-agent:
    restart: unless-stopped  # Restart on failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

---

## 9. Resource Summary

### 9.1 Total Resource Requirements

**Memory (RPi5 8GB):**
```
Infrastructure:
  - Redis: 256 MB
  - PostgreSQL: 512 MB
  - Neo4j: 1024 MB
  - Qdrant: 512 MB
  Subtotal: 2304 MB

Core Services:
  - Central Agent: 512 MB
  - Visual Agent: 50 MB
  - Auditory Agent: 40 MB
  - Language Center: 150 MB
  - Emotion Regulator: 30 MB
  - Skill Executor: 200 MB
  - Memory Manager: 200 MB
  - Voice Synthesizer: 180 MB
  - Motor Controller: 30 MB
  - Tool Coordinator: 80 MB
  Subtotal: 1472 MB

Monitoring:
  - Prometheus: 256 MB
  - Grafana: 128 MB
  - Loki: 256 MB
  - Promtail: 64 MB
  Subtotal: 704 MB

Total: ~4.5 GB (leaves ~3.5 GB for OS and buffers)
```

**Storage:**
```
Databases: ~2 GB
Models: ~1 GB
Logs: ~500 MB (rotating)
Backups: ~3 GB (compressed)
Docker images: ~5 GB
Total: ~12 GB (recommend 32 GB+ SD card)
```

---

## 10. Summary & Next Steps

### Design Complete ✅

**System Integration includes:**
1. ✅ Docker Compose orchestration (16 services)
2. ✅ gRPC communication protocols
3. ✅ Multi-architecture support (ARM64 + x86_64)
4. ✅ Configuration management
5. ✅ Prometheus + Grafana monitoring
6. ✅ Loki logging aggregation
7. ✅ Health checks and automatic recovery
8. ✅ Development and production environments
9. ✅ Setup, update, and backup scripts
10. ✅ Complete resource allocation

### Ready for Implementation

**All 11 architectural systems are now complete:**
1. ✅ Skill Tree System
2. ✅ Memory Consolidation
3. ✅ Central Agent Architecture
4. ✅ Module Activation Strategy
5. ✅ Tool Plugin System
6. ✅ Screen Awareness Pipeline
7. ✅ Character Animation System
8. ✅ Voice Pipeline
9. ✅ Sub-Agent Designs
10. ✅ Architecture Diagrams
11. ✅ System Integration

### Implementation Phases

**Phase 1: Infrastructure (Weeks 1-2)**
- Set up Docker environment
- Deploy databases (PostgreSQL, Neo4j, Redis, Qdrant)
- Configure monitoring (Prometheus, Grafana)

**Phase 2: Core Agents (Weeks 3-8)**
- Implement Central Agent
- Implement Memory Manager
- Implement Language Center
- Implement Emotion Regulator

**Phase 3: Sensory & Motor (Weeks 9-14)**
- Implement Visual Agent
- Implement Auditory Agent
- Implement Motor Controller
- Implement Voice Synthesizer

**Phase 4: Advanced Features (Weeks 15-20)**
- Implement Skill Executor
- Implement Tool Coordinator
- Implement Character Animation
- Implement Screen Awareness

**Phase 5: Integration & Testing (Weeks 21-24)**
- End-to-end integration
- Performance optimization
- Security hardening
- User testing

**Total Estimated Time: 24 weeks (6 months)**

---

**Architecture Status:** ✅ 100% COMPLETE  
**Total Documents:** ~724 KB  
**Ready for:** Implementation Phase 1
