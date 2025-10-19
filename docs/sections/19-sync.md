# 19. Sync API — `/api/sync`

> File: `app/api/sync.py` → `app/services/sync_service.py` · Blueprint: `sync_bp` · **2 endpoints** · **JWT-protected**

Offline-first sync: **delta pull** of everything changed since a cursor, plus a
**last-write-wins push** of client-side edits and deletions. Backed by `updatedAt` on every
document and the `tombstones` collection.

Synced collections: `tasks`, `subtasks`, `planner`, `summaries`, `notifications`, `mood`,
`reflections`, `reminders`.

---

## 19.1 `POST /api/sync/pull` — Delta download

- **Auth:** 🔒 JWT · **Content-Type:** `application/json`
- **Body:** `{ "since": "<iso timestamp>" }` — omit or `null` for a **full** sync.

**Response**

```json
{
  "serverTime": "2026-10-17T09:15:00+00:00",
  "full": false,
  "since": "2026-10-17T09:00:00+00:00",
  "tasks": [ { "taskId": "…", "title": "…", "updatedAt": "…" } ],
  "subtasks": [ { "subtaskId": "…", "taskId": "…", "title": "…", "updatedAt": "…" } ],
  "planner": [], "summaries": [], "notifications": [],
  "mood": [], "reflections": [], "reminders": [],
  "deleted": [
    { "userId": "…", "collection": "tasks", "docId": "…", "deletedAt": "…", "updatedAt": "…" }
  ]
}
```

**Notes**
- Returns only documents with `updatedAt > since` (all of them when `since` is omitted).
- `deleted[]` lists tombstones since `since` so the client can prune local rows.
- `full: true` signals a first sync — the client should **replace** its local store.

---

## 19.2 `POST /api/sync/push` — Upload offline changes

- **Auth:** 🔒 JWT · **Content-Type:** `application/json`

**Request body**

```json
{
  "changes": {
    "tasks": [ { "taskId": "client-1", "title": "Made offline", "isCompleted": false } ],
    "subtasks": [], "planner": [], "summaries": [],
    "notifications": [], "mood": [], "reflections": [], "reminders": [],
    "deletions": [ { "collection": "tasks", "id": "client-2" } ]
  }
}
```

**Response**

```json
{
  "applied": { "tasks": 1, "planner": 0, "summaries": 0, "notifications": 0,
               "mood": 0, "reflections": 0, "reminders": 0, "subtasks": 0, "deletions": 1 },
  "skipped": [],
  "serverTime": "2026-10-17T09:15:00+00:00"
}
```

**Semantics**
- Upsert by the collection's id field; `userId` is **forced to the caller** (no cross-user writes).
- **Conflict resolution — last-write-wins:** if the server copy has a newer `updatedAt` than the
  incoming document, the incoming write is skipped.
- Subtask pushes must reference a task the caller owns, otherwise the entry is reported in `skipped`.
- `deletions[]` removes the document (owner-scoped) and records a tombstone.

```bash
# full sync
curl -X POST http://127.0.0.1:5000/api/sync/pull \
  -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" -d '{}'

# push
curl -X POST http://127.0.0.1:5000/api/sync/push \
  -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" \
  -d '{"changes":{"tasks":[{"taskId":"client-1","title":"Made offline"}]}}'
```
