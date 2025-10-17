# 1. Auth API — `/api/auth`

> File: `app/api/auth.py` · Blueprint: `auth_bp` · **2 endpoints** · **Both public (no JWT)**

---

## 1.1 `POST /api/auth/signup`

Create a new user and return a JWT.

- **Auth:** public
- **Content-Type:** `application/json`

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | ✅ | |
| `email` | string | ✅ | must be unique |
| `password` | string | ✅ | bcrypt-hashed server-side |
| `profilePicture` | string | ❌ | default `""` |
| `preferences` | object | ❌ | default `{ "theme": "light", "notificationsEnabled": true }` |

```json
{
  "name": "Lorde",
  "email": "you@example.com",
  "password": "secret123"
}
```

**Responses**

| Code | Body |
|------|------|
| `201` | `{ "message": "User created", "access_token": "...", "userId": "..." }` |
| `400` | `{ "message": "Missing required fields" }` \| `{ "message": "Email already exists" }` |
| `500` | `{ "message": "Internal server error" }` |

```bash
curl -X POST http://127.0.0.1:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Lorde","email":"you@example.com","password":"secret123"}'
```

---

## 1.2 `POST /api/auth/login`

Authenticate and return a JWT.

- **Auth:** public
- **Content-Type:** `application/json`

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `email` | string | ✅ |
| `password` | string | ✅ |

```json
{ "email": "you@example.com", "password": "secret123" }
```

**Responses**

| Code | Body |
|------|------|
| `200` | `{ "access_token": "...", "userId": "..." }` |
| `400` | `{ "message": "Missing required fields" }` |
| `401` | `{ "message": "User not found" }` \| `{ "message": "Invalid password" }` |
| `500` | `{ "message": "Internal server error" }` |

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret123"}'
```

**Notes**
- JWT identity = `userId`; token valid for **1 hour** (`JWT_ACCESS_TOKEN_EXPIRES = 3600`).
- bcrypt cost: default `gensalt()`.
