# CampusPulse System Architecture

## Overview

CampusPulse is a comprehensive athletic performance analytics platform that uses computer vision and machine learning to analyze exercise form and technique. The system consists of a mobile app for data capture, a backend API for processing and storage, and a web dashboard for analytics and administration.

## System Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│   Mobile App    │◄──►│   Backend API    │◄──►│  Web Dashboard  │
│   (Flutter)     │    │   (FastAPI)      │    │   (React)       │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  Local Storage  │    │   PostgreSQL     │    │   Static Files  │
│   (SQLite)      │    │   Database       │    │   (CDN/S3)      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                │
                                ▼
                       ┌──────────────────┐
                       │                  │
                       │   Redis Cache    │
                       │   & Queue        │
                       │                  │
                       └──────────────────┘
                                │
                                │
                                ▼
                       ┌──────────────────┐
                       │                  │
                       │  ML Processing   │
                       │   & Forensics    │
                       │    Workers       │
                       │                  │
                       └──────────────────┘
```

## Component Details

### 1. Mobile Application (Flutter)

**Purpose**: Capture exercise videos and provide real-time feedback to athletes.

**Key Features**:
- Real-time pose detection using TensorFlow Lite
- Video recording with pose overlay
- Offline analysis with sync capability
- Local data persistence with SQLite
- Background upload queue with retry logic

**Technology Stack**:
- Flutter framework for cross-platform development
- TensorFlow Lite for on-device ML inference
- Camera plugin for video capture
- SQLite for local data storage
- Dio for HTTP client with retry logic

**Architecture**:
```
┌─────────────────────────────────────────┐
│              UI Layer                   │
├─────────────────────────────────────────┤
│         Business Logic Layer            │
├─────────────────────────────────────────┤
│           Service Layer                 │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ ML Service  │  │ Submission Svc  │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│            Data Layer                   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   SQLite    │  │   File System   │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

### 2. Backend API (FastAPI)

**Purpose**: Process submissions, manage data, and provide analytics.

**Key Features**:
- RESTful API with automatic documentation
- JWT authentication and authorization
- File upload and storage management
- Asynchronous background processing
- Forensics analysis for fraud detection
- Real-time analytics and reporting

**Technology Stack**:
- FastAPI for high-performance async API
- PostgreSQL with JSONB for flexible data storage
- SQLAlchemy ORM with Alembic migrations
- Redis for caching and job queues
- RQ (Redis Queue) for background workers
- OpenCV and FFmpeg for video processing

**Architecture**:
```
┌─────────────────────────────────────────┐
│            API Layer                    │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Auth & Auth │  │ Rate Limiting   │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│          Business Logic Layer           │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │    CRUD     │  │   Analytics     │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│            Worker Layer                 │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  Forensics  │  │   Reporting     │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│            Data Layer                   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ PostgreSQL  │  │     Redis       │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

### 3. Web Dashboard (React)

**Purpose**: Administrative interface for coaches and system administrators.

**Key Features**:
- Real-time analytics dashboard
- Athlete profile management
- Submission review and verification
- System health monitoring
- Leaderboard and reporting

**Technology Stack**:
- React 18 with hooks and context
- Vite for fast development and building
- Tailwind CSS for utility-first styling
- React Router for client-side routing
- Recharts for data visualization
- Zustand for state management

**Architecture**:
```
┌─────────────────────────────────────────┐
│           Component Layer               │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │    Pages    │  │   Components    │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│             Hook Layer                  │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Auth Store  │  │   API Hooks     │   │
│  └─────────────┘  └─────────────────┘   │
├─────────────────────────────────────────┤
│           Service Layer                 │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ API Client  │  │     Utils       │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

## Data Flow

### 1. Video Submission Flow

```
Mobile App → Record Video → Analyze Poses → Queue Upload
     ↓
Background Sync → API Upload → Store Video → Queue Processing
     ↓
Forensics Worker → Analyze Video → Update Database
     ↓
Dashboard → Display Results → Admin Review → Final Verification
```

### 2. Real-time Analysis Flow

```
Camera Feed → Pose Detection → Analysis Engine → UI Update
     ↓
Local Storage → Background Sync → Cloud Backup
```

### 3. Authentication Flow

```
Login Request → JWT Generation → Token Storage → API Requests
     ↓
Token Refresh → Automatic Renewal → Session Management
```

## Security Architecture

### Authentication & Authorization
- JWT tokens with configurable expiration
- Role-based access control (athlete, admin, super_admin)
- API key support for external integrations
- Password hashing with bcrypt

### Data Protection
- HTTPS/TLS encryption for all communications
- Database encryption at rest
- File storage with access controls
- PII anonymization in analytics

### API Security
- Rate limiting per endpoint and user
- Request size limits
- CORS configuration
- Input validation and sanitization
- SQL injection prevention via ORM

## Scalability Considerations

### Horizontal Scaling
- Stateless API design for load balancing
- Redis for shared session storage
- Background job processing with multiple workers
- CDN for static file delivery

### Database Optimization
- Indexed queries for performance
- JSONB for flexible document storage
- Connection pooling
- Read replicas for analytics queries

### Caching Strategy
- API response caching with Redis
- Client-side caching with HTTP headers
- CDN caching for static assets
- Database query result caching

## Monitoring & Observability

### Logging
- Structured logging with correlation IDs
- Centralized log aggregation
- Error tracking and alerting
- Performance metrics collection

### Health Checks
- API endpoint health monitoring
- Database connection health
- Redis connectivity checks
- Worker queue monitoring

### Analytics
- User engagement metrics
- System performance metrics
- Business intelligence dashboards
- Custom event tracking

## Deployment Architecture

### Development Environment
```
Docker Compose → Local Services → Hot Reload
```

### Production Environment
```
Load Balancer → API Instances → Database Cluster
      ↓              ↓              ↓
   CDN/Static    Worker Pool    Redis Cluster
```

### CI/CD Pipeline
```
Code Push → Tests → Build → Deploy → Health Check
```

## Technology Decisions

### Database Choice: PostgreSQL
- JSONB support for flexible schema
- ACID compliance for data integrity
- Mature ecosystem and tooling
- Excellent performance for mixed workloads

### API Framework: FastAPI
- Automatic OpenAPI documentation
- High performance with async support
- Built-in validation with Pydantic
- Modern Python features support

### Mobile Framework: Flutter
- Single codebase for iOS/Android
- High performance with native compilation
- Rich ecosystem for ML and camera
- Consistent UI across platforms

### Frontend Framework: React
- Large ecosystem and community
- Component-based architecture
- Excellent developer tooling
- Strong TypeScript support

This architecture provides a solid foundation for the CampusPulse platform while maintaining flexibility for future enhancements and scale.