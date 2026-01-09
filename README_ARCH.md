# Recorder AI - Modern Architecture

This project has been re-architected into a full-stack application using FastAPI and Vue 3.

## Architecture

- **Backend**: FastAPI (Python)
  - Database: PostgreSQL (AsyncPG + SQLAlchemy)
  - Cache: Redis
  - Storage: S3 Compatible (MinIO / AWS S3)
  - AI: OpenAI / Anthropic Integration Hooks
- **Frontend**: Vue 3 + Vite
  - UI Library: Ant Design Vue
  - Styling: Tailwind CSS

## Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL
- Redis
- MinIO (or AWS S3 credentials)

## Setup & Run

### Backend

1. Navigate to `backend/`
2. Create virtual environment: `python -m venv venv`
3. Activate venv: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run server: `uvicorn app.main:app --reload`

### Frontend

1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Run dev server: `npm run dev`

## Migration Note

The original `Recorder` library (src/) needs to be integrated into the Vue frontend. Currently, `frontend/src/App.vue` contains a basic skeleton. You should copy the `recorder-core.js` and extensions to `frontend/public/recorder-lib/` or import them if available via npm.
