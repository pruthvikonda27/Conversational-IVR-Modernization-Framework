## IRCTC Smart IVR (FastAPI)

### What’s where

- `main.py`: **root entrypoint** (so you can run Uvicorn from this folder)
- `IRCTC/`: project source folder (contains milestones + a local virtualenv)
  - `IRCTC/main.py`: entrypoint that loads Milestone 2 backend
  - `IRCTC/IRCTC/`: Python package with `Milestone2/`, `Milestone3/`, `Milestone4/`

### Run the API (recommended)

From this folder:

```bash
uvicorn main:app --reload
```

### Notes

- `.venv/` is ignored via `.gitignore` (keep it locally, don’t commit it).

