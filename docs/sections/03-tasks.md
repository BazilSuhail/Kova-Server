# 3. Tasks API — `/api/tasks`

> File: `app/api/tasks.py` · Blueprint: `tasks_bp` · **11 endpoints** · **All JWT-protected**

Task creation has **4 modes**: manual, natural-language (LLM), voice (AssemblyAI + LLM),
and camera/scan (OCR + LLM). Manual creates are **auto-categorised** locally (no key needed).

---

## 3.1 `POST /api/tasks/` — Create task (manual)

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

**Request body**

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `title` | string | ✅ | — |
| `description` | string | ❌ | `""` |
| `category` | string | ❌ | `""` |
| `dueDate` | string | ❌ | `""` |
| `createdFrom` | string | ❌ | `"manual"` |

**Responses:** `201` created task · `400 { "message": "Title required" }` · `500`

```json
{
  "taskId": "6890abc...",
  "userId": "68862e...",
  "title": "Buy groceries",
  "description": "Milk, eggs",
  "category": "Personal",
  "dueDate": "2026-10-06",
  "isCompleted": false,
  "createdFrom": "manual",
  "createdAt": "2026-10-05T09:00:00+00:00",
  "hasSubtasks": false
}
```

---

## 3.2 `POST /api/tasks/create/natural-language` — Create task from text prompt

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json` *(required — 415 otherwise)*
- **Flow:** `prompt` → Groq LLM (`generate_task_fields_from_llm`) → task fields

| Field | Type | Required |
|-------|------|----------|
| `prompt` | string | ✅ |

```json
{ "prompt": "remind me to call the dentist next tuesday morning" }
```

**Responses**

| Code | Body |
|------|------|
| `201` | task object, `createdFrom: "natural-language"` |
| `400` | `{ "message": "prompt is required in JSON body" }` |
| `415` | `{ "message": "Request must be JSON" }` |
| `500` | `{ "message": "Internal server error" }` |

---

## 3.3 `POST /api/tasks/create/voice` — Create task from audio

- **Auth:** 🔒 JWT
- **Content-Type:** `multipart/form-data`
- **Flow:** upload audio → AssemblyAI transcription → Groq LLM → task fields

| Field | Type | Required |
|-------|------|----------|
| `file` | audio file | ✅ |

```bash
curl -X POST http://127.0.0.1:5000/api/tasks/create/voice \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@voice_note.mp3"
```

**Responses:** `201` task (`createdFrom: "voice"`) · `400 { "message": "Audio file is required." }` · `500`
**Env required:** `ASSEMBLYAI_API_KEY`, `GROQ_API_KEY`

---

## 3.4 `GET /api/tasks/` — List tasks

- **Auth:** 🔒 JWT

**Query parameters (all optional)**

| Param | Type | Effect |
|-------|------|--------|
| `completed` | `true` / `false` | filter on `isCompleted` |
| `category` | string | exact category match |
| `q` | string | case-insensitive title substring |
| `page` | int ≥ 1 | switches response to the paged envelope (see below) |
| `limit` | int 1–100 | page size (default 50; used with `page`) |

Without `page`/`limit` the body is the **bare array** (legacy shape — no params
means no behavior change for existing clients):

**Responses:** `200` array of the current user's tasks · `400` invalid query
param (`page must be an integer`, `limit must be at most 100`, …) · `500`

```bash
curl http://127.0.0.1:5000/api/tasks/?completed=false&q=report \
  -H "Authorization: Bearer <access_token>"
```

With `?page=2&limit=20` the body becomes:

```json
{
  "items": [ { "...": "task" } ],
  "pagination": {
    "page": 2, "limit": 20, "total": 37,
    "totalPages": 2, "hasNext": false, "hasPrev": true
  }
}
```

---

## 3.5 `GET /api/tasks/<task_id>` — Get single task

- **Auth:** 🔒 JWT

**Responses:** `200` task · `404 { "message": "Task not found" }` · `500`

---

## 3.6 `PUT /api/tasks/<task_id>` — Update task

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

**Allowed fields:** `title`, `description`, `category`, `dueDate`, `isCompleted`

```json
{ "isCompleted": true }
```

**Responses:** `200 { "message": "Task updated" }` · `404 { "message": "Task not found" }` · `500`

> ⚠️ If nothing actually changed, `modified_count == 0` → returns **404** even though the task exists.

---

## 3.7 `DELETE /api/tasks/<task_id>` — Delete task

- **Auth:** 🔒 JWT

**Responses:** `200 { "message": "Task deleted" }` · `404 { "message": "Task not found" }` · `500`

**✅ Note:** deleting a task also **cascade-deletes its subtasks** (Sprint A — the
legacy implementation left orphaned subtask documents behind). Nothing happens when
the task does not exist or isn't yours. The deletion is recorded as a sync tombstone.

---

## 3.8 `POST /api/tasks/create/image` — Create task from a photo (OCR)

- **Auth:** 🔒 JWT · **Content-Type:** `multipart/form-data`
- **Form field:** `file` (image) — **required**

Pipeline: image → **OCR.space** text → **Groq** structured task.

**Responses**

| Code | Body |
|------|------|
| `201` | the created task, **plus** `extractedText` (OCR text, echoed, not persisted) |
| `400` | `{ "message": "Image file is required." }` \| `{ "message": "Failed to parse LLM response: …" }` |
| `503` | `{ "message": "OCR provider is not configured" }` (no `ZENFLOW_OCR_API_KEY`) |

```bash
curl -X POST http://127.0.0.1:5000/api/tasks/create/image \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@notes.jpg"
```

---

## 3.9 `POST /api/tasks/suggest-title` — Rewrite a title (no persist)

- **Auth:** 🔒 JWT · Body: `{ "title": "buy milk tmrw" }` (**required**)

Rewrites a vague title into a clear one. Uses the LLM when a key is configured, otherwise a
local heuristic (expands `tmrw`→`tomorrow`, `mtg`→`meeting`, capitalises, collapses spaces).

**Responses:** `200 { "title": "Buy milk tomorrow" }` · `400 { "message": "title is required" }`

---

## 3.10 `POST /api/tasks/<task_id>/categorize` — Re-derive category

- **Auth:** 🔒 JWT
- Re-derives and **persists** the task's category from a local keyword heuristic.

**Responses:** `200 { "taskId": "…", "category": "finance" }` · `404 { "message": "Task not found" }`

---

## 3.11 `POST /api/tasks/<task_id>/rewrite-title` — Rewrite + persist title

- **Auth:** 🔒 JWT
- Rewrites the task's title (same engine as §3.9) and saves it.

**Responses:** `200 { "taskId": "…", "title": "Call mom tomorrow" }` · `404 { "message": "Task not found" }`
