# Databricks Free Edition AI Support App Foundation

Last verified: **2026-08-04**

This note preserves the verified platform facts, assignment requirements, and project decisions for the Day 1 AI support application. Platform claims below are grounded only in first-party Databricks documentation. Assignment requirements are identified separately because their source is the bootcamp prompt, not Databricks documentation.

## Assignment requirements (bootcamp-provided)

The application must use Lakebase as its operational datastore and include two related tables:

- `tickets`: `ticket_id`, `title`, `status`, `created_by`, and `created_at`.
- `ticket_messages`: `message_id`, `ticket_id`, `message_text`, `author`, and `created_at`.
- `ticket_messages.ticket_id` must reference `tickets.ticket_id`.

The database must contain at least three tickets, two messages per ticket, and at least two ticket statuses. The deployed app must list tickets, display the selected ticket's messages, create tickets, add messages, and update status. Every operation must read or write Lakebase, and writes must remain after refresh.

The submission must contain the Databricks App URL, a source-code ZIP, a screenshot of the deployed app, a screenshot of the Lakebase tables and sample rows, and a 3–5 sentence reflection addressing the hardest part, Lakebase versus a traditional analytics table, and a potential next feature. Secrets and credentials must not be submitted.

Selected bonus features for version one:

- Ticket priority.
- Status filtering.
- Input validation and useful error messages.
- Ticket statistics.
- Improved visual design.

Delete functionality is deliberately excluded from version one.

## Verified Databricks Free Edition facts

- Free Edition provides only serverless compute and does not support custom compute configurations. It is subject to a fair-use policy; if quota is exceeded, compute can be unavailable until the daily or, in extreme cases, monthly limit resets, while data and settings are retained. [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- A Free Edition account supports up to three Databricks Apps. An app runs for up to 24 hours after it is started, updated, or redeployed, then stops automatically; it can be restarted. [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- A Free Edition account supports one Lakebase project with scale-to-zero compute. [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- Lakebase scale-to-zero can make the first database query after an idle period take several seconds. [Using Lakebase with Databricks Apps](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps)
- Free Edition is intended for non-commercial use and has no guaranteed reliability, support, or SLA. These constraints are acceptable for this bootcamp assignment but should not be assumed suitable for a production support system. [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)

## Verified application and Lakebase architecture

- Databricks Apps hosts interactive applications in the workspace. Adding Lakebase as an app resource provides a managed PostgreSQL backend. Databricks creates an app service principal, creates or reuses a matching PostgreSQL role, grants database access, and supplies connection details as environment variables. [Using Lakebase with Databricks Apps](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps), [Add a Lakebase resource to a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
- A new Lakebase project starts with a `production` branch and a `databricks_postgres` database. Projects contain branches, which represent isolated database environments. [Using Lakebase with Databricks Apps](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps)
- For a Lakebase Autoscaling resource, the app configuration selects a project, branch, and database. The currently available resource permission is **Can connect and create**, which grants the service principal `CONNECT` and `CREATE` privileges on the selected database. Adding the resource requires `CAN MANAGE` on the project. [Add a Lakebase resource to a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
- For the first database resource, Databricks supplies `PGAPPNAME`, `PGDATABASE`, `PGHOST`, `PGPORT`, `PGSSLMODE`, and `PGUSER`. `PGUSER` is the app service principal's client ID and PostgreSQL role name. [Add a Lakebase resource to a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
- Lakebase resources persist independently of app lifecycle: schemas and tables created by the app remain after the app is redeployed or stopped. This is the persistence behavior the homework refresh test should demonstrate. [Add a Lakebase resource to a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
- Databricks Apps can deploy Python applications, install dependencies from `requirements.txt`, and run the command defined in `app.yaml`. The repository must contain the entry point, dependencies, and app configuration needed for deployment. [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)

The resulting application data flow is:

1. A user opens the Streamlit UI through the Databricks Apps reverse proxy.
2. Streamlit calls the repository layer for ticket reads and mutations.
3. The repository obtains a pooled PostgreSQL connection using the Lakebase resource's `PG*` settings and a fresh OAuth database credential.
4. Parameterized SQL reads or updates the `support` schema in Lakebase.
5. The UI reruns and reads the durable state back from Lakebase.

## Verified authentication and identity behavior

- Databricks Apps authenticate to Lakebase with OAuth database tokens that expire after one hour. Databricks' documented rotation pattern uses `WorkspaceClient`, a custom Psycopg connection that generates a fresh credential when a connection is created, and a connection pool so newly opened connections do not reuse expired credentials. The app runs as its service principal in Databricks and as the current Databricks user during authenticated local development. [Connect a custom Databricks app to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling)
- The connection settings come from `PGHOST`, `PGDATABASE`, `PGUSER`, `PGPORT`, and `PGSSLMODE`. Generating a database credential also requires the Lakebase endpoint resource name (`projects/.../branches/.../endpoints/...`), conventionally exposed to the app as `ENDPOINT_NAME`. No static database password is needed or should be committed. [Connect a custom Databricks app to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling)
- The Databricks Apps proxy forwards identity-related headers including `X-Forwarded-Preferred-Username`, `X-Forwarded-User`, and `X-Forwarded-Email`. These headers exist only when the app runs inside Databricks Apps; local testing must simulate them or supply a fallback. [Access HTTP headers passed to Databricks apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/http-headers)

## Verified Git-backed deployment behavior

- Databricks Apps can deploy directly from a Git repository and reads the configured branch, tag, or commit on each deployment. GitHub, GitLab, Bitbucket, Azure DevOps, and AWS CodeCommit are supported providers. [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)
- Public repositories do not require a Git credential. Private repositories require a credential for the app service principal. [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)
- GitHub automatic deployment is a Beta feature that requires a private repository, the Databricks GitHub app, and a Git credential for the app service principal. Public repositories can still be deployed manually without a Git credential. [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)

## Project decisions

These are implementation choices, not Databricks platform requirements:

- Use a public GitHub repository named `ai-support-app` with `main` as the deployment branch. Keep source versioning and Databricks deployment pointed at the same canonical repository.
- Use manual deployment/redeployment from `main` so each bootcamp checkpoint is intentional and because Databricks does not support automatic GitHub deployment from a public repository.
- Build a Streamlit application with a separate repository/database layer rather than embedding SQL throughout UI code.
- Use Lakebase as the sole runtime datastore. Do not add hard-coded ticket data or a local fallback database.
- Have the app run an idempotent, transactional initialization that owns a `support` schema, creates `tickets` and `ticket_messages`, their constraints, foreign key, and query indexes, and seeds sample rows only when the tables are empty.
- Model ticket status and priority as constrained values. Validate required fields, allowed values, and practical text lengths in application code, then retain database constraints as the final integrity boundary.
- Use parameterized PostgreSQL queries for all user-supplied values.
- Populate `created_by` and message `author` from the forwarded Databricks user email when deployed. Permit an explicit typed identity only for local development where the forwarded headers do not exist.
- Use OAuth credential generation and rotation; never store a database password, Databricks token, GitHub token, API key, `.env` file, or other secret in Git or the submission ZIP.
- Show ticket counts/statistics, filter by status, display a selected ticket's messages chronologically, and provide forms for ticket creation, new messages, and status changes.
- Keep deletion out of version one to reduce accidental data loss and keep the graded persistence workflow focused.

## Verification and submission decisions

- Automated tests will cover validation, identity fallback, status changes, and repository behavior with mocked database connections. Syntax checks and the full test suite should run before committing.
- Manual deployed verification must prove that existing Lakebase tickets load, a new ticket can be created, a message can be added, a status can be changed, and all three mutations survive a browser refresh.
- Use the Lakebase Tables view or SQL Editor to verify sample rows and the `ticket_messages.ticket_id` foreign key. Databricks documents the Tables view and SQL Editor as direct ways to inspect app-written Lakebase data. [Using Lakebase with Databricks Apps](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps)
- Restart the app immediately before final verification or grading if its 24-hour Free Edition runtime has elapsed.
- Final deliverables are the deployed App URL, a clean source ZIP that excludes Git metadata/caches/secrets, the deployed-app screenshot, the Lakebase schema/sample-data screenshot, a submission checklist, and the required 3–5 sentence reflection.

## Local environment observations

These observations describe the local machine and are not claims from Databricks documentation:

- The pre-implementation workspace was effectively empty and was not a Git repository. During implementation, scaffolding may appear, so future sessions should inspect current state rather than treating this snapshot as permanent.
- The Databricks CLI was not installed or available on `PATH` at the time of inspection.
- GitHub CLI was installed at `/opt/homebrew/bin/gh`, but the active `cookx775` credential was invalid. `gh auth login -h github.com` is required before repository creation or push.

## Implementation outcome (2026-08-04)

- GitHub CLI authentication for `cookx775` was restored, the workspace was initialized as a Git repository, and `main` was pushed to the public [cookx775/ai-support-app](https://github.com/cookx775/ai-support-app) repository.
- The existing Free Edition Lakebase project `new-database` was reused because the account is limited to one project. The app uses the `production` branch, `databricks_postgres` database, and endpoint resource name `projects/new-database/branches/production/endpoints/primary`.
- A Databricks App named `ai-support-app` was created, attached to Lakebase with **Can connect and create**, and manually deployed from public GitHub branch `main`. Its URL is https://ai-support-app-7474657586545240.aws.databricksapps.com.
- Deployed verification created ticket `#4`, added a message, changed its status to `in_progress`, and confirmed all values remained after a full browser refresh. The app correctly used the signed-in identity supplied by Databricks.
- A direct Lakebase query returned four tickets and seven messages. A catalog query confirmed `ticket_messages_ticket_id_fkey` as `FOREIGN KEY (ticket_id) REFERENCES support.tickets(ticket_id)`.
- The final automated verification passed 22 tests plus Ruff and Git whitespace checks. Submission screenshots are stored under `submissions/homework-1/`.
- **Graded result: 100/100.** Homework 1 is closed; this document is the frozen Day 1 record and should not be revised except to correct an error. Platform findings from later assignments belong in their own research documents.

## First-party references

- [Databricks Free Edition limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- [Using Lakebase with Databricks Apps](https://docs.databricks.com/aws/en/oltp/projects/databricks-apps)
- [Add a Lakebase resource to a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/lakebase)
- [Deploy a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)
- [Connect a custom Databricks app to Lakebase](https://docs.databricks.com/aws/en/oltp/projects/tutorial-databricks-apps-autoscaling)
- [Access HTTP headers passed to Databricks apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/http-headers)
