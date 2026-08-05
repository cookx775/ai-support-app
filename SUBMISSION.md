# Day 1 Homework Submission

## Deliverables

- **Databricks App URL:** https://ai-support-app-7474657586545240.aws.databricksapps.com
- **Complete upload archive:** `ai-support-app-submission.zip` (source code included)
- **Deployed application screenshot:** `docs/submission/deployed-application.jpg`
- **Lakebase tables and sample-records screenshot:** `docs/submission/lakebase-tables-and-records.jpg`

## Verification checklist

- [x] Existing tickets load from Lakebase.
- [x] A new ticket can be created.
- [x] A message can be added to an existing ticket.
- [x] A ticket's status can be updated.
- [x] All changes remain after refreshing the app.
- [x] `ticket_messages.ticket_id` has a foreign key to `tickets.ticket_id`.
- [x] The database contains at least three tickets and two messages per seeded ticket.
- [x] Screenshots contain no credentials, tokens, or secret values.

## Reflection

The most difficult part was configuring the Lakebase connection correctly because the OAuth credential request requires the endpoint's resource name, not the UUID-style identifiers displayed elsewhere in the Lakebase interface. Lakebase differs from a traditional analytics table because it is PostgreSQL designed for low-latency transactional reads and writes, relational constraints, and immediate row-level updates rather than batch-oriented analytical processing. Its data also persists independently of the Databricks App lifecycle, which makes it appropriate for operational application state. The next feature I would add is ownership and assignment routing so support teams can track responsibility and response time for each ticket.
