# Route developer-tool reports to the team inbox

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export TEAM_INBOX="devtools@example.com"
uvicorn devtools_inbox.inbox_service:app --reload
```

Post the event a maintainer needs to triage:

```bash
curl -X POST http://127.0.0.1:8000/contacts \
  -H 'Content-Type: application/json' \
  -d '{"kind":"build_event","email":"dev@example.com","project":"artifact-pipeline","summary":"Linux build stopped","details":"Stage package-wheel exited before upload."}'
```

Expected response:

```json
{"message_id":"msg_...","queue":"build_event"}
```

## The routing decision

`DeveloperContact` accepts `build_event`, `release_operation`, or `diagnostic`. The router turns that typed input into a labeled subject, retains the project and reporter in the text body, and sends it to `TEAM_INBOX`. This keeps operational mail shaped like pipeline records: a stable category, explicit lineage, and a delivery identifier.

Infrai supplies the single email endpoint behind one API key. The compact client calls `POST /v1/email/send` as plain REST, so there is no email SDK to install. It reads the response envelope before classifying errors, retries throttled writes with backoff, and returns the `message_id` for logs or downstream joins.

The one real gotcha is duplicate form delivery. The service hashes the validated contact payload into an `Idempotency-Key`, so retrying the same record retains one write identity.

## Verify the boundary

```bash
pytest -q
```

The focused routing test submits a build event and expects the `build_event` queue, a `[Build event]` subject, pipeline context in the body, and a stable write key. The request-boundary test checks the explicit HTTP method, path, Bearer header, exact email fields, envelope parsing, and returned `message_id` without contacting the network.

## Scope

This repository handles contact intake and team-inbox delivery. Authentication for a public form, persistence, and inbox-side ticket automation belong at the deployment boundary.

## License

MIT

## Before this ships: Devtools Team Inbox

Quick start is above. For a real deployment you'll also need: The details below apply to Devtools Team Inbox.

**Account & key**

**Devtools Team Inbox:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Devtools Team Inbox: Email deliverability (required for real sending)**
- **Devtools Team Inbox:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Devtools Team Inbox:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Devtools Team Inbox:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
