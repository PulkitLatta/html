# CampusPulse API Specification

## OpenAPI Schema

```yaml
openapi: 3.0.3
info:
  title: CampusPulse API
  description: AI-powered athletic performance analysis platform
  version: 1.0.0
  contact:
    name: CampusPulse Team
    email: support@campuspulse.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.campuspulse.com/v1
    description: Production server
  - url: https://staging-api.campuspulse.com/v1
    description: Staging server
  - url: http://localhost:8000/api
    description: Development server

security:
  - BearerAuth: []

paths:
  # Authentication Endpoints
  /auth/login:
    post:
      tags: [Authentication]
      summary: User login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username, password]
              properties:
                username:
                  type: string
                  example: "athlete@university.edu"
                password:
                  type: string
                  example: "SecurePass123!"
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  refresh_token:
                    type: string
                  token_type:
                    type: string
                    example: "bearer"
                  expires_in:
                    type: integer
                    example: 1800
        '401':
          description: Invalid credentials
        '429':
          description: Too many login attempts

  /auth/refresh:
    post:
      tags: [Authentication]
      summary: Refresh access token
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [refresh_token]
              properties:
                refresh_token:
                  type: string
      responses:
        '200':
          description: Token refreshed
        '401':
          description: Invalid refresh token

  # Submission Endpoints
  /submissions:
    post:
      tags: [Submissions]
      summary: Create new submission
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [analysis_data]
              properties:
                analysis_data:
                  type: object
                  properties:
                    overallScore:
                      type: number
                      minimum: 0
                      maximum: 100
                    formConsistency:
                      type: number
                    movementEfficiency:
                      type: number
                    techniqueScore:
                      type: number
                    balance:
                      type: number
                    duration:
                      type: number
                    totalFrames:
                      type: integer
                    avgConfidence:
                      type: number
                      minimum: 0
                      maximum: 1
                submission_type:
                  type: string
                  default: "analysis"
                video_url:
                  type: string
                  format: uri
      responses:
        '201':
          description: Submission created
        '400':
          description: Invalid submission data
        '429':
          description: Daily submission limit exceeded

  /submissions/me:
    get:
      tags: [Submissions]
      summary: Get user's submissions
      parameters:
        - name: skip
          in: query
          schema:
            type: integer
            default: 0
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, processing, completed, failed]
      responses:
        '200':
          description: List of submissions
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Submission'

  /submissions/{submission_id}:
    get:
      tags: [Submissions]
      summary: Get specific submission
      parameters:
        - name: submission_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Submission details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Submission'
        '404':
          description: Submission not found
        '403':
          description: Access denied

  # Athlete Endpoints
  /athletes/me:
    get:
      tags: [Athletes]
      summary: Get current user profile
      responses:
        '200':
          description: User profile
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

    put:
      tags: [Athletes]
      summary: Update current user profile
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                full_name:
                  type: string
                university:
                  type: string
                sport:
                  type: string
                profile_data:
                  type: object
      responses:
        '200':
          description: Profile updated

  /athletes/me/stats:
    get:
      tags: [Athletes]
      summary: Get current user statistics
      responses:
        '200':
          description: User statistics
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AthleteStats'

  /athletes/{athlete_id}:
    get:
      tags: [Athletes]
      summary: Get public athlete profile
      parameters:
        - name: athlete_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Public profile data

  /leaderboard:
    get:
      tags: [Leaderboard]
      summary: Get leaderboard
      parameters:
        - name: period
          in: query
          schema:
            type: string
            enum: [weekly, monthly, all_time]
            default: weekly
        - name: category
          in: query
          schema:
            type: string
            enum: [overall, sport_specific, university]
            default: overall
        - name: sport
          in: query
          schema:
            type: string
        - name: university
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
            maximum: 200
      responses:
        '200':
          description: Leaderboard entries
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/LeaderboardEntry'

  # Admin Endpoints
  /admin/users:
    get:
      tags: [Admin]
      summary: Get all users (admin only)
      security:
        - BearerAuth: []
      parameters:
        - name: skip
          in: query
          schema:
            type: integer
        - name: limit
          in: query
          schema:
            type: integer
            maximum: 200
      responses:
        '200':
          description: List of users
        '403':
          description: Admin access required

  /admin/submissions/stats:
    get:
      tags: [Admin]
      summary: Get submission statistics
      parameters:
        - name: days
          in: query
          schema:
            type: integer
            default: 7
            maximum: 365
      responses:
        '200':
          description: Submission statistics
          content:
            application/json:
              schema:
                type: object
                properties:
                  total_submissions:
                    type: integer
                  recent_submissions:
                    type: integer
                  status_breakdown:
                    type: object
                  average_scores:
                    type: object

  /health:
    get:
      tags: [System]
      summary: Health check
      security: []
      responses:
        '200':
          description: System status
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  version:
                    type: string
                    example: "1.0.0"
                  database:
                    type: string
                    example: "connected"
                  timestamp:
                    type: string
                    format: date-time

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        username:
          type: string
        full_name:
          type: string
        university:
          type: string
        sport:
          type: string
        role:
          type: string
          enum: [athlete, coach, admin]
        is_active:
          type: boolean
        is_verified:
          type: boolean
        created_at:
          type: string
          format: date-time
        last_login:
          type: string
          format: date-time

    Submission:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        analysis_data:
          type: object
        submission_type:
          type: string
        status:
          type: string
          enum: [pending, processing, completed, failed]
        priority_score:
          type: number
        video_url:
          type: string
          format: uri
        verification_status:
          type: string
          enum: [pending, verified, flagged]
        overall_score:
          type: number
        created_at:
          type: string
          format: date-time
        processed_at:
          type: string
          format: date-time

    AthleteStats:
      type: object
      properties:
        id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        total_sessions:
          type: integer
        total_duration:
          type: number
        current_rank:
          type: integer
        best_score:
          type: number
        average_score:
          type: number
        recent_score:
          type: number
        consistency_rating:
          type: number
        achievements:
          type: object
        created_at:
          type: string
          format: date-time

    LeaderboardEntry:
      type: object
      properties:
        user_id:
          type: string
          format: uuid
        username:
          type: string
        full_name:
          type: string
        university:
          type: string
        sport:
          type: string
        rank:
          type: integer
        score:
          type: number
        sessions_count:
          type: integer

    Error:
      type: object
      properties:
        error:
          type: string
        message:
          type: string
        code:
          type: string
        details:
          type: object
```

## curl Examples

### Authentication

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "athlete@university.edu",
    "password": "SecurePass123!"
  }'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Create Submission

```bash
# Create new performance submission
curl -X POST "http://localhost:8000/api/submissions" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_data": {
      "overallScore": 87.5,
      "formConsistency": 85.2,
      "movementEfficiency": 89.1,
      "techniqueScore": 88.0,
      "balance": 86.5,
      "duration": 12.3,
      "totalFrames": 369,
      "avgConfidence": 0.87,
      "timestamp": 1640995200000,
      "analysisVersion": "1.0.0"
    },
    "submission_type": "analysis",
    "video_url": "https://storage.example.com/videos/123.mp4"
  }'
```

### Get User Submissions

```bash
# Get my submissions with pagination
curl -X GET "http://localhost:8000/api/submissions/me?limit=10&skip=0" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get submissions filtered by status
curl -X GET "http://localhost:8000/api/submissions/me?status=completed" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Get Leaderboard

```bash
# Get weekly overall leaderboard
curl -X GET "http://localhost:8000/api/leaderboard?period=weekly&category=overall" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get university-specific leaderboard for basketball
curl -X GET "http://localhost:8000/api/leaderboard?period=monthly&sport=basketball&university=Stanford" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Get Athlete Profile

```bash
# Get my profile
curl -X GET "http://localhost:8000/api/athletes/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Get my statistics
curl -X GET "http://localhost:8000/api/athletes/me/stats" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Update Profile

```bash
# Update profile information
curl -X PUT "http://localhost:8000/api/athletes/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith",
    "university": "Stanford University",
    "sport": "Basketball",
    "profile_data": {
      "bio": "Junior basketball player",
      "height": "6ft 2in",
      "position": "Guard"
    }
  }'
```

### Admin Operations

```bash
# Get all users (admin only)
curl -X GET "http://localhost:8000/api/admin/users?limit=50" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get submission statistics
curl -X GET "http://localhost:8000/api/admin/submissions/stats?days=30" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Get system health
curl -X GET "http://localhost:8000/api/health"
```

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/login` | 10 requests | 15 minutes |
| `/submissions` | 20 requests | 1 minute |
| `/submissions/me` | 60 requests | 1 minute |
| `/athletes/*` | 100 requests | 1 minute |
| `/leaderboard` | 30 requests | 1 minute |
| `/admin/*` | 30 requests | 1 minute |
| General API | 1000 requests | 1 hour |

## Error Codes

| Code | Description | Example |
|------|-------------|---------|
| 400 | Bad Request | Invalid JSON or missing required fields |
| 401 | Unauthorized | Invalid or expired token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Duplicate resource |
| 422 | Validation Error | Data validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

## Status Codes

### Submission Status
- `pending`: Awaiting processing
- `processing`: Currently being analyzed
- `completed`: Analysis finished successfully
- `failed`: Analysis failed or error occurred

### Verification Status
- `pending`: Awaiting forensics analysis
- `verified`: Passed authenticity checks
- `flagged`: Potential manipulation detected

## Pagination

Most list endpoints support pagination:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: varies, max: 100-200)

Response includes total count when applicable:
```json
{
  "items": [...],
  "total": 150,
  "skip": 20,
  "limit": 20
}
```

## Filtering & Search

### Submission Filters
- `status`: Filter by submission status
- `sport`: Filter by sport type
- `date_from`: Start date (ISO 8601)
- `date_to`: End date (ISO 8601)

### Leaderboard Filters
- `period`: Time period (weekly, monthly, all_time)
- `category`: Grouping (overall, sport_specific, university)
- `sport`: Specific sport filter
- `university`: Specific university filter

## WebSocket Events

Real-time updates via WebSocket (future enhancement):
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Listen for submission updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'submission_update') {
    console.log('Submission updated:', data.payload);
  }
};
```

## SDK Examples

### Python SDK
```python
from campuspulse import CampusPulseClient

client = CampusPulseClient(
    base_url="https://api.campuspulse.com/v1",
    token="your-access-token"
)

# Create submission
submission = client.submissions.create({
    "analysis_data": {...},
    "submission_type": "analysis"
})

# Get leaderboard
leaderboard = client.leaderboard.get(
    period="weekly",
    category="overall"
)
```

### JavaScript SDK
```javascript
import { CampusPulseAPI } from '@campuspulse/api-client';

const api = new CampusPulseAPI({
  baseURL: 'https://api.campuspulse.com/v1',
  token: 'your-access-token'
});

// Create submission
const submission = await api.submissions.create({
  analysis_data: {...},
  submission_type: 'analysis'
});

// Get profile
const profile = await api.athletes.getProfile();
```

This API specification provides comprehensive documentation for integrating with the CampusPulse platform, supporting mobile applications, web dashboards, and third-party integrations.