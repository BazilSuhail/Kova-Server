# 2. Users API — `/api/users`

> File: `app/api/users.py` · Blueprint: `users_bp` · **3 endpoints** · **All JWT-protected**

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

**⚠️ Note:** deletes only the `users` document — tasks/subtasks/planner/summaries are **orphaned** (no cascade).
