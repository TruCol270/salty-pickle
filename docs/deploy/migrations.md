# Postgres Migrations and Beta Seed

Salty Pickle uses Alembic for schema migrations and SQLAlchemy async sessions for application data access.

## Current setup

- Alembic config: `alembic.ini`
- Migration scripts: `app/alembic/versions`
- Alembic env: `app/alembic/env.py`
- SQLAlchemy base/session: `app/database.py`
- Docker startup applies pending migrations with `alembic upgrade head`
- Railway release command also runs `alembic upgrade head`

## Local workflow

```bash
docker-compose up db redis
docker-compose run api alembic upgrade head
docker-compose run api python -m app.seed
```

The Makefile aliases are:

```bash
make migrate
make seed-beta
```

Use a custom beta email when needed:

```bash
docker-compose run api python -m app.seed --email beta.runner@example.com
```

The beta seed is idempotent. It updates the seeded user and plan, then replaces only rows anchored to beta seed source IDs, event IDs, or `source="beta_seed"`.

## Creating migrations

Create schema migrations from model changes:

```bash
docker-compose run api alembic revision --autogenerate -m "describe change"
```

Review generated migrations before committing. Avoid mixing schema DDL with data backfills in the same revision.

Apply pending migrations:

```bash
docker-compose run api alembic upgrade head
```

Check migration state:

```bash
docker-compose run api alembic current
docker-compose run api alembic history
```

## Production migration strategy

1. Take a database backup before deploying a migration.
2. Deploy migrations forward with `alembic upgrade head`.
3. Treat deployed migrations as immutable. If a deployed migration is wrong, create a new forward migration that fixes it.
4. Keep large data changes separate from schema changes and run them in batches.
5. For existing large tables, create indexes concurrently where downtime matters. Alembic needs special handling because `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block.
6. For destructive changes, deploy in phases: remove application reads/writes first, then drop columns or tables in a later migration.

## Backup and rollback

Before production migrations, create a logical backup:

```bash
pg_dump "$DATABASE_URL" --format=custom --file="backup-$(date +%Y%m%d-%H%M%S).dump"
```

Verify the backup can be listed:

```bash
pg_restore --list backup-YYYYMMDD-HHMMSS.dump >/dev/null
```

Rollback preference is a forward fix migration. Use `alembic downgrade` only for local development or an explicitly rehearsed emergency rollback. If restoration is required, restore the backup into a fresh database or maintenance window, then repoint the app after validation.

## Seed data ownership

The beta seed script lives at `app/seed.py`. It does not create schema and should be run only after migrations are at head. It is intended for local, staging, and beta demo data, not production customer data.
