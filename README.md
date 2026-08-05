# AI Support App

A Streamlit support-ticket application deployed with Databricks Apps and backed by Lakebase Postgres. This is the Day 1 homework foundation for the Databricks AI Engineers Bootcamp.

## Features

- View and filter all support tickets.
- Select a ticket and read its chronological message history.
- Create tickets and add messages.
- Update ticket status.
- Track priority and view status statistics.
- Validate inputs and identify deployed users from Databricks forwarded headers.
- Persist every ticket and message in Lakebase.

## Architecture

```text
Databricks user
    -> Streamlit app on Databricks Apps
    -> SupportRepository (parameterized SQL)
    -> pooled Psycopg connections with rotating OAuth credentials
    -> Lakebase Postgres: support.tickets + support.ticket_messages
```

The app service principal receives PostgreSQL connection settings from its attached Lakebase resource. `WorkspaceClient` requests a fresh database credential whenever the pool opens a connection, so no database password is stored in the repository.

## Project structure

```text
app.py                 Streamlit UI and user workflows
support_app/db.py      Lakebase configuration, OAuth, and connection pooling
support_app/domain.py  Status/priority values, identity, and validation
support_app/models.py  Ticket and message records
support_app/repository.py  Schema initialization, seeding, and CRUD operations
tests/                 Unit tests at the domain and repository seams
app.yaml               Databricks Apps runtime configuration
```

## Run tests locally

Python 3.9 or later is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Local database testing additionally requires Databricks CLI authentication and the environment values described in the [official Lakebase OAuth tutorial](https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling). Never commit those local values.

## Deploy on Databricks Free Edition

1. In **Lakebase Postgres**, create the account's Lakebase project. Use its default `production` branch and `databricks_postgres` database.
2. Open the branch's compute details and copy its resource name in the form `projects/<project>/branches/<branch>/endpoints/<endpoint>`.
3. Set `ENDPOINT_NAME` in `app.yaml` to that non-secret resource name, then commit and push the change to `main`. This repository is already configured for the bootcamp workspace's `new-database/production/primary` endpoint; change it when deploying to another workspace.
4. In **Databricks Apps**, create a custom app named `ai-support-app` and configure its Git source as this public GitHub repository, branch `main`.
5. Add an App resource of type **Database**, select the Lakebase project, `production` branch, and `databricks_postgres` database, and grant **Can connect and create**.
6. Review authorizations and deploy. The first request can take several seconds if Lakebase has scaled to zero.
7. After future pushes, use **Deploy > From Git > main** to redeploy manually. Databricks automatic GitHub deployment currently requires a private repository.

The app creates the `support` schema, both required tables, their constraints and indexes, and the sample records during its first successful startup.

## Verify the homework requirements

Exercise each workflow in the deployed app, refresh the page, and confirm the mutations remain. In the Lakebase SQL Editor, run:

```sql
SELECT ticket_id, title, status, priority, created_by, created_at
FROM support.tickets
ORDER BY ticket_id;

SELECT message_id, ticket_id, message_text, author, created_at
FROM support.ticket_messages
ORDER BY ticket_id, created_at;

SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'support.ticket_messages'::regclass;
```

Capture one screenshot of the deployed app and one showing the Lakebase tables/sample rows. Free Edition Apps stop after 24 hours, so restart the app before final verification or grading if needed.

## Security

- Do not commit `.env` files, OAuth tokens, database credentials, API keys, or screenshots containing secrets.
- `ENDPOINT_NAME` and the `PG*` resource values identify infrastructure but are not database passwords.
- Lakebase is the only runtime datastore; there is no local or hard-coded fallback ticket store.

See [the durable research record](docs/research/databricks-free-edition-app-foundation.md) for the verified platform constraints and primary documentation.
