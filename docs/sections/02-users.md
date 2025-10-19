# 2. Users API — `/api/users`

> File: `app/api/users.py` · Blueprint: `users_bp` · **7 endpoints**
> 5 JWT-protected (profile + settings) · 2 public (avatar catalogue + avatar images)

---

## 2.1 `GET /api/users/profile`

Get the current user's profile (password excluded).

- **Auth:** 🔒 JWT required
- **User id:** from JWT (`get_jwt_identity()`)

**Responses**

| Code | Body |
|------|------|
| `200` | user object (see below) |
| `404` | `{ "message": "User not found" }` |
| `500` | `{ "message": "Internal server error" }` |

```json
{
  "_id": "...",
  "userId": "68862e59ed9293b0ad17b27f",
  "name": "Lorde",
  "email": "you@example.com",
  "profilePicture": "",
  "preferences": { "theme": "light", "notificationsEnabled": true },
  "createdAt": "2026-01-01T10:00:00"
}
```

```bash
curl http://127.0.0.1:5000/api/users/profile \
  -H "Authorization: Bearer <access_token>"
```

---

## 2.2 `PUT /api/users/profile`

Update own profile. Only whitelisted fields are applied.

- **Auth:** 🔒 JWT required
- **Content-Type:** `application/json`

**Allowed fields:** `name`, `email`, `profilePicture`, `preferences`

```json
{
  "name": "Lorde",
  "profilePicture": "https://cdn.example.com/me.png",
  "preferences": { "theme": "dark", "notificationsEnabled": false }
}
```

**Responses**

| Code | Body |
|------|------|
| `200` | updated user object (password excluded) |
| `400` | `{ "message": "Email already in use" }` \| `{ "message": "User not found or no changes made" }` |
| `500` | `{ "message": "Internal server error" }` |

```bash
curl -X PUT http://127.0.0.1:5000/api/users/profile \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Lorde"}'
```

**Picking an avatar:** send `avatarId` (from [§2.6](#26-get-apiusersavatars--avatar-catalogue))
instead of `profilePicture` — the server resolves it to a hosted image URL and stores
that in `profilePicture`. An unknown id → `400 { "message": "Unknown avatar" }`.

```bash
curl -X PUT http://127.0.0.1:5000/api/users/profile \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"avatarId":"avatar3"}'
# 200 → "profilePicture": "/api/users/avatars/avatar3.svg"
```

---

## 2.3 `DELETE /api/users/profile`

Delete the current user account.

- **Auth:** 🔒 JWT required

**Responses**

| Code | Body |
|------|------|
| `200` | `{ "message": "User deleted" }` |
| `404` | `{ "message": "User not found" }` |
| `500` | `{ "message": "Internal server error" }` |

```bash
curl -X DELETE http://127.0.0.1:5000/api/users/profile \
  -H "Authorization: Bearer <access_token>"
```

**✅ Cascade:** deleting the account also removes **everything it owns** — tasks,
subtasks, planner, summaries, notifications, mood entries, reflections, reminders,
push devices, tombstones and revoked-token rows. Other users' data is untouched.
Deletion is irreversible.

---

## 2.4 `GET /api/users/profile/settings` — Read customisation

- **Auth:** 🔒 JWT

Returns the caller's customisation block (`preferences`).

```json
{ "theme": "light", "notificationsEnabled": true }
```

| Code | Body |
|------|------|
| `200` | settings object |
| `404` | `{ "message": "User not found" }` |

---

## 2.5 `PUT /api/users/profile/settings` — Update customisation

- **Auth:** 🔒 JWT · **Content-Type:** `application/json`

Merges **whitelisted** settings into `preferences`; unknown keys are ignored.

**Allowed keys:** `theme`, `fontSize`, `layout`, `notificationStyle`, `notificationsEnabled`, `language`

```bash
curl -X PUT http://127.0.0.1:5000/api/users/profile/settings \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"theme":"dark","fontSize":"large","notificationStyle":"gentle"}'
```

**Responses:** `200` → the merged settings object · `404 { "message": "User not found" }`

---

## 2.6 `GET /api/users/avatars` — Avatar catalogue

- **Auth:** public (the mobile app may show the picker during onboarding)
- Lists the avatar images shipped with the server (`app/assets/avatars`, or
  `KOVA_AVATAR_DIR`).

```json
{
  "avatars": [
    { "id": "avatar1", "filename": "avatar1.svg", "url": "/api/users/avatars/avatar1.svg" },
    { "id": "avatar2", "filename": "avatar2.svg", "url": "/api/users/avatars/avatar2.svg" }
  ]
}
```

`id` is what the client sends as `avatarId`; `url` is relative to the API base.
Operators can drop extra `.svg/.png/.jpg/.jpeg/.webp` files into the folder — they
appear automatically (id = filename without extension).

---

## 2.7 `GET /api/users/avatars/<filename>` — Serve an avatar image

- **Auth:** public — non-sensitive static asset, so a client `<Image>` needs no
  `Authorization` header. Content-Type is derived from the extension
  (`image/svg+xml`, `image/png`, …).

| Code | Body |
|------|------|
| `200` | the image bytes |
| `404` | `{ "message": "Avatar not found" }` (also for path-traversal attempts) |

```bash
curl -O http://127.0.0.1:5000/api/users/avatars/avatar1.svg
```
