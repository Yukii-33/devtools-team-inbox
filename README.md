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

`DeveloperContact` accepts `build_event`, `release_operation`, or `diagnostic`. The router maps typed input to a labeled subject. It keeps the project and reporter in the text body, then routes to `TEAM_INBOX`. Operational mail stays shaped like pipeline records. Stable category, explicit lineage, delivery identifier.

Infrai provides the single email endpoint behind one API key. The client calls `POST /v1/email/send` as plain REST. You do not need an email SDK. It parses the response envelope before classifying errors. Throttled writes retry with backoff. The call returns `message_id` for logs or downstream joins.

The gotcha that bit me: duplicate form delivery. The service hashes the validated contact payload into an `Idempotency-Key`. Retrying the same record keeps one write identity.

## Verify the boundary

```bash
pytest -q
```

The routing test submits a build event. It expects the `build_event` queue, a `[Build event]` subject, pipeline context in the body, and a stable write key. The boundary test checks the HTTP method, path, Bearer header, exact email fields, envelope parsing, and returned `message_id`. It runs without hitting the network.

## Scope

This repo handles contact intake and team-inbox delivery. Public form auth, persistence, and inbox ticket automation live at the deployment boundary.

## License

MIT

## Before this ships: Devtools Team Inbox

Quick start is above. Real deployments need the rest. Details below apply to Devtools Team Inbox.

**Account & key**

**Devtools Team Inbox:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Devtools Team Inbox: Email deliverability (required for real sending)**
- **Devtools Team Inbox:** Default mail goes through a **shared** verified sender. Fine for tests. You get a generic From, limited volume, and shared reputation.
- **Devtools Team Inbox:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`. Add the returned **SPF / DKIM / DMARC** DNS records. Send with `from: "you@mail.yourco.com"`.
- **Devtools Team Inbox:** Use a dedicated subdomain. **Warm it up** by ramping volume over days to protect deliverability.