# 5. Notifications API — `/api/notifications`

> File: `app/api/notifications.py` · Blueprint: `notifications_bp` · **5 endpoints** · **All JWT-protected**

Notifications are sorted `createdAt` descending (newest first).

---

## 5.1 `POST /api/notifications/` — Create notification

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `title` | string | ✅ | — |
| `message` | string | ✅ | — |
| `type` | string | ❌ | `""` |
| `relatedId` | string | ❌ | `""` |
| `triggerTime` | string (ISO) | ❌ | `null` |

```json
{
  "title": "Task due",
  "message": "Buy groceries is due in 1 hour",
  "type": "reminder",
  "relatedId": "6890abc...",
  "triggerTime": "2026-10-05T18:00:00+00:00"
}
```

**Responses**

| Code | Body |
|------|------|
| `201` | created notification (`read: false`, `createdAt`, `notificationId`) |
| `400` | `{ "message": "Title and message are required" }` |
| `500` | `{ "message": "Internal server error" }` |

---

## 5.2 `GET /api/notifications/` — List notifications

- **Auth:** 🔒 JWT

**Query parameters (all optional)**

| Param | Type | Effect |
|-------|------|--------|
| `unread` | `true` / `false` | filter by read state |
| `page` | int ≥ 1 | switches response to the paged envelope (see below) |
| `limit` | int 1–100 | page size (default 50; used with `page`) |

**Responses:** `200` array (newest first) · `400` invalid `unread`/`page`/`limit` · `500`

Without `page`/`limit` the body is the bare array:

```json
[
  {
    "notificationId": "6890xyz...",
    "userId": "68862e...",
    "title": "Task due",
    "message": "Buy groceries is due in 1 hour",
    "type": "reminder",
    "relatedId": "6890abc...",
    "createdAt": "2026-10-05T09:00:00+00:00",
    "read": false,
    "triggerTime": "2026-10-05T18:00:00+00:00"
  }
]
```

With `?page=1&limit=20`:

```json
{
  "items": [ { "...": "notification" } ],
  "pagination": {
    "page": 1, "limit": 20, "total": 42,
    "totalPages": 3, "hasNext": true, "hasPrev": false
  }
}
```

```bash
curl http://127.0.0.1:5000/api/notifications/?unread=true \
  -H "Authorization: Bearer <access_token>"
```

---

## 5.3 `GET /api/notifications/<notification_id>` — Single notification

- **Auth:** 🔒 JWT

**Responses:** `200` notification · `404 { "message": "Notification not found" }` (missing or another user's)

---

## 5.4 `PUT /api/notifications/<notification_id>` — Update notification

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

**Allowed fields:** `read`, `title`, `message`, `triggerTime`

```json
{ "read": true }
```

**Responses:** `200 { "message": "Notification updated" }` · `404 { "message": "Notification not found" }` · `500`

---

## 5.5 `DELETE /api/notifications/<notification_id>` — Delete notification

- **Auth:** 🔒 JWT

**Responses:** `200 { "message": "Notification deleted" }` · `404 { "message": "Notification not found" }` · `500`
