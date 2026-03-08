# Changes

## 2026-03-06

### Fixed
- Resolved frontend dependency conflict that blocked install/build:
  - downgraded `react-leaflet` from `^5.0.0` to `^4.2.1` to match React 18.
- Added reusable backend integration gate helper:
  - `backend/services/integration_requirements.py`
  - `get_missing_env_vars(required)`
  - `ensure_integration_configured(...)`.
- Standardized AI-gated backend endpoints to fail closed with actionable setup payloads:
  - `backend/routers/agents.py`
  - `backend/routers/blog.py`
  - `backend/routers/intel.py`
  - `backend/routers/swoop.py`
  - `backend/routers/bids.py`
- Updated integration requirements doc note to reflect structured 501 response payload.

### Verification
- Frontend lint: pass
- Frontend typecheck (`npx tsc --noEmit`): pass
- Frontend build: pass
- Docker images build: pass (`align-backend`, `align-frontend`)
- Backend syntax compile in container (`python -m compileall backend`): pass

### Still gated by credentials (by design)
- Grok AI features require `XAI_API_KEY`.
- Optional auth integrations require provider-specific env vars.
- Optional S3 storage requires S3/AWS env vars when `STORAGE_BACKEND=s3`.
