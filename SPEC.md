You are an expert full-stack TypeScript and Python developer and education technology specialist. Build a complete, production-ready MVP for a secure, locally-hosted Student Learning Analytics and MTSS Recommendation System.

## App Name

Compass

## Goal

Build Compass as a traditional internal web application using a Next.js frontend and FastAPI backend. The app must run entirely on local infrastructure, keep all student data on-premises, and support role-based access for district staff.

## Product Requirements

### Purpose

- Collect and analyze student learning data such as homework, quizzes, tests, and progress monitoring scores.
- Identify strengths and weaknesses by subject.
- Determine MTSS tier status for students and classes.
- Recommend personalized curriculum adjustments and interventions.

### MTSS Framework Integration

The app must make MTSS explicit throughout the product:

- Tier 1: Universal high-quality core instruction for all students.
- Tier 2: Targeted supplemental interventions for some students.
- Tier 3: Intensive individualized supports for a smaller group of students.

Use screening and progress-monitoring data to:

- calculate current tier placement
- flag students needing support
- suggest evidence-based interventions

### Role-Based Access Control

Strict RBAC is required:

- IT Admin: full access to users, schools, classes, subjects, benchmarks, and system settings
- District Admin: read access to all schools, district dashboards, and district-wide reports
- Principal: access only to their assigned school, including all classes and grade levels in that school
- Teacher: access only to assigned classes and students

### Security and Deployment

- 100% local deployment on an internal school or district server
- no cloud services
- all PII remains on-premises
- use SQLite for MVP simplicity and easy backups
- support later migration to PostgreSQL if concurrency grows
- authenticate with bcrypt-hashed passwords
- use backend-managed sessions in secure cookies
- never expose Ollama or raw database access directly to the browser

### Local AI Analysis

Integrate Ollama running locally on port 11434.

Requirements:

- configurable model name, defaulting to `llama3.2` or `mistral-nemo`
- configurable temperature
- one-click student analysis
- one-click class analysis
- responses must include:
  - recommended MTSS tier
  - curriculum recommendations
  - intervention strategies
  - rationale with references to actual scores

## Required MVP Features

### 1. Authentication

- login page
- user session handling
- logout
- current-user endpoint
- role-aware frontend navigation

Note:

- if a username can have multiple roles in future, the UI may support role selection after login
- for the MVP, one role per user is acceptable if that simplifies implementation

### 2. Navigation

- role-aware sidebar or app shell
- clean internal-app UX with no framework-branded deploy UI
- protected routes

### 3. Data Management

Manage:

- students
- classes
- schools
- subjects
- scores

Student fields:

- student name
- student ID
- grade level
- assigned school
- assigned class

Score fields:

- student
- subject
- score type: homework, quiz, test
- score value
- date
- notes

Also include:

- downloadable CSV template
- CSV bulk score import
- server-side validation for CSV uploads

### 4. Dashboards

Provide dashboards for:

- student profile
- class overview
- school overview
- district overview

Dashboard requirements:

- scores over time
- subject strengths and weaknesses
- class and grade averages
- percent of students per MTSS tier
- alerts for Tier 2 and Tier 3 students
- color coding:
  - green: >= 80%
  - yellow: 70-79%
  - red: < 70%

### 5. AI-Powered Recommendations

- analyze individual students
- analyze classes
- display results clearly
- store recommendation history
- allow teacher and principal visibility to relevant recommendation history

### 6. Intervention Tracking

Teachers must be able to log:

- intervention strategy
- description
- start date
- outcome notes
- review or resolution status

### 7. Alerts

Highlight:

- students needing Tier 2 support
- students needing Tier 3 support
- classes with high concentrations of at-risk students

### 8. Admin Tools

IT Admin must be able to:

- create, edit, and delete users
- assign roles
- assign schools and classes
- manage schools
- manage classes
- manage subjects
- configure benchmark thresholds by grade and subject

### 9. Reports

Support PDF and CSV exports for:

- student summaries
- class summaries
- school summaries
- district summaries

### 10. Helpful Extras

Include:

- dark/light mode
- sample data loader for first-time setup
- progress monitoring trends over time
- search and filter across students
- audit log for compliance
- configurable Ollama model name and temperature

## Recommended Technical Architecture

### Frontend

Use Next.js with TypeScript.

Recommended responsibilities:

- page routing
- forms and validation UX
- tables and search/filter interfaces
- dashboard rendering
- protected layouts
- role-aware navigation
- report download flows
- dark/light theme toggle

Recommended frontend stack:

- Next.js
- TypeScript
- React
- Tailwind CSS or a similar UI styling approach
- Plotly, Recharts, or Chart.js for charts
- React Hook Form and Zod if desired for form validation

### Backend

Use FastAPI with Python.

Recommended responsibilities:

- authentication
- authorization
- CRUD APIs
- CSV import parsing and validation
- MTSS tier calculations
- benchmark application
- AI integration with Ollama
- report generation
- audit logging

Recommended backend stack:

- FastAPI
- SQLAlchemy or SQLModel
- SQLite for MVP
- Alembic for migrations
- bcrypt or passlib with bcrypt
- Pydantic for request and response schemas

### Database

Start from this data model:

- schools
- users
- classes
- students
- subjects
- scores
- ai_recs
- interventions
- audit_log
- benchmarks

Optional:

- sessions table if you want DB-backed session tracking

## API Design

Design the backend around JSON APIs under `/api`.

### Auth

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Dashboard

- `GET /api/dashboard/teacher`
- `GET /api/dashboard/principal`
- `GET /api/dashboard/district`

### Students

- `GET /api/students`
- `GET /api/students/{student_id}`
- `POST /api/students`
- `PATCH /api/students/{student_id}`

### Scores

- `POST /api/scores`
- `POST /api/scores/import`
- `GET /api/scores/student/{student_id}`

### AI

- `POST /api/ai/student/{student_id}/analyze`
- `POST /api/ai/class/{class_id}/analyze`
- `GET /api/ai/student/{student_id}/history`
- `GET /api/ai/class/{class_id}/history`

### Interventions

- `GET /api/interventions`
- `POST /api/interventions`
- `PATCH /api/interventions/{intervention_id}`

### Admin

- `GET /api/admin/users`
- `POST /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `DELETE /api/admin/users/{user_id}`
- matching CRUD routes for schools, classes, subjects, and benchmarks

### Reports

- `GET /api/reports/student/{student_id}.csv`
- `GET /api/reports/student/{student_id}.pdf`
- `GET /api/reports/class/{class_id}.csv`
- `GET /api/reports/class/{class_id}.pdf`

## Application Structure

Use a monorepo-style layout like this:

```text
compass/
  frontend/
    package.json
    src/
      app/
        login/
        dashboard/
        students/
        students/[id]/
        scores/
        ai/
        admin/
        reports/
      components/
      lib/
      styles/
  backend/
    pyproject.toml
    app/
      main.py
      config.py
      db.py
      models/
      schemas/
      routes/
      services/
      middleware/
      tests/
  deploy/
  docs/
```

## Business Logic Guidance

### MTSS Tier Logic

Tier should be computed in backend service code, not in frontend components.

Default thresholds:

- Tier 1: >= 80
- Tier 2: 70-79
- Tier 3: < 70

The backend must support benchmark overrides by grade and subject.

### AI Logic

The frontend should never call Ollama directly.

Correct flow:

1. frontend calls FastAPI
2. FastAPI gathers student or class summary data
3. FastAPI builds the prompt
4. FastAPI calls local Ollama
5. FastAPI stores recommendation history
6. FastAPI returns the result to the frontend

## UX Requirements

The UI should feel like a polished internal school app, not a developer dashboard.

Requirements:

- educator-friendly language
- clear MTSS labels and tooltips
- responsive layout for desktop and laptop use
- accessible color usage
- simple navigation
- intentional visual design

## Deliverables

Provide:

1. Full frontend source code
2. Full backend source code
3. Frontend and backend dependency manifests
4. Root README with:
   - installation steps
   - local development steps
   - how to run frontend and backend
   - Ollama setup and model pull command
   - how to load demo data
   - how to back up the database
5. Database schema diagram in text form
6. Sample CSV import template
7. Database migration or initialization scripts
8. Deployment notes for running on a local internal server

## Implementation Priorities

Build in this order:

### Phase 1

- backend auth and sessions
- frontend login and protected layout
- student, class, subject, and score data model
- student list and profile
- score entry
- CSV score import

### Phase 2

- teacher dashboard
- principal dashboard
- district dashboard
- alerts and at-risk indicators

### Phase 3

- AI analysis and recommendation history
- intervention tracking
- benchmark configuration

### Phase 4

- reports
- audit logging
- theme toggle
- search and filtering polish

## Final Instruction

Generate the complete MVP using Next.js for the frontend and FastAPI for the backend. Prioritize maintainability, secure local deployment, clear role separation, and an educator-friendly user experience.

