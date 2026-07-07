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

---

# Release Notes: scivalet - Phase 2

Welcome to Phase 2 of **scivalet** ("Science Reading List Recommender"). In this phase, we implemented the core background engines that query online publication repositories and score/filter papers based on user preferences.

## 🚀 New Features

### 1. Environment & Credential Orchestration
- Created a local `.env` configuration template for credentials.
- Parametrizing database credentials (`MYSQL_ROOT_PASSWORD`, `SCIVALET_USER` and `SCIVALET_PASS`) in `docker-compose.yml` for all database, backend, and cron tasks.

### 2. Publication Harvester Ingestion Engine
- Implemented the background `Harvester` daemon (`backend/harvester.py`).
- Integrated queries to the public **arXiv API** via native Python `urllib` parsing XML feed nodes using standard libraries (preventing OWASP vulnerability issues).
- Created mock integrations for Harvard ADS and Google Scholar searches.
- Handled deduplication logic to ensure publications are stored uniquely in MariaDB.

### 3. User Interest Inference & Scoring Engine
- Implemented the `InferenceEngine` (`backend/inference.py`).
- Ingests non-interactive user context items (invited talks, repositories, social logs) to infer positive keyword interests using the ADS keyword taxonomy.
- Computes matching scores for new publications based on user-defined prompt overlap and explicit positive keywords.
- **Negation Filtering**: Automatically filters out papers matching user-specified negated keywords.

### 4. Background Workers & API Triggers
- Updated the periodic worker scheduler (`backend/cron_scheduler.py`) to trigger the harvest and inference loops every 5 minutes.
- Added API endpoints in `backend/main.py`:
  - `POST /api/context`: Ingest user context.
  - `POST /api/jobs/harvest`: Manually trigger paper harvesting.
  - `POST /api/jobs/infer`: Manually trigger interest scoring.

---

## 🧪 Verification & Unit Testing
- Developed automated tests in `backend/tests/test_engines.py` verifying the XML parser, harvester deduplication, and inference negation filtering.
- Executed and validated all tests successfully inside Docker (9/9 tests passed).
- Verified the complete end-to-end user preference-harvest-inference flow in MariaDB via a mock integration test script.

