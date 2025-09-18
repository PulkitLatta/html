# CampusPulse System Architecture

## Overview

CampusPulse is a comprehensive AI-powered athletic performance analysis platform that combines mobile pose detection, cloud-based analytics, and web-based dashboards to provide real-time feedback and insights for athletes and coaches.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Mobile App    │◄──►│   Backend API   │◄──►│   Dashboard     │
│   (Flutter)     │    │   (FastAPI)     │    │   (React)       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│  TensorFlow     │    │   PostgreSQL    │    │   External      │
│  Lite Models    │    │   Database      │    │   APIs          │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                                ▼
                    ┌─────────────────┐
                    │                 │
                    │  Redis Cache    │
                    │  & Job Queue    │
                    │                 │
                    └─────────────────┘
                                │
                                │
                                ▼
                    ┌─────────────────┐
                    │                 │
                    │  Forensics      │
                    │  Worker (RQ)    │
                    │                 │
                    └─────────────────┘
```

## Component Architecture

### 1. Mobile Application (Flutter)

```
Mobile App Structure:
├── main.dart                    # Application entry point
├── routes.dart                  # Navigation configuration
├── screens/                     # UI screens
│   ├── splash_screen.dart      # App initialization
│   ├── home_screen.dart        # Main dashboard
│   ├── camera_screen.dart      # Pose capture interface
│   ├── results_screen.dart     # Analysis results
│   ├── leaderboard_screen.dart # Competition rankings
│   └── profile_screen.dart     # User profile
├── services/                    # Business logic
│   ├── ml_service.dart         # TensorFlow Lite integration
│   ├── analysis.dart           # Performance metrics
│   └── submission_service.dart # API communication
└── widgets/                     # Reusable components
    ├── camera_overlay.dart     # Pose visualization
    └── result_card.dart        # Score display
```

**Key Technologies:**
- Flutter 3.16.0 for cross-platform development
- TensorFlow Lite 2.14.0 for on-device ML inference
- Camera plugin for video capture
- HTTP package for API communication
- Sqflite for local data persistence

**Performance Considerations:**
- Real-time pose detection at 30 FPS
- Efficient memory management for video processing
- Background processing for analysis computation
- Offline capability with sync when connected

### 2. Backend API (FastAPI)

```
Backend Structure:
├── main.py                     # FastAPI application setup
├── models.py                   # SQLAlchemy database models
├── schemas.py                  # Pydantic data validation
├── crud.py                     # Database operations
├── api/                        # REST API endpoints
│   ├── submissions.py         # Performance submissions
│   ├── athletes.py           # User management
│   └── admin.py              # Administrative functions
├── utils/                      # Shared utilities
│   ├── auth.py               # JWT authentication
│   └── storage.py            # File management
└── forensics.py               # Video analysis worker
```

**Key Features:**
- RESTful API design with OpenAPI documentation
- JWT-based authentication and authorization
- Rate limiting and security middleware
- Background job processing with RQ
- Comprehensive error handling and logging

**Scalability:**
- Horizontal scaling with load balancers
- Database connection pooling
- Redis caching for performance
- Asynchronous request handling

### 3. Database Design

```
PostgreSQL Schema:

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Users    │    │ Submissions │    │AthleteStats │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (UUID)   │◄──►│ id (UUID)   │    │ id (UUID)   │
│ email       │    │ user_id     │    │ user_id     │
│ username    │    │ analysis_data│    │ total_sessions│
│ password    │    │ video_url   │    │ best_score  │
│ university  │    │ forensics   │    │ current_rank│
│ sport       │    │ timestamp   │    │ achievements│
│ role        │    └─────────────┘    └─────────────┘
│ profile_data│
└─────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Leaderboards │    │ForensicsLogs│    │SystemSettings│
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (UUID)   │    │ id (UUID)   │    │ key         │
│ user_id     │    │submission_id│    │ value       │
│ period      │    │ verdict     │    │ description │
│ rank        │    │ confidence  │    │ is_public   │
│ score       │    │ results     │    │ updated_at  │
│ updated_at  │    │ created_at  │    └─────────────┘
└─────────────┘    └─────────────┘
```

**Data Strategy:**
- JSONB fields for flexible schema evolution
- Composite indexes for query optimization
- Partitioning for large datasets
- Regular backup and disaster recovery

### 4. Web Dashboard (React)

```
Dashboard Structure:
├── App.jsx                     # Main application component
├── api.js                      # API service layer
├── components/                 # Reusable UI components
│   ├── ErrorBoundary.jsx      # Error handling
│   ├── ProtectedRoute.jsx     # Authentication wrapper
│   ├── KPICard.jsx           # Metrics display
│   ├── Map.jsx               # Geographic visualization
│   └── DataTable.jsx         # Tabular data display
└── pages/                      # Application pages
    ├── Login.jsx              # Authentication
    ├── AdminDashboard.jsx     # Admin overview
    ├── AthleteProfile.jsx     # Individual profiles
    └── Leaderboard.jsx        # Rankings display
```

**UI/UX Features:**
- Responsive design with Tailwind CSS
- Real-time data updates
- Interactive charts and visualizations
- Accessibility compliance (WCAG 2.1)

## Data Flow Architecture

### 1. Performance Analysis Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Camera    │───►│ Pose Extract│───►│  Analysis   │
│   Capture   │    │  (MoveNet)  │    │  Engine     │
└─────────────┘    └─────────────┘    └─────────────┘
                             │                 │
                             ▼                 ▼
                    ┌─────────────┐    ┌─────────────┐
                    │Local Storage│    │   Metrics   │
                    │(SQLite Queue)│    │Calculation  │
                    └─────────────┘    └─────────────┘
                             │                 │
                             ▼                 ▼
                    ┌─────────────┐    ┌─────────────┐
                    │    Sync     │◄───┤   Results   │
                    │ to Backend  │    │   Display   │
                    └─────────────┘    └─────────────┘
```

### 2. Forensics Analysis Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Video Upload │───►│   Queue     │───►│  Analysis   │
│  (optional) │    │  (Redis)    │    │   Worker    │
└─────────────┘    └─────────────┘    └─────────────┘
                             │                 │
                             ▼                 ▼
                    ┌─────────────┐    ┌─────────────┐
                    │ Video Hash  │    │ Optical     │
                    │ Generation  │    │ Flow Check  │
                    └─────────────┘    └─────────────┘
                             │                 │
                             ▼                 ▼
                    ┌─────────────┐    ┌─────────────┐
                    │ Metadata    │    │  Verdict    │
                    │ Analysis    │───►│ Generation  │
                    └─────────────┘    └─────────────┘
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───►│    Auth     │◄──►│  Resource   │
│ Application │    │  Service    │    │   Server    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       │              JWT Token            Protected
       │              Generation           Resources
       ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Local     │    │   Redis     │    │ Role-Based  │
│ Storage     │    │ Blacklist   │    │   Access    │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Security Measures:**
- JWT tokens with short expiration
- Refresh token rotation
- Rate limiting per user/IP
- CORS policy enforcement
- SQL injection prevention
- XSS protection headers

### Data Protection

- **Encryption at Rest**: Database and file storage
- **Encryption in Transit**: HTTPS/TLS 1.3
- **Data Anonymization**: PII removal from analytics
- **Access Logging**: Comprehensive audit trails
- **Privacy Compliance**: GDPR/CCPA adherence

## Machine Learning Architecture

### Model Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Raw       │───►│  Feature    │───►│   Model     │
│   Poses     │    │ Engineering │    │ Inference   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       │             Normalization       TensorFlow
       │             Smoothing           Lite Model
       ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Validation  │    │ Sequence    │    │Performance  │
│  & Cleanup  │    │Generation   │    │  Scores     │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Model Specifications:**
- **Input**: 17 keypoints × 2 coordinates (34 features)
- **Architecture**: LSTM with attention mechanism
- **Output**: 5 technique classes + confidence scores
- **Latency**: <100ms inference time on mobile
- **Accuracy**: 87.3% on validation dataset

## Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                     │
│                  (nginx/HAProxy)                    │
└─────────────────┬───────────────┬───────────────────┘
                  │               │
                  ▼               ▼
        ┌─────────────┐    ┌─────────────┐
        │   API       │    │   API       │
        │ Server 1    │    │ Server 2    │
        └─────────────┘    └─────────────┘
                  │               │
                  └───────┬───────┘
                          │
        ┌─────────────────▼─────────────────┐
        │          Database Cluster         │
        │    (Primary + Read Replicas)     │
        └───────────────────────────────────┘
```

### Container Architecture

```yaml
# docker-compose.yml structure
services:
  backend:        # FastAPI application
  dashboard:      # React frontend
  database:       # PostgreSQL
  redis:          # Cache & job queue  
  worker:         # Background jobs
  nginx:          # Reverse proxy
  monitoring:     # Observability stack
```

### CI/CD Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Source    │───►│    Build    │───►│    Test     │
│   Control   │    │   & Package │    │   & QA      │
│   (GitHub)  │    │  (Docker)   │    │ (Automated) │
└─────────────┘    └─────────────┘    └─────────────┘
                            │                 │
                            ▼                 ▼
                   ┌─────────────┐    ┌─────────────┐
                   │   Deploy    │◄───┤  Security   │
                   │(Kubernetes) │    │   Scan      │
                   └─────────────┘    └─────────────┘
```

## Monitoring & Observability

### Metrics Collection

- **Application Metrics**: Request rate, latency, error rate
- **Business Metrics**: User activity, submission success rate
- **Infrastructure Metrics**: CPU, memory, disk, network
- **ML Metrics**: Model accuracy, inference latency

### Logging Strategy

- **Structured Logging**: JSON format for searchability
- **Log Levels**: DEBUG, INFO, WARN, ERROR, CRITICAL  
- **Correlation IDs**: Request tracing across services
- **Retention Policy**: 30 days hot, 90 days cold storage

### Alerting Framework

- **SLA Monitoring**: 99.9% uptime target
- **Error Rate Alerts**: >5% error rate threshold
- **Performance Alerts**: >2s response time
- **Business Alerts**: Low user engagement

## Scalability Considerations

### Horizontal Scaling

- **API Layer**: Stateless services behind load balancer
- **Database**: Read replicas and connection pooling
- **File Storage**: CDN distribution for global access
- **ML Inference**: GPU clusters for batch processing

### Performance Optimization

- **Caching Strategy**: Multi-layer caching (Redis, CDN)
- **Database Optimization**: Query optimization, indexing
- **Code Optimization**: Async processing, connection reuse
- **Resource Management**: Auto-scaling based on load

## Future Architecture Evolution

### Short-term Enhancements
- Microservices decomposition
- Event-driven architecture
- Real-time streaming analytics
- Mobile offline-first capabilities

### Long-term Vision
- Multi-region deployment
- Edge computing for ultra-low latency
- AI-powered auto-scaling
- Blockchain integration for data integrity

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|------------|---------|----------|
| Mobile | Flutter | 3.16.0 | Cross-platform mobile app |
| Backend | FastAPI | 0.104.1 | High-performance API server |
| Database | PostgreSQL | 14+ | Relational data storage |
| Cache | Redis | 7.0+ | Caching and job queue |
| Frontend | React | 18.2.0 | Web dashboard interface |
| ML | TensorFlow Lite | 2.14.0 | Mobile ML inference |
| Deployment | Docker | 20.10+ | Containerization |
| Orchestration | Kubernetes | 1.25+ | Container orchestration |
| Monitoring | Prometheus/Grafana | Latest | Metrics and visualization |

This architecture provides a robust, scalable foundation for CampusPulse while maintaining flexibility for future enhancements and growth.