# Install dependencies and set up environment

## 1. Create & activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install requirements

```bash
pip install -r requirements.txt
```

## 3. Environment variables

- Copy `.env.example` to `.env` and set the values. IMPORTANT: the application does **not** use fallbacks for critical configuration.

Required environment variables (no fallbacks):

- `SQLALCHEMY_DATABASE_URL` — Postgres connection string (required, validated)
- `REDIS_URL` — Redis URL used by Celery (required, will raise if unset)
- `BATCH_SIZE` — The batch size for CSV processing (required, must be a positive integer)

Optional environment variables:

- `CSV_DELETION_POLICY` — Controls when CSV files are deleted after processing:
  - `always` (default): Delete the CSV file regardless of task success or failure
  - `success`: Only delete the CSV file if the task completes successfully
  - `never`: Keep the CSV file for debugging purposes
- `DB_POOL_SIZE` — Database connection pool size (default: 20)
- `DB_MAX_OVERFLOW` — Maximum overflow connections for the database pool (default: 10)

The app uses a centralized configuration module (`app/config.py`) to load and validate environment variables at startup.
