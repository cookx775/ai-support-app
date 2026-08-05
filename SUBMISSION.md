# Day 1 Homework Submission

## Deliverables

- **Databricks App URL:** _Add after deployment_
- **Source ZIP:** `ai-support-app.zip`
- **Deployed application screenshot:** _Attach after final verification_
- **Lakebase tables and sample-records screenshot:** _Attach after final verification_

## Verification checklist

- [ ] Existing tickets load from Lakebase.
- [ ] A new ticket can be created.
- [ ] A message can be added to an existing ticket.
- [ ] A ticket's status can be updated.
- [ ] All changes remain after refreshing the app.
- [ ] `ticket_messages.ticket_id` has a foreign key to `tickets.ticket_id`.
- [ ] The database contains at least three tickets and two messages per ticket.
- [ ] Screenshots contain no credentials, tokens, or secret values.

## Reflection

The most difficult part was connecting the app to Lakebase with the correct service-principal permissions and renewable OAuth database credentials. Lakebase differs from a traditional analytics table because it is PostgreSQL designed for low-latency transactional reads and writes, with relational constraints and immediate row-level updates rather than batch-oriented analytical processing. Its persistence also remains independent of the Databricks App lifecycle, which makes it appropriate for operational application state. The next feature I would add is ownership and assignment routing so support teams can track responsibility and response time for each ticket.

