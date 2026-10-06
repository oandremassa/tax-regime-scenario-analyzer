# Deployment

## Railway

The repository is configured for Railway with `railway.json` and `Procfile`.

1. Create a Railway project from the GitHub repository.
2. Railway installs `requirements.txt`.
3. Start command runs Gunicorn on `$PORT`.
4. Health check uses `/api/health`.
5. Generate a public domain under Railway Networking.

No mandatory environment variables are required for the synthetic demo.

Recommended optional variables:

```text
SECRET_KEY=<random-value>
DATABASE_PATH=/data/tax_strategy.db
UPLOAD_FOLDER=/data/uploads
```

If a Railway volume is mounted at `/data`, the two path variables above can make the SQLite demo persistent across deployments. Without a volume, the application reseeds a fresh synthetic dataset when the database is recreated.

## Docker

```bash
docker build -t tax-strategy-workspace .
docker run --rm -p 5000:5000 -e PORT=5000 tax-strategy-workspace
```

## Production note

SQLite + local uploads are intentional for the portfolio deployment. A production implementation should use PostgreSQL, object storage, migration tooling, authentication/RBAC, secrets management, backups and monitoring.
