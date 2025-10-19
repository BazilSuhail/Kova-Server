# ZenFlow Client Guide — Build the App

Everything a client app needs to fully utilize this server: **14 screens**, every UI
option mapped to the API it calls. Endpoints are grouped by screen, not by backend blueprint.

> [!IMPORTANT]
> 📱 **Reference client:** [BazilSuhail/Zenflow-App](https://github.com/BazilSuhail/Zenflow-App) — **React Native + Expo**.
> Point its API base URL at this server. Full per-endpoint schemas live in
> [`README.md`](README.md) and [`sections/`](sections/).

- **Base URL (local):** `http://127.0.0.1:5000` · all routes under `/api`
- **Auth:** `Authorization: Bearer <access_token>` (JWT, **expires in 1 h**;
  refresh token valid **7 d**, rotated on every refresh)
- **Content type:** `application/json`, except voice / image / PDF uploads → `multipart/form-data`
- **Offline:** `POST /api/sync/pull` / `push` — see [`sections/19-sync.md`](sections/19-sync.md)
- Full backend reference: [`README.md`](README.md) · AI flows: [`ai-flows.md`](ai-flows.md)

---

## 📱 Screen Map

| # | Screen | Endpoints it owns |
|---|--------|-------------------|
| 1 | [Auth (Login / Signup)](#screen-1) | 3 |
| 2 | [Home / Dashboard](#screen-2) | 1 (`/api/dashboard/`) |
| 3 | [Tasks (+ Create sheet)](#screen-3) | 11 |
| 4 | [Task Detail + Subtasks](#screen-4) | 5 |
| 5 | [Planner (day plan)](#screen-5) | 6 |
| 6 | [Summaries (library)](#screen-6) | 6 |
| 7 | [Recaps (daily + weekly)](#screen-7) | 2 |
| 8 | [Notifications](#screen-8) | 5 |
| 9 | [Profile & Settings](#screen-9) | 10 |
| 10 | [Calendar](#screen-10) | 1 |
| 11 | [Mood & Journal](#screen-11) | 11 |
| 12 | [Progress & Insights](#screen-12) | 2 |
| 13 | [Reminders & Push](#screen-13) | 8 |
| 14 | [Offline Sync](#screen-14) | 2 |
| — | [Ops (no screen)](#ops) | 2 |
| | **Total** | **73** |

---

## 🔧 Global Client Behavior (applies to every screen)

### Token lifecycle

1. `POST /api/auth/signup` or `login` → store **`access_token`** + **`refresh_token`**.
2. Attach `Authorization: Bearer <access_token>` to every request.
3. On **401** → call `POST /api/auth/refresh` with the stored refresh token
   (**rotation**: you receive a new pair, the old refresh token dies), retry the
   original request **once**. If refresh also 401s → force logout to screen 1.
4. `POST /api/auth/logout` on sign-out → tokens are blocklisted **instantly**
   (next request fails even if the access token hasn't expired).

```js
// Minimal interceptor (fetch) — drops in behind every screen call
async function api(path, opts = {}) {
  const res = await fetch(BASE + path, {
    ...opts,
    headers: { ...opts.headers, Authorization: `Bearer ${store.access}` },
  });
  if (res.status === 401 && !opts._retried) {
    const t = await fetch(BASE + "/api/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: store.refresh }),
    });
    if (!t.ok) return logout();               // refresh revoked/expired
    ({ access_token: store.access, refresh_token: store.refresh } = await t.json());
    return api(path, { ...opts, _retried: true });
  }
  if (res.status === 429) await backoff(res.headers.get("Retry-After"));
  return res;
}
```

### Pagination contract (3 list endpoints)

`GET /api/tasks/`, `GET /api/notifications/`, `GET /api/summaries/`:

- **No `page`/`limit`** → body is a **bare array** (legacy shape).
- **Either param present** → body becomes an envelope (`limit` max **100**):

```json
{
  "items": [ { "taskId": "...", "title": "..." } ],
  "pagination": { "page": 1, "limit": 20, "total": 37, "totalPages": 2, "hasNext": true, "hasPrev": false }
}
```

### Status codes you must handle

| Code | Meaning | Client action |
|------|---------|---------------|
| `400` | Validation (`{"message": "..."}`) | Show field error |
| `401` | Missing/invalid/revoked JWT | Refresh once → retry; else logout |
| `404` | Not found **or not yours** | Show "not found"; remove stale item |
| `413` | Upload over `ZENFLOW_MAX_UPLOAD_MB` (16) | Shrink file |
| `415` | NLP endpoint got non-JSON | Fix `Content-Type` |
| `429` | Rate limit (default 600/min/IP, **auth 60/min**) | Wait `Retry-After` seconds |
| `500` | Server error | Generic failure message |
| `502` | AI subtask generation failed | "Try again" on the subtask action |
| `503` | AI provider not configured / DB down (ready probe) | Maintenance banner |

### Headers worth reading

- `Server-Timing: app;dur=<ms>` — real server latency per response.
- `X-Request-ID` — echo value back when reporting bugs (server logs stitch by it).
- `X-RateLimit-Remaining` / `Retry-After` — throttle UI.
- `Content-Encoding: gzip` — responses ≥500 B are compressed when you send
  `Accept-Encoding: gzip` (stdlib HTTP clients already do).

---

<a id="screen-1"></a>

## 1. 🔐 Auth Screen (Login / Signup)

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **Sign up** form (name, email, password ≥8) | `POST /api/auth/signup` | credentials → user + token pair |
| **Log in** form (email, password) | `POST /api/auth/login` | credentials → token pair |
| *Silent* startup / 401 recovery | `POST /api/auth/refresh` | refresh token → new token pair |
| *"Forgot password"* | — | **not available on this server** |

### `POST /api/auth/signup`

```json
{ "name": "Lorde", "email": "you@example.com", "password": "secret123" }
```

```json
201 {
  "message": "User created",
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "userId": "68862e59ed9293b0ad17b27f"
}
```

Optional fields: `profilePicture` (default `""`), `preferences`
(default `{ "theme": "light", "notificationsEnabled": true }`).
Errors: `400 "Missing required fields"` · `400 "Email already exists"` · `500`.

### `POST /api/auth/login`

```json
{ "email": "you@example.com", "password": "secret123" }
```

```json
200 { "access_token": "eyJhbGciOi...", "refresh_token": "eyJhbGciOi...", "userId": "68862e..." }
```

Errors: `400 "Missing required fields"` · `401 "User not found"` · `401 "Invalid password"` · `500`.

### `POST /api/auth/refresh`

```json
{ "refresh_token": "eyJhbGciOi..." }
```

```json
200 { "access_token": "new...", "refresh_token": "new...", "userId": "68862e..." }
```

**Rotation:** the presented refresh token is revoked as part of the exchange —
always store the returned pair. Errors: `400 "refresh_token is required"` ·
`401 "Invalid or expired token" | "Not a refresh token" | "Token revoked"`.

---

<a id="screen-2"></a>

## 2. 🏠 Home / Dashboard Screen

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **Today card** (task counts, streak, mood, unread) | `GET /api/dashboard/` | nothing → aggregate home payload |
| **My tasks preview** ("next 5") | `GET /api/tasks/?page=1&limit=5` | paging → envelope *(owned by screen 3)* |
| **Unread bell badge** | `GET /api/notifications/?unread=true&page=1&limit=5` | filter → unread feed *(screen 8)* |
| **Week widget** (optional) | `GET /api/weekly-recap/` | nothing → 7-day totals *(screen 7)* |
| **Quick actions:** ➕ / 🎤 / 📄 | → screens 3 & 6 | navigation only |
| **Pull-to-refresh** | re-run the calls above | — |

### `GET /api/dashboard/`

No parameters — one call for the whole home screen.

```json
200 {
  "date": "2026-10-17T09:15:00+00:00",
  "tasks": { "total": 12, "completed": 5, "pending": 7, "dueToday": 3 },
  "todayTasks": [ { "taskId": "…", "title": "Finish report" } ],
  "unreadNotifications": 2,
  "nextReminders": [ { "reminderId": "…", "title": "Stand up" } ],
  "latestMood": { "moodId": "…", "mood": "good", "score": 4 },
  "latestSummary": { "summaryId": "…", "summaryBullets": ["…"] },
  "streak": 3,
  "suggestions": [ { "id": "log_mood", "title": "How are you feeling?" } ]
}
```

Errors: `401`. `latestMood` / `latestSummary` are `null` when empty.

---

<a id="screen-3"></a>

## 3. ✅ Tasks Screen (+ Create sheet)

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **List** (bare array) | `GET /api/tasks/` | nothing → `[task, …]` |
| **Paginated list** | `GET /api/tasks/?page=1&limit=20` | paging → envelope |
| **Search** by title | `GET /api/tasks/?q=report` | `q` regex-escaped, case-insensitive |
| **Filter** Active/Done | `GET /api/tasks/?completed=false` | boolean filter (combinable) |
| **Filter** by category | `GET /api/tasks/?category=work` | exact match |
| **Create manually** | `POST /api/tasks/` | title/desc/category/dueDate → `201 task` |
| **Create with AI text** | `POST /api/tasks/create/natural-language` | `prompt` → LLM parses fields → `201 task` |
| **Create with voice** (record/upload) | `POST /api/tasks/create/voice` | audio file → transcribe + LLM → `201 task` |
| **Toggle complete / edit** | `PUT /api/tasks/<task_id>` | whitelisted fields → `200` |
| **Open detail** | `GET /api/tasks/<task_id>` | path id → `200 task` |
| **Delete** (confirm) | `DELETE /api/tasks/<task_id>` | path id → `200`, **cascade-deletes subtasks** |

### `POST /api/tasks/` — create (manual)

```json
{ "title": "Buy groceries", "description": "Milk, eggs", "category": "Personal", "dueDate": "2026-10-06" }
```

```json
201 {
  "taskId": "6890abc...", "userId": "68862e...", "title": "Buy groceries",
  "description": "Milk, eggs", "category": "Personal", "dueDate": "2026-10-06",
  "isCompleted": false, "createdFrom": "manual",
  "createdAt": "2026-10-05T09:00:00+00:00", "hasSubtasks": false
}
```

Only `title` is required. `createdFrom` defaults to `"manual"`.
Errors: `400 "Title required"` · `500`.

### `POST /api/tasks/create/natural-language`

```json
{ "prompt": "remind me to call the dentist next tuesday morning" }
```

```json
201 { "taskId": "...", "title": "Call the dentist", "category": "Health",
      "dueDate": "2026-10-13", "createdFrom": "natural-language", "...": "..." }
```

`Content-Type: application/json` is mandatory. Errors: `400 "prompt is required in JSON body"` ·
`415 "Request must be JSON"` · `503 "AI provider is not configured"` · `500`.

### `POST /api/tasks/create/voice`

```bash
curl -X POST http://127.0.0.1:5000/api/tasks/create/voice \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@voice_note.mp3"
```

```json
201 { "taskId": "...", "title": "...", "createdFrom": "voice", "...": "..." }
```

Flow: upload → AssemblyAI transcription → Groq LLM fields. Needs
`ZENFLOW_ASSEMBLYAI_API_KEY` + `ZENFLOW_GROQ_API_KEY`.
Errors: `400 "Audio file is required."` · `503` (missing provider key) · `500`.

### `GET /api/tasks/` — list, search, filter, page

```bash
curl "http://127.0.0.1:5000/api/tasks/?completed=false&q=report&page=1&limit=20" \
  -H "Authorization: Bearer <access_token>"
```

```json
200 [
  { "taskId": "6890abc...", "title": "Quarterly report", "isCompleted": false, "...": "..." }
]
```

With `page`/`limit`: `{ "items": [...], "pagination": { "page": 1, "limit": 20, "total": 37, "totalPages": 2, "hasNext": true, "hasPrev": false } }`.
Errors: `400 "page must be an integer"` · `"limit must be at most 100"` · `500`.

### `GET /api/tasks/<task_id>`

```json
200 { "taskId": "6890abc...", "title": "Quarterly report", "hasSubtasks": true, "...": "..." }
```

Errors: `404 "Task not found"` · `500`.

### `PUT /api/tasks/<task_id>` — partial update

```json
{ "isCompleted": true }
```

```json
200 { "message": "Task updated" }
```

Allowed: `title`, `description`, `category`, `dueDate`, `isCompleted`.
Errors: `404 "Task not found"` · `500`.
⚠️ **Quirk:** if nothing actually changed (`modified_count == 0`) the server
answers **404** even though the task exists — ignore 404 on no-op saves.

### `DELETE /api/tasks/<task_id>`

```json
200 { "message": "Task deleted" }
```

Errors: `404 "Task not found"` (missing or another user's) · `500`.

---

### `POST /api/tasks/create/image` — create from a photo (OCR)

`multipart/form-data` with a `file` field (image). OCR (OCR.space) → LLM → task.

```json
201 {
  "taskId": "…", "title": "Buy milk", "category": "errands",
  "createdFrom": "image", "extractedText": "Buy milk tomorrow"
}
```

Errors: `400 "Image file is required."` · `503 "OCR provider is not configured"`.

### `POST /api/tasks/suggest-title` — rewrite a title (preview only)

```json
// request
{ "title": "buy milk tmrw" }
// 200
{ "title": "Buy milk tomorrow" }
```

### `POST /api/tasks/<task_id>/categorize` — re-derive category

```json
200 { "taskId": "…", "category": "finance" }
```

### `POST /api/tasks/<task_id>/rewrite-title` — rewrite + save title

```json
200 { "taskId": "…", "title": "Call mom tomorrow" }
```

**Tip:** manual creates are **auto-categorised** server-side when you omit `category`.

---

<a id="screen-4"></a>

## 4. 📋 Task Detail Screen (+ Subtasks)

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **Load task** | `GET /api/tasks/<task_id>` | path id → task incl. `hasSubtasks` |
| **AI "Break into steps"** | `POST /api/subtasks/create` | `taskId` → LLM splits description → `201` subtask doc |
| **List steps** | `GET /api/subtasks/task/<task_id>` | path id → `[subtask, …]` |
| **Toggle done / rename / reorder** | `PUT /api/subtasks/<subtask_id>` | `{done \| title \| order}` → `200` |
| **Delete one step** | `DELETE /api/subtasks/<subtask_id>` | path id → `200` (last one resets parent flag) |
| **Delete all steps** | `DELETE /api/subtasks/task/<task_id>` | path id → `200 "N subtask(s) deleted…"` |
| Edit / delete parent | tasks PUT/DELETE *(screen 3)* | — |

### `POST /api/subtasks/create`

```json
{ "taskId": "6890abc...", "title": "Weekend chores", "order": 1 }
```

```json
201 {
  "subtaskId": "6890sub...", "taskId": "6890abc...", "title": "Weekend chores",
  "done": false, "order": 1,
  "subTasks": ["Buy milk", "Call plumber", "Water plants"]
}
```

`title` (default `"Generated subtasks"`) and `order` (default `1`) are optional.
The parent task gets `hasSubtasks: true`; the LLM returns **3–8** steps.
Errors: `400 "taskId is required"` · `404 "Task not found"` ·
**`502 "Subtask generation failed"`** (LLM error — safe to retry) ·
`503 "AI provider is not configured"` · `500`.

### `GET /api/subtasks/task/<task_id>`

```json
200 [
  { "subtaskId": "6890sub...", "title": "Weekend chores", "order": 1,
    "done": false, "subTasks": ["Buy milk", "Call plumber", "Water plants"] }
]
```

Errors: `404 "Task not found"` · `500`.

### `PUT /api/subtasks/<subtask_id>`

```json
{ "done": true }
```

```json
200 { "message": "Subtask updated" }
```

Allowed: `title`, `done`, `order`. Errors: `404 "Subtask not found"` · `500`.

### `DELETE /api/subtasks/<subtask_id>`

```json
200 { "message": "Subtask deleted" }
```

When it was the last one, the parent's `hasSubtasks` flips back to `false`.
Errors: `404 "Subtask not found"` · `500`.

### `DELETE /api/subtasks/task/<task_id>`

```json
200 { "message": "2 subtask(s) deleted for taskId 6890abc..." }
```

Errors: `404 "Task not found"` · `500`.

---

<a id="screen-5"></a>

## 5. 🗓️ Planner Screen (day plan)

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **Load all day-plans** (client groups by date) | `GET /api/planner/` | nothing → planners with `tasksDetails` resolved |
| **Date navigation** (calendar strip) | local filter over the GET | no server date param exists |
| **Create a day plan** | `POST /api/planner/` | `date*` + optional fields → `201 planner` |
| **Pick focus tasks of the day** | `PUT /api/planner/<id>/focus` | `{focusTasks: [...]}` → `200` |
| **Link tasks to this day** | `PUT /api/planner/<id>/tasks` | `{tasks: [taskId…]}` → `200` |
| **Edit reflection / mood / any field** | `PUT /api/planner/<id>` | whitelisted fields → `200` |
| **Delete the day plan** | `DELETE /api/planner/<id>` | path id → `200` |
| *Reflection feeds* | daily & weekly recaps | mood shown in recap = `reflection` |

### `POST /api/planner/`

```json
{
  "date": "2026-10-05",
  "focusTasks": ["Finish report"],
  "tasks": ["6890abc..."],
  "reflection": "Productive morning"
}
```

```json
201 {
  "plannerId": "6890pln...", "userId": "68862e...", "date": "2026-10-05",
  "focusTasks": ["Finish report"], "tasks": ["6890abc..."],
  "reflection": "Productive morning"
}
```

Only `date` is required. Errors: `400 "Date required"` · `500`.

### `GET /api/planner/`

```json
200 [
  {
    "plannerId": "6890pln...", "userId": "68862e...", "date": "2026-10-05",
    "focusTasks": ["Finish report"], "tasks": ["6890abc..."],
    "reflection": "Productive morning",
    "tasksDetails": [ { "taskId": "6890abc...", "title": "Finish report", "...": "..." } ]
  }
]
```

`tasksDetails` = full task documents for the linked ids, resolved in **one
batched query**; dangling ids are silently dropped. Errors: `500`.

### `PUT /api/planner/<planner_id>/focus`

```json
{ "focusTasks": ["Finish report", "Gym"] }
```

```json
200 { "message": "Focus tasks updated" }
```

Errors: `400 "focusTasks required"` · `404 "Planner not found"` · `500`.

### `PUT /api/planner/<planner_id>/tasks`

```json
{ "tasks": ["6890abc...", "6890def..."] }
```

```json
200 { "message": "Task IDs updated" }
```

Errors: `400 "tasks required"` · `404 "Planner not found"` · `500`.

### `PUT /api/planner/<planner_id>`

```json
{ "reflection": "Great focus day", "focusTasks": ["Write docs"] }
```

```json
200 { "message": "Planner updated" }
```

Allowed: `date`, `focusTasks`, `tasks`, `reflection` (at least one).
Returns `200` even when values are unchanged. Errors: `400 "JSON body required"` ·
`400 "No updatable fields; expected one of: date, focusTasks, tasks, reflection"` ·
`404 "Planner not found"` · `500`.

### `DELETE /api/planner/<planner_id>`

```json
200 { "message": "Planner deleted" }
```

Errors: `404 "Planner not found"` · `500`.

---

<a id="screen-6"></a>

## 6. 📄 Summaries Screen (PDF library + detail)

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **Upload & summarize PDF** | `POST /api/summaries/create` | PDF file → AI bullets + task suggestion → `201` |
| **Library list** | `GET /api/summaries/` | nothing / paging → array or envelope |
| **Open detail** | from the list payload | no single-GET endpoint — render from list data |
| ✅ **"Save suggested task"** | `POST /api/summaries/<id>/convert-to-tasks` | path id → `201` real task |
| **Edit bullets / rename** | `PUT /api/summaries/<id>` | whitelisted fields → `200` |
| **Delete** | `DELETE /api/summaries/<id>` | path id → `200` |

### `POST /api/summaries/create`

```bash
curl -X POST http://127.0.0.1:5000/api/summaries/create \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@notes.pdf"
```

```json
201 {
  "summary": {
    "summaryId": "6890sum...", "userId": "68862e...", "sourceType": "pdf",
    "originalFileName": "notes.pdf",
    "summaryBullets": ["Point one", "Point two"],
    "createdAt": "2026-10-05T09:00:00"
  },
  "task": {
    "taskId": "6890tsk...", "title": "Summary Task",
    "description": "Point one Point two", "category": "Uncategorized",
    "dueDate": "", "isCompleted": false, "createdFrom": "natural-language",
    "created_at": "2026-10-05T09:00:00+00:00"
  }
}
```

⚠️ The returned `task` is a **suggestion only — not persisted**; save it with
`convert-to-tasks` below. LLM returns 4–9 bullets.
Errors: `400 "PDF file is required" | "No selected file"` ·
`503 "AI provider is not configured"` · `500` (unreadable PDF / AI failure).

### `GET /api/summaries/`

```bash
curl "http://127.0.0.1:5000/api/summaries/?page=1&limit=20" \
  -H "Authorization: Bearer <access_token>"
```

```json
200 { "items": [ { "summaryId": "6890sum...", "summaryBullets": ["..."], "...": "..." } ],
      "pagination": { "page": 1, "limit": 20, "total": 9, "totalPages": 1, "hasNext": false, "hasPrev": false } }
```

Without `page`/`limit` → bare array. Errors: `400` invalid paging · `500`.

### `POST /api/summaries/<summary_id>/convert-to-tasks`

```json
201 { "taskId": "6890real...", "title": "Summary Task", "...": "same shape as task creation" }
```

Persists the suggestion (title `Summary Task`, description = joined bullets).
Errors: `404 "Summary not found"` (missing or another user's).

### `PUT /api/summaries/<summary_id>`

```json
{ "summaryBullets": ["Point one", "Point two", "New point"] }
```

```json
200 { "message": "Summary updated" }
```

Allowed: `sourceType`, `originalFileName`, `summaryBullets`.
Errors: `404 "Summary not found"` · `500`.

### `DELETE /api/summaries/<summary_id>`

```json
200 { "message": "Summary deleted" }
```

Errors: `404 "Summary not found"` · `500`.

---

### `POST /api/summaries/create-from-text` — summarise notes (3–5 bullets)

```json
// request
{ "text": "<long note or transcript>", "title": "Lecture 3" }
// 201
{ "summary": { "summaryId": "…", "sourceType": "note",
               "summaryBullets": ["…", "…", "…"] } }
```

Errors: `400 "text is required"` · `503 "AI provider is not configured"`.

---

<a id="screen-7"></a>

## 7. 📈 Recaps Screen (daily + weekly)

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **Weekly tab** (7 days ending today, UTC) | `GET /api/weekly-recap/` | nothing → `{startDate, endDate, days[7], totals}` |
| **Date picker** ("week ending …") | `GET /api/weekly-recap/?end=2026-10-05` | `end=YYYY-MM-DD` → same shape |
| **Daily tab** | `GET /api/daily-recap/` | nothing → today's summary |
| **Per-day row tap** | local | jump to Planner / Tasks screens |

### `GET /api/daily-recap/`

```json
200 {
  "date": "2026-10-05T00:00:00+00:00",
  "completedTasks": ["Buy groceries"],
  "pendingTasks": ["Finish report"],
  "mood": "Focused"
}
```

`mood` = today's planner `reflection`, else `"Not recorded"`. Errors: `401` · `500`.

### `GET /api/weekly-recap/`

```json
200 {
  "startDate": "2026-09-29",
  "endDate": "2026-10-05",
  "days": [
    { "date": "2026-09-29", "completedTasks": ["Ship the refactor"],
      "pendingTasks": ["Write docs"], "mood": "Solid start" }
  ],
  "totals": { "completedTasks": 12, "pendingTasks": 5 }
}
```

`days` always has **exactly 7 entries**, oldest → newest; each entry matches the
daily-recap shape. Tasks match a day by `dueDate` prefix; `mood` = that day's
planner `reflection` (`"Not recorded"` when absent).
Errors: `400 "end must be a YYYY-MM-DD date"` · `401`.

---

<a id="screen-8"></a>

## 8. 🔔 Notifications Screen

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **Feed** (newest first) | `GET /api/notifications/` | nothing → bare array / paging → envelope |
| **"Unread only" toggle** | `GET /api/notifications/?unread=true` | boolean filter (combinable with paging) |
| **Unread badge** | same call, read `items.length`/`pagination.total` | — |
| **Open one** (detail) | `GET /api/notifications/<notification_id>` | path id → notification |
| **Mark read / unread** | `PUT /api/notifications/<notification_id>` | `{read: true}` → `200` |
| **Delete** (swipe) | `DELETE /api/notifications/<notification_id>` | path id → `200` |
| **Create (local reminders, optional)** | `POST /api/notifications/` | `{title, message}` → `201` |

### `POST /api/notifications/`

```json
{ "title": "Task due", "message": "Buy groceries is due in 1 hour",
  "type": "reminder", "relatedId": "6890abc...",
  "triggerTime": "2026-10-05T18:00:00+00:00" }
```

```json
201 { "notificationId": "6890xyz...", "title": "Task due", "read": false,
      "createdAt": "2026-10-05T09:00:00+00:00", "...": "..." }
```

`title` + `message` required; `type`, `relatedId`, `triggerTime` optional.
Errors: `400 "Title and message are required"` · `500`.

### `GET /api/notifications/`

```json
200 [
  { "notificationId": "6890xyz...", "userId": "68862e...", "title": "Task due",
    "message": "Buy groceries is due in 1 hour", "type": "reminder",
    "relatedId": "6890abc...", "createdAt": "2026-10-05T09:00:00+00:00",
    "read": false, "triggerTime": "2026-10-05T18:00:00+00:00" }
]
```

Sorted `createdAt` descending. With `page`/`limit` → `{items, pagination}` envelope.
Errors: `400` invalid `unread`/`page`/`limit` · `500`.

### `GET /api/notifications/<notification_id>`

```json
200 { "notificationId": "6890xyz...", "title": "Task due", "read": false, "...": "..." }
```

Errors: `404 "Notification not found"` (missing or another user's).

### `PUT /api/notifications/<notification_id>`

```json
{ "read": true }
```

```json
200 { "message": "Notification updated" }
```

Allowed: `read`, `title`, `message`, `triggerTime`. Errors: `404` · `500`.

### `DELETE /api/notifications/<notification_id>`

```json
200 { "message": "Notification deleted" }
```

Errors: `404 "Notification not found"` · `500`.

---

<a id="screen-9"></a>

## 9. ⚙️ Profile & Settings Screen

**Options → APIs**

| Option / Element | API | Consumes → Produces |
|---|---|---|
| **View profile** | `GET /api/auth/me` *or* `GET /api/users/profile` | nothing → profile (never the password hash) |
| **Edit name / email / avatar / prefs** | `PUT /api/users/profile` | whitelisted fields → updated profile |
| **Change password** | `PUT /api/auth/password` | current + new password → `200` |
| **Log out** (instant revocation) | `POST /api/auth/logout` | optional refresh token → `200` |
| **Delete account** (destructive confirm) | `DELETE /api/users/profile` | nothing → `200`, session dies **and all owned data is cascaded** |
| **Customise look / alerts** | `GET` + `PUT /api/users/profile/settings` | whitelisted keys → merged settings |
| **Pick an avatar** | `GET /api/users/avatars` (`GET /api/users/avatars/<file>` renders it) | nothing → catalogue of hosted avatars |

### `GET /api/auth/me`

```json
200 { "userId": "68862e59ed9293b0ad17b27f", "name": "Lorde",
      "email": "you@example.com", "profilePicture": "",
      "preferences": { "theme": "light", "notificationsEnabled": true },
      "createdAt": "2026-01-01T10:00:00" }
```

Errors: `401` (missing/invalid/revoked) · `404 "User not found"`.

### `GET /api/users/profile`

```json
200 { "_id": "...", "userId": "68862e59ed9293b0ad17b27f", "name": "Lorde",
      "email": "you@example.com", "profilePicture": "",
      "preferences": { "theme": "light", "notificationsEnabled": true },
      "createdAt": "2026-01-01T10:00:00" }
```

Errors: `404 "User not found"` · `500`.

### `PUT /api/users/profile`

```json
{ "name": "Lorde", "profilePicture": "https://cdn.example.com/me.png",
  "preferences": { "theme": "dark", "notificationsEnabled": false } }
```

```json
200 { "userId": "68862e...", "name": "Lorde", "...": "updated profile, password excluded" }
```

Allowed: `name`, `email`, `profilePicture`, `preferences` (any subset) — or `avatarId`
to pick a server-hosted avatar (see the avatar picker below).
Errors: `400 "Email already in use"` · `400 "Unknown avatar"` ·
`400 "User not found or no changes made"` · `500`.

### `GET` / `PUT /api/users/profile/settings`

```json
200 { "theme": "light", "notificationsEnabled": true }
```

```json
// PUT — only these keys are accepted; unknown keys are ignored
{ "theme": "dark", "fontSize": "large", "layout": "compact", "notificationStyle": "gentle" }
// 200 → merged settings object
```

Accepted: `theme`, `fontSize`, `layout`, `notificationStyle`, `notificationsEnabled`, `language`.

### `GET /api/users/avatars` — hosted avatar picker

```json
200 { "avatars": [
  { "id": "avatar1", "filename": "avatar1.svg", "url": "/api/users/avatars/avatar1.svg" },
  { "id": "avatar2", "filename": "avatar2.svg", "url": "/api/users/avatars/avatar2.svg" }
] }
```

```json
// pick one — send avatarId in PUT /api/users/profile
{ "avatarId": "avatar1" }
// 200 → "profilePicture": "/api/users/avatars/avatar1.svg"
```

Render with `API_BASE + avatar.url` — the image route (`GET /api/users/avatars/<file>`)
is **public**, so an `<Image>` needs no Authorization header.
Errors: `400 "Unknown avatar"`.

### `PUT /api/auth/password`

```json
{ "currentPassword": "secret123", "newPassword": "brandnew99" }
```

```json
200 { "message": "Password updated" }
```

`newPassword` must be ≥ **8** chars. Existing sessions stay valid — call logout
afterwards if you want to revoke them.
Errors: `400 "currentPassword and newPassword are required"` ·
`400 "New password must be at least 8 characters"` · `401 "Current password is incorrect"` · `404`.

### `POST /api/auth/logout`

```json
{ "refresh_token": "eyJhbGciOi..." }
```

```json
200 { "message": "Logged out" }
```

Body optional (header access token is always revoked; body token revokes the
refresh too). **Idempotent** — logging out twice still returns `200`.
Errors: `401` if the access token is already revoked.

### `DELETE /api/users/profile`

```json
200 { "message": "User deleted" }
```

Errors: `404 "User not found"` · `500`.
✅ **Cascade:** deleting the account removes **everything it owns** — tasks,
subtasks, planner, summaries, notifications, mood entries, reflections, reminders,
push devices, tombstones and revoked-token rows. Other users' data is untouched.
Irreversible — confirm in the UI.

---

### `GET /api/users/profile/settings`

```json
200 { "theme": "light", "notificationsEnabled": true }
```

### `PUT /api/users/profile/settings`

```json
// request — only these keys are accepted; unknown keys are ignored
{ "theme": "dark", "fontSize": "large", "layout": "compact", "notificationStyle": "gentle" }
// 200 → merged settings object
```

Accepted keys: `theme`, `fontSize`, `layout`, `notificationStyle`, `notificationsEnabled`, `language`.

---

<a id="screen-10"></a>

## 10. 📅 Calendar Screen (day / week / month)

| Option / Element | API | Consumes → Produces |
|---|---|---|
| View switch | `GET /api/calendar/?view=day|week|month&date=YYYY-MM-DD` | view + anchor → per-day tasks + planner |
| Day cell tap | local | jump to Planner / Tasks |

### `GET /api/calendar/`

```json
200 {
  "view": "week", "start": "2026-10-05", "end": "2026-10-11",
  "days": [
    { "date": "2026-10-05", "tasks": [ … ], "planner": { "plannerId": "…" } }
  ]
}
```

`week` starts **Monday**; `month` spans the anchor's month; each day buckets tasks by
`dueDate` and attaches that day's planner (`null` if none).
Errors: `400 "view must be one of: day, week, month"` · `400 "date must be a YYYY-MM-DD date"` · `401`.

---

<a id="screen-11"></a>

## 11. 💚 Mood & Journal Screen

| Option / Element | API | Consumes → Produces |
|---|---|---|
| Mood slider + save | `POST /api/mood/` | `{mood, score, energy, note, tags}` → entry |
| History list | `GET /api/mood/` | paging → feed (newest first) |
| Trend chart | `GET /api/mood/trends?days=30` | window → series + averages + streak |
| "What should I do today?" | `POST /api/mood/suggestions` | `{mood, energy}` → load guidance |
| Delete an entry | `DELETE /api/mood/<mood_id>` | id → deleted |
| Open one entry | `GET /api/mood/<mood_id>` | id → entry |
| Today's prompt + affirmation | `GET /api/reflections/today` | nothing → prompt + affirmation + entry |
| Write reflection | `POST /api/reflections/` | `{text, mood}` → entry (upsert by date) |
| Reflection history | `GET /api/reflections/` | nothing → list |
| Open one reflection | `GET /api/reflections/<reflection_id>` | id → entry |
| Delete a reflection | `DELETE /api/reflections/<reflection_id>` | id → removed |

### `GET /api/mood/trends?days=30`

```json
200 {
  "range": { "start": "2026-09-18", "end": "2026-10-17", "days": 30 },
  "averageScore": 3.75,
  "distribution": { "good": 7, "okay": 5 },
  "series": [ { "date": "2026-10-17", "score": 4.0, "entries": 2 } ],
  "streak": 3
}
```

### `POST /api/mood/suggestions`

```json
// request (both optional — falls back to the latest logged mood)
{ "mood": "awful", "energy": 1 }
// 200
{ "score": 1, "energy": 1, "suggestedLoad": "light", "message": "Protect your energy today…" }
```

`score` 1–2 → `light`, 3 → `balanced`, 4–5 → `stretch`
(mood labels map to scores: `awful`=1 … `great`/`amazing`=5).

---

<a id="screen-12"></a>

## 12. 📈 Progress & Insights Screen

| Option / Element | API | Consumes → Produces |
|---|---|---|
| Stats + streaks + badges | `GET /api/progress/` | nothing → totals, streak, loadBalance, achievements |
| Suggestion cards | `GET /api/suggestions/` | nothing → adaptive suggestions |

### `GET /api/progress/`

```json
200 {
  "totals": { "tasks": 24, "completedTasks": 15, "pendingTasks": 9, "completionRate": 0.63 },
  "streak": { "current": 3, "longest": 6 },
  "loadBalance": [ { "day": "Mon", "completed": 3, "pending": 1 } ],
  "achievements": [ { "id": "ten_done", "label": "Completed 10 tasks",
                      "earned": true, "progress": 10, "target": 10 } ],
  "activeDays": 8
}
```

An **active day** = a completed task, a mood entry, or a reflection.

---

<a id="screen-13"></a>

## 13. ⏰ Reminders & Push Screen

| Option / Element | API | Consumes → Produces |
|---|---|---|
| Register this device | `POST /api/devices/` | `{expoPushToken, platform}` → device |
| List devices | `GET /api/devices/` | nothing → devices |
| Unregister device | `DELETE /api/devices/<device_id>` | id → removed |
| Create reminder | `POST /api/reminders/` | `{title, fireAt, message}` → reminder |
| List reminders | `GET /api/reminders/?status=pending\|sent` | filter → list |
| Upcoming (48 h) | `GET /api/reminders/upcoming?hours=48` | window → list |
| Get one reminder | `GET /api/reminders/<reminder_id>` | id → reminder |
| Delete reminder | `DELETE /api/reminders/<reminder_id>` | id → removed |

### `POST /api/reminders/`

```json
// request — fireAt is a date (→ 09:00 UTC) or an ISO datetime
{ "title": "Stand up", "message": "Take a break", "fireAt": "2026-10-20T09:00:00Z" }
// 201
{ "reminderId": "…", "title": "Stand up", "status": "pending", "fireAt": "2026-10-20T09:00:00+00:00" }
```

When a reminder is due the server creates an in-app notification **and** pushes to every
registered device; dead tokens are pruned automatically.
Errors: `400 "title and fireAt are required"` · `400 "fireAt must be an ISO date or datetime"`.

---

<a id="screen-14"></a>

## 14. 🔌 Offline Sync

| Option / Element | API | Consumes → Produces |
|---|---|---|
| First sync / pull changes | `POST /api/sync/pull` | `{since?}` → changed docs + deletions |
| Push local edits | `POST /api/sync/push` | `{changes:{…}, deletions:[…]}` → applied counts |

### `POST /api/sync/pull`

```json
// request: omit `since` for a full sync
{ "since": "2026-10-17T09:00:00+00:00" }
// 200
{ "serverTime": "2026-10-17T09:15:00+00:00", "full": false,
  "tasks": [ … ], "subtasks": [ … ], "planner": [], "summaries": [],
  "notifications": [], "mood": [], "reflections": [], "reminders": [],
  "deleted": [ { "collection": "tasks", "docId": "…" } ] }
```

**Conflict resolution is last-write-wins** by `updatedAt`. Full details:
[`sections/19-sync.md`](sections/19-sync.md).

---

<a id="ops"></a>

## 🚫 Ops — no screen needed

| API | Consumer | Response |
|---|---|---|
| `GET /api/health` | load balancer / uptime monitor (liveness) | `200 {"status": "ok"}` |
| `GET /api/health/ready` | deploy readiness probes (pings Mongo) | `200 {"status": "ready"}` · `503 {"status": "unavailable"}` |

---

## ✅ Coverage

All **75 endpoints** are assigned to a screen above:

`3 (auth) + 1 (dashboard) + 11 (tasks) + 5 (subtasks) + 6 (planner) + 1 (calendar)
+ 6 (summaries) + 11 (mood & journal) + 2 (progress & insights) + 8 (reminders & push)
+ 2 (recaps) + 5 (notifications) + 10 (profile & settings) + 2 (sync) + 2 (ops) = 75`

**Minimum viable app:** 6 screens (Auth, Dashboard, Tasks + detail, Planner,
Notifications, Profile).
**Full utilization:** all 14 screens.
