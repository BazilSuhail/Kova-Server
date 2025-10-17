# 7. Summaries API — `/api/summaries`

> File: `app/api/summaries.py` · Blueprint: `summaries_bp` · **4 endpoints** · **All JWT-protected**

Upload a **PDF** → text extraction → LLM → bullet summary (plus a derived task object).

---

## 7.1 `POST /api/summaries/create` — Summarize a PDF

- **Auth:** 🔒 JWT
- **Content-Type:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `file` | PDF file | ✅ |

```bash
curl -X POST http://127.0.0.1:5000/api/summaries/create \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@notes.pdf"
```

**Flow:** `extract_pdf_text(file)` → `generate_summary_from_llm(text)` (Groq) → insert into `summaries`.

**Responses**

| Code | Body |
|------|------|
| `201` | `{ "summary": {...}, "task": {...} }` (see shape below) |
| `400` | `{ "message": "PDF file is required" }` \| `{ "message": "No selected file" }` |
| `500` | `{ "message": "Internal server error" }` |

```json
{
  "summary": {
    "summaryId": "6890sum...",
    "userId": "68862e...",
    "sourceType": "pdf",
    "originalFileName": "notes.pdf",
    "summaryBullets": ["Point one", "Point two"],
    "createdAt": "2026-10-05T09:00:00"
  },
  "task": {
    "taskId": "6890tsk...",
    "title": "Summary Task",
    "description": "Point one Point two",
    "category": "Uncategorized",
    "dueDate": "",
    "isCompleted": false,
    "createdFrom": "natural-language",
    "created_at": "2026-10-05T09:00:00+00:00"
  }
}
```

> ⚠️ The returned `task` is **not persisted** to `db.tasks` — see [TODO.md](../TODO.md).

---

## 7.2 `GET /api/summaries/` — List summaries

- **Auth:** 🔒 JWT

**Responses:** `200` array of summaries · `500`

```bash
curl http://127.0.0.1:5000/api/summaries/ -H "Authorization: Bearer <access_token>"
```

---

## 7.3 `PUT /api/summaries/<summary_id>` — Update summary

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

**Allowed fields:** `sourceType`, `originalFileName`, `summaryBullets`

```json
{ "summaryBullets": ["Point one", "Point two", "New point"] }
```

**Responses:** `200 { "message": "Summary updated" }` · `404 Summary not found` · `500`

---

## 7.4 `DELETE /api/summaries/<summary_id>` — Delete summary

- **Auth:** 🔒 JWT

**Responses:** `200 { "message": "Summary deleted" }` · `404 { "message": "Summary not found" }` · `500`
