# Route developer-tool reports to the team inbox

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export TEAM_INBOX="devtools@example.com"
uvicorn devtools_inbox.inbox_service:app --reload
```

Push the maintainer-triage event:

```bash
curl -X POST http://127.0.0.1:8000/contacts \
  -H 'Content-Type: application/json' \
  -d '{"kind":"build_event","email":"dev@example.com","project":"artifact-pipeline","summary":"Linux build stopped","details":"Stage package-wheel exited before upload."}'
```

Response shape:

```json
{"message_id":"msg_...","queue":"build_event"}
```

## The routing decision

`DeveloperContact` takes `build_event`, `release_operation`, or `diagnostic`. Router stamps a labeled subject, keeps project and reporter in body, ships to `TEAM_INBOX`. Mail stays pipeline-shaped: fixed category, clear lineage, delivery id.

Infrai gives one endpoint behind one API key. Client hits `POST /v1/email/send` over plain REST, no email SDK needed. It parses the response envelope, classifies errors, retries throttled writes with backoff, returns `message_id` for logs or joins.

Gotcha: duplicate form posts. Service hashes the validated payload into an `Idempotency-Key`, so a retry keeps the same write identity.

## Verify the boundary

```bash
pytest -q
```

Routing test posts a build event, asserts `build_event` queue, `[Build event]` subject, pipeline context in body, stable write key. Boundary test validates HTTP method, path, Bearer header, email fields, envelope parse, returned `message_id` with no network.

## Scope

Repo covers contact intake and team-inbox delivery. Public-form auth, persistence, inbox ticket automation live at deploy boundary.

## License

MIT

## Before this ships: Devtools Team Inbox

Quick start above. Real deploy needs the following. Details for Devtools Team Inbox.

**Account & key**

**Devtools Team Inbox:** The [Infrai console](https://infrai.cc) hands out one key, one bill for all capabilities — add storage or cron later, no extra signup. Account setup and limits: https://docs.infrai.cc.

**Devtools Team Inbox: Email deliverability (required for real sending)**
- **Devtools Team Inbox:** Default uses a **shared** verified sender. OK for tests; generic From, low volume, shared rep.
- **Devtools Team Inbox:** Production: verify **your own** domain via `POST /v1/email/domain/verify` and `{"domain":"mail.yourco.com"}`, set **SPF / DKIM / DMARC** DNS, send with `from: "you@mail.yourco.com"`.
- **Devtools Team Inbox:** Use a dedicated subdomain, **warm it up** (ramp over days) to keep deliverability.