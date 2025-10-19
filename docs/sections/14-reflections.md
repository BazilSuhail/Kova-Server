# 14. Reflections API — `/api/reflections`

> File: `app/api/reflections.py` → `app/services/reflection_service.py` · Blueprint: `reflections_bp` · **5 endpoints** · **JWT-protected**

Daily affirmation + journaling prompt, and the reflection journal itself.

---

## 14.1 `GET /api/reflections/today` — Prompt + affirmation

- **Auth:** 🔒 JWT · Query: `date` (optional `YYYY-MM-DD`, defaults to today UTC)

```json
{
  "date": "2026-10-17",
  "prompt": "What is one thing that went well today?",
  "affirmation": "Progress, not perfection, is the goal today.",
  "reflection": null
}
```

**Notes**
- Prompt + affirmation are **deterministic by date** (curated list, no network/key).
- `reflection` is the caller's entry for that date, or `null`.

---

## 14.2 `GET /api/reflections/` — Journal (newest first)

- **Auth:** 🔒 JWT → array of entries.

---

## 14.3 `POST /api/reflections/` — Write / replace a reflection

- **Auth:** 🔒 JWT · **Content-Type:** `application/json`

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `text` | string | ✅ | the reflection body |
| `date` | string | ❌ | `YYYY-MM-DD`, default today UTC |
| `mood` | string | ❌ | optional mood label |
| `prompt` | string | ❌ | defaults to the day's curated prompt |

**Responses:** `201` created/replaced entry · `400 { "message": "text is required" }`

> Posting twice for the same `date` **replaces** that day's entry (upsert by date), so the feed keeps one row per day.

---

## 14.4 `GET /api/reflections/<reflection_id>` — Single entry

- **Responses:** `200` · `404 { "message": "Reflection not found" }`

## 14.5 `DELETE /api/reflections/<reflection_id>` — Delete

- **Responses:** `200 { "message": "Reflection deleted" }` · `404`
- Recorded as a sync tombstone.
