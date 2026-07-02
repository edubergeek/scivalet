# Release Notes: scivalet - Phase 1

Welcome to the initial development release of **scivalet** ("Science Reading List Recommender"). This release lays the architectural foundation, scaffolding both frontend and backend systems, configuring data layers, and setting up the local containerized developer environment.

## 🚀 New Features

### 1. Git Repository Initialization
- Initialized the standard development workflow by checking out the brand-new `develop` branch from `main`.

### 2. FastAPI Backend Application
- Developed the core API server in Python using **FastAPI** (`backend/main.py`).
- Integrated **SQLAlchemy 2.0 ORM** for query building and structured schema mapping.
- Configured connection retry handling for database access to handle environment latency.
- Implemented strictly **CamelCase** properties across all Python models and REST payloads.

### 3. MariaDB Relational Database Schema
Created and verified the complete database architecture in `backend/models.py`:
- `User`: Identifies scientists via ORCID, name, email, and institution.
- `Keyword`: Standard keyword filtering with inclusion and exclusion (negation) flags.
- `Preference`: Stores natural language search prompts.
- `UserContext`: Stores heterogeneous context (code repositories, TED talks, etc.).
- `Publication`: Catalog of scientific papers from arXiv, ADS, Google Scholar, etc.
- `Recommendation`: Individual reading list recommendations with user feedback (upvotes/downvotes).

### 4. Vite React Frontend Scaffolding
- Scaffolding a **Vite React** Single Page Application in the `frontend/` directory.
- Created `frontend/src/index.css` defining the premium design theme (dark slate, cyber-teal/indigo colors, glassmorphic panels, custom scrollbars, and modern Inter typography).

### 5. Docker Orchestration Stack
- Configured `docker-compose.yml` defining four main services:
  - `db`: MariaDB database with persistent volumes.
  - `backend`: FastAPI API server built with custom Dockerfile.
  - `frontend`: Node 20 runtime serving the React application with hot-reloading.
  - `cron-tasks`: Periodic worker service running `backend/cron_scheduler.py`.
- Configured native healthchecks ensuring correct container startup order.

---

## 🛠️ Refactoring & Compilation Fixes
- **GCC 14 Compiler Fix**: Handled a GCC 14 compiler error where incompatible pointer types fail building the `mariadb` library wheel by setting `CFLAGS="-Wno-error=incompatible-pointer-types"` during image builds.

---

## 🧪 Verification & Unit Testing
- Developed an automated testing suite (`backend/tests/test_models.py`) running against an in-memory SQLite database.
- Executed and validated tests inside the built Docker image:
  - `test_user_creation`: PASS
  - `test_keywords_association`: PASS
  - `test_user_preference_prompt`: PASS
  - `test_user_heterogeneous_context`: PASS
  - `test_publications_and_recommendations`: PASS
