# 13. Mood API — `/api/mood`

> File: `app/api/mood.py` → `app/services/mood_service.py` · Blueprint: `mood_bp` · **6 endpoints** · **JWT-protected**

Mood journal, trends, and mood-based task-load suggestions.

Mood labels map to a **1–5 score** when the client does not send an explicit `score`:
`awful`/`bad`/`low`/`okay`/`ok`/`neutral`/`good`/`great`/`amazing`.

---

## 13.1 `POST /api/mood/` — Log a mood entry

- **Auth:** 🔒 JWT · **Content-Type:** `application/json`

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `mood` | string | ✅ | e.g. `great`, `okay`, `awful` |
| `score` | int | ❌ | 1–5; derived from `mood` if omitted/invalid |
| `energy` | int | ❌ | 1–5; stored as `null` if omitted/invalid |
| `note` | string | ❌ | free text |
| `tags` | string[] | ❌ | e.g. `["study","sleep"]` |

**Responses:** `201` created entry · `400 { "message": "mood is required" }` · `401`

```json
{ "moodId": "…", "userId": "…", "mood": "good", "score": 4, "energy": 4,
  "note": "Focused morning", "tags": ["study"], "loggedAt": "2026-10-17T08:00:00+00:00",
  "date": "2026-10-17", "createdAt": "…", "updatedAt": "…" }
```

---

## 13.2 `GET /api/mood/` — Mood feed (newest first)

- **Auth:** 🔒 JWT · optional `page`/`limit` (max 100) → bare array or `{items, pagination}` envelope.

---

## 13.3 `GET /api/mood/trends` — Trends over a window

- **Auth:** 🔒 JWT · Query: `days` (default `30`, clamp `1..365`)

```json
{
  "range": { "start": "2026-09-18", "end": "2026-10-17", "days": 30 },
  "entries": 12,
  "averageScore": 3.75,
  "distribution": { "good": 7, "okay": 5 },
  "series": [ { "date": "2026-09-18", "score": null, "entries": 0 }, { "date": "…", "score": 4.0, "entries": 2 } ],
  "streak": 3
}
```

**Errors:** `400 { "message": "days must be between 1 and 365" }` · `400 { "message": "days must be an integer" }`

---

## 13.4 `POST /api/mood/suggestions` — Mood-based load suggestion

- **Auth:** 🔒 JWT · Body (both optional): `{ "mood": "awful", "energy": 1 }`
- Uses the supplied mood, else the caller's latest logged entry, else a neutral default.

| `score` | `suggestedLoad` |
|:-------:|-----------------|
| 1–2 | `light` |
| 3 | `balanced` |
| 4–5 | `stretch` |

```json
{ "score": 1, "energy": 1, "suggestedLoad": "light",
  "message": "Protect your energy today: pick one essential task and let the rest wait." }
```

---

## 13.5 `GET /api/mood/<mood_id>` — Single entry

- **Responses:** `200` entry · `404 { "message": "Mood entry not found" }` (also for another user's id)

## 13.6 `DELETE /api/mood/<mood_id>` — Delete an entry

- **Responses:** `200 { "message": "Mood entry deleted" }` · `404 { "message": "Mood entry not found" }`
- Deletion is recorded as a sync tombstone.
