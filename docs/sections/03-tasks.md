# 3. Tasks API — `/api/tasks`

> File: `app/api/tasks.py` · Blueprint: `tasks_bp` · **7 endpoints** · **All JWT-protected**

Task creation has **3 modes**: manual, natural-language (LLM), and voice (AssemblyAI + LLM).

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

## 3.4 `GET /api/tasks/` — List all tasks

- **Auth:** 🔒 JWT

**Responses:** `200` array of the current user's tasks · `500`

```bash
curl http://127.0.0.1:5000/api/tasks/ -H "Authorization: Bearer <access_token>"
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

**⚠️ Note:** subtasks of the deleted task are **not** cascade-deleted.
