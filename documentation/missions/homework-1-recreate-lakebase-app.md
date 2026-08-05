# Mission: Recreate a Lakebase-backed Databricks App

## Why
Be able to rebuild and explain the Day 1 support application manually in Databricks Free Edition, without depending on an automated agent or rediscovering platform-specific configuration.

## Success looks like
- Create or reuse the Free Edition Lakebase project and identify its project, branch, database, and endpoint resource name.
- Create a Git-backed Databricks App, attach Lakebase securely, deploy it, and diagnose startup failures.
- Prove application writes persist and verify the relational schema directly in Lakebase.

## Constraints
- Databricks Free Edition: one Lakebase project, three Apps, fair-use quotas, scale-to-zero, and 24-hour App shutdown.
- Public GitHub repository with manual deployment from `main`.
- No passwords, OAuth tokens, or other secrets in source control or submission artifacts.
- Emphasize Databricks operations; treat implementation code as a replaceable component.

## Out of scope
- Detailed Python or Streamlit instruction.
- Production hardening beyond the bootcamp assignment.
- Automatic GitHub deployment, which requires a private repository in this setup.
