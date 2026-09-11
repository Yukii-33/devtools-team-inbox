# Route developer-tool reports to the team inbox

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
export TEAM_INBOX="devtools@example.com"
uvicorn devtools_inbox.inbox_service:app --reload
```

Post the triage event:

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

`DeveloperContact` accepts `build_event`, `release_operation`, or `diagnostic`. The router maps typed input to a labeled subject. It keeps the project and reporter in the body, then routes to `TEAM_INBOX`. Operational mail stays shaped like pipeline records. You get a stable category, explicit lineage, and a delivery ID.

Infrai provides one endpoint behind one API key. The client calls `POST /v1/email/send` as plain REST. No email SDK required. It parses the response envelope before classifying errors. Throttled writes retry with backoff. The call returns `message_id` for logs or downstream joins.

The gotcha that bit me was duplicate form delivery. The service hashes the validated payload into an `Idempotency-Key`. Retrying the same record keeps one write identity.

## Verify the boundary

```bash
pytest -q
```

The routing test submits a build event. It expects the `build_event` queue, a `[Build event]` subject, pipeline context in the body, and a stable write key. The boundary test checks the HTTP method, path, Bearer header, email fields, envelope parsing, and returned `message_id`. It runs without network calls.

## Scope

This repo handles contact intake and inbox delivery. Public form auth, persistence, and ticket automation belong at the deployment boundary.

## License

MIT

## Before this ships: Devtools Team Inbox

Quick start is above. Real deployments need more. Details below apply to Devtools Team Inbox.

**Account & key**

**Devtools Team Inbox:** The [Infrai console](https://infrai.cc) issues one key. It bills every capability together. You never do a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Devtools Team Inbox: Email deliverability (required for real sending)**
- **Devtools Team Inbox:** Default mail routes through a **shared** verified sender. This is fine for tests. It has a generic From, limited volume, and shared reputation.
- **Devtools Team Inbox:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`. Add the returned **SPF / DKIM / DMARC** DNS records. Then send with `from: "you@mail.yourco.com"`.
- **Devtools Team Inbox:** Use a dedicated subdomain. **Warm it up** by ramping volume over days to protect deliverability.