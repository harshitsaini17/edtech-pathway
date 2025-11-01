# LearnPro Architecture Documentation

## System Overview

LearnPro is an **Agentic RAG (Retrieval-Augmented Generation) Adaptive Learning System** that provides personalized education through real-time curriculum adaptation powered by AI agents and streaming data pipelines.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Web Frontend │  │ Mobile App   │  │ Dashboard (Streamlit)│  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼───────────────────────┼────────────┘
          │                  │                       │
          └──────────────────┼───────────────────────┘
                             │
┌─────────────────────────────┼──────────────────────────────────┐
│                        API GATEWAY LAYER                        │
│                    ┌────────┴────────┐                          │
│                    │   FastAPI REST  │                          │
│                    │   + WebSocket   │                          │
│                    └────────┬────────┘                          │
└─────────────────────────────┼──────────────────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────────┐
│                     ORCHESTRATION LAYER                         │
│            ┌─────────────────┴─────────────────┐                │
│            │   Learning Agent Orchestrator     │                │
│            │   (Decision Engine & State Machine│                │
│            └──┬────────────┬──────────────┬───┘                │
│               │            │              │                     │
│        ┌──────▼──┐   ┌─────▼────┐   ┌────▼─────┐               │
│        │Curriculum│   │Assessment│   │ Content  │               │
│        │ Adapter  │   │ Generator│   │Generator │               │
│        └──────┬──┘   └─────┬────┘   └────┬─────┘               │
└───────────────┼────────────┼─────────────┼───────────────────────┘
                │            │             │
┌───────────────┼────────────┼─────────────┼──────────────────────┐
│              STREAMING & EVENT PROCESSING LAYER                 │
│                    ┌──────┴────────┐                            │
│                    │ Event Stream  │                            │
│                    │    Handler    │                            │
│                    └──────┬────────┘                            │
│                           │                                     │
│                    ┌──────▼────────┐                            │
│                    │    Pathway    │                            │
│                    │   Streaming   │                            │
│                    │   Pipeline    │                            │
│                    └──────┬────────┘                            │
└────────────────────────────┼──────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────┐
│                        DATA LAYER                              │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐     │
│  │ ChromaDB│   │ MongoDB │   │  Redis   │   │  Azure   │     │
│  │ (Vector)│   │(Profiles│   │  (Cache) │   │  OpenAI  │     │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Gateway Layer

**FastAPI REST API** (`server/api/main.py`)
- RESTful endpoints for all operations
- WebSocket support for real-time updates
- Auto-generated OpenAPI documentation
- CORS middleware for cross-origin access

**Key Endpoints:**
- `/api/v1/profile` - Student management
- `/api/v1/theory` - Content delivery
- `/api/v1/quiz` - Assessment generation
- `/api/v1/quiz/submit` - Answer evaluation
- `/api/v1/metrics` - Performance analytics
- `/api/v1/agent/next-action` - AI recommendations

### 2. Orchestration Layer

**Learning Agent Orchestrator** (`server/agent/learning_agent_orchestrator.py`)
- **Decision Engine**: 8-state finite state machine
- **Action Executor**: Coordinates all system components
- **State Management**: Tracks student progression
- **Configurable Thresholds**: Mastery, weak areas, cooldowns

**States:**
1. NOT_STARTED → New student
2. STUDYING_THEORY → Content consumption
3. READY_FOR_ASSESSMENT → Quiz trigger
4. TAKING_QUIZ → Assessment in progress
5. NEEDS_REMEDIATION → Intervention required
6. MASTERED_MODULE → Ready to advance
7. READY_FOR_NEXT_MODULE → Progression
8. COMPLETED_COURSE → Graduation

**Curriculum Adapter** (`server/agent/curriculum_adapter.py`)
- **Topic Reranking**: Prioritizes weak areas
- **Remedial Injection**: RAG-based prerequisite content
- **Difficulty Adjustment**: 4 levels (beginner → expert)
- **Skip-Ahead Logic**: For high performers

### 3. Assessment System

**Adaptive Quiz Generator** (`server/assessment/adaptive_quiz_generator.py`)
- RAG-based question generation
- 5 question types: MCQ, short_answer, true_false, code, numerical
- Context retrieval from vector store
- LLM-powered generation

**Quiz Analyzer** (`server/assessment/quiz_analyzer.py`)
- Intelligent answer evaluation
- Performance metrics calculation
- Weak area detection
- Mastery scoring

### 4. Streaming & Event Processing

**Event Stream Handler** (`server/events/event_stream.py`)
- Thread-safe event buffer
- Backpressure handling
- Multiple event handlers
- Real-time metrics

**Pathway Pipeline** (`server/pathway/pathway_pipeline.py`)
- Real-time event processing
- Stream aggregations (groupby, reduce, join)
- Anomaly detection
- Performance trend analysis

**Input Connectors:**
- Python (in-memory for testing)
- Kafka (production streaming)
- CSV (batch processing)

### 5. Data Layer

**ChromaDB** - Vector Database
- Semantic search for topics
- Question embeddings
- Sentence-transformers (all-MiniLM-L6-v2)
- 384-dimensional embeddings

**MongoDB** - Document Store
- Student profiles
- Module progress
- Quiz attempts
- Performance history

**Redis** - Cache Layer
- Theory content (TTL: 1h)
- Quiz data (TTL: 1h)
- Embeddings (TTL: 7d)
- Metrics (TTL: 5min)

**Azure OpenAI** - LLM Provider
- GPT-4.1 (system1)
- GPT-5 (system2)
- LangChain integration

## Data Flow

### 1. Student Enrollment Flow
```
POST /api/v1/profile
  ↓
Create StudentProfile
  ↓
Initialize in MongoDB
  ↓
Agent: initialize_student
  ↓
Return profile + first action
```

### 2. Content Delivery Flow
```
POST /api/v1/theory
  ↓
Check Redis cache
  ↓ (miss)
Query vector store for context
  ↓
Generate theory via LLM
  ↓
Cache in Redis (1h TTL)
  ↓
Return content
```

### 3. Assessment Flow
```
POST /api/v1/quiz
  ↓
Vector store: search relevant topics
  ↓
LLM: generate questions
  ↓
Cache quiz in Redis
  ↓
Return quiz
  ↓
Student submits answers
  ↓
POST /api/v1/quiz/submit
  ↓
Analyze answers
  ↓
Update student profile
  ↓
Trigger event stream
  ↓
Return results + weak areas
```

### 4. Adaptation Flow
```
Quiz submission event
  ↓
Event Stream Handler
  ↓
Pathway Pipeline (aggregation)
  ↓
Performance metrics
  ↓
Curriculum Adapter
  ↓
Make adaptation decision
  ↓
Apply: rerank/remediate/adjust
  ↓
Update curriculum
  ↓
Notify student
```

### 5. Agent Orchestration Loop
```
Agent: determine_student_state()
  ↓
Agent: make_decision()
  ↓
Decision: {action, reasoning}
  ↓
Agent: execute_action()
  ↓
Update state
  ↓
Record metrics
  ↓
Repeat
```

## Scalability Considerations

### Horizontal Scaling
- **API Layer**: Multiple FastAPI instances behind load balancer
- **Pathway Pipeline**: Distributed processing with Kafka
- **Databases**: MongoDB replica sets, Redis cluster

### Performance Optimization
- **Caching Strategy**: Multi-tier (Redis → ChromaDB → LLM)
- **Connection Pooling**: Database connections reused
- **Async Operations**: Non-blocking I/O throughout
- **Batch Processing**: Events processed in batches

### High Availability
- **Database Replication**: MongoDB replica sets
- **Cache Redundancy**: Redis sentinel/cluster
- **Service Health Checks**: Docker health checks
- **Graceful Degradation**: Cache fallbacks

## Security

### Authentication & Authorization
- JWT tokens for API access
- Role-based access control (RBAC)
- API key for Azure OpenAI
- Token authentication for ChromaDB

### Data Protection
- Encrypted connections (TLS/SSL)
- Sensitive data in environment variables
- MongoDB authentication
- Redis password protection

## Monitoring & Observability

### Metrics
- API response times
- Cache hit rates
- Event processing throughput
- Student progress metrics
- LLM token usage

### Logging
- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging
- Error stack traces

### Dashboard (Streamlit)
- Real-time system health
- Student progress visualization
- Performance analytics
- Curriculum adaptation history

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI | REST API framework |
| Orchestration | Python | Agent logic |
| Streaming | Pathway | Real-time processing |
| Vector DB | ChromaDB | Semantic search |
| Document DB | MongoDB | Student data |
| Cache | Redis | Performance |
| LLM | Azure OpenAI | Content generation |
| Dashboard | Streamlit | Monitoring |
| Containerization | Docker | Deployment |
| Orchestration | Docker Compose | Multi-service |

## Deployment Architecture

### Development
```
docker-compose up
  ↓
Start all services locally
  ↓
API: http://localhost:8000
Dashboard: http://localhost:8501
```

### Production (Kubernetes)
```
├── API Deployment (3 replicas)
├── MongoDB StatefulSet
├── Redis StatefulSet
├── ChromaDB StatefulSet
├── Ingress (Load Balancer)
└── Monitoring (Prometheus + Grafana)
```

## Future Enhancements

1. **Multi-tenancy**: Support multiple institutions
2. **Advanced Analytics**: Predictive performance models
3. **Social Learning**: Peer-to-peer collaboration
4. **Mobile Apps**: Native iOS/Android
5. **Offline Mode**: Progressive Web App (PWA)
6. **A/B Testing**: Experiment framework
7. **Advanced RAG**: Multi-hop reasoning
8. **Voice Interface**: Speech-to-text integration

---

**Version**: 1.0  
**Last Updated**: October 31, 2025  
**Maintained by**: LearnPro Team
