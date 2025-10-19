# 1. Auth API — `/api/auth`

> File: `app/api/auth.py` · Blueprint: `auth_bp` · **6 endpoints**
> 3 public (signup/login/refresh) · 3 JWT-protected (logout/me/password)

---

## 1.1 `POST /api/auth/signup`

Create a new user and return an access + refresh token.

- **Auth:** public
- **Content-Type:** `application/json`

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | ✅ | |
| `email` | string | ✅ | must be unique |
| `password` | string | ✅ | bcrypt-hashed server-side (cost 12) |
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
| `201` | `{ "message": "User created", "access_token": "...", "refresh_token": "...", "userId": "..." }` |
| `400` | `{ "message": "Missing required fields" }` \| `{ "message": "Email already exists" }` |
| `500` | `{ "message": "Internal server error" }` |

```bash
curl -X POST http://127.0.0.1:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Lorde","email":"you@example.com","password":"secret123"}'
```

---

## 1.2 `POST /api/auth/login`

Authenticate and return an access + refresh token.

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
| `200` | `{ "access_token": "...", "refresh_token": "...", "userId": "..." }` |
| `400` | `{ "message": "Missing required fields" }` |
| `401` | `{ "message": "User not found" }` \| `{ "message": "Invalid password" }` |
| `500` | `{ "message": "Internal server error" }` |

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret123"}'
```

**Notes**
- JWT identity = `userId`; **access token valid 1 hour** (`KOVA_JWT_EXPIRES_SECONDS = 3600`),
  **refresh token valid 7 days** (`KOVA_JWT_REFRESH_EXPIRES_SECONDS = 604800`).
- bcrypt cost pinned to `rounds=12`.

---

## 1.3 `POST /api/auth/refresh` — Rotate tokens

Exchange a valid **refresh token** for a brand-new access/refresh pair (public).

- **Auth:** public (token in body, not header)
- **Content-Type:** `application/json`

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `refresh_token` | string | ✅ |

**Responses**

| Code | Body |
|------|------|
| `200` | `{ "access_token": "...", "refresh_token": "...", "userId": "..." }` |
| `400` | `{ "message": "refresh_token is required" }` |
| `401` | `{ "message": "Invalid or expired token" }` \| `{ "message": "Not a refresh token" }` \| `{ "message": "Token revoked" }` |

**Notes**
- **Rotation:** the presented refresh token is revoked as part of the exchange, so a
  replayed/stolen token stops working after the legitimate client refreshes once.

---

## 1.4 `POST /api/auth/logout` — Revoke tokens

Immediately invalidate the caller's access token (from the header) and, optionally,
a refresh token supplied in the body.

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json` (optional body)

**Request body (optional)**

| Field | Type | Required |
|-------|------|----------|
| `refresh_token` | string | ❌ |

**Responses:** `200 { "message": "Logged out" }` · `401` (missing/revoked token)

**Notes**
- Idempotent: logging out twice, or with an expired refresh token, still returns `200`.
- Revocation is stored in the `token_blocklist` collection (TTL index) and checked
  on every protected request — the access token dies **immediately**, not at expiry.

---

## 1.5 `GET /api/auth/me` — Current user

- **Auth:** 🔒 JWT

**Responses**

| Code | Body |
|------|------|
| `200` | profile: `userId`, `name`, `email`, `profilePicture`, `preferences`, `createdAt` (never the password hash) |
| `401` | missing/invalid/revoked token |
| `404` | `{ "message": "User not found" }` |

---

## 1.6 `PUT /api/auth/password` — Change password

Rotate the caller's password after re-proving the current one.

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `currentPassword` | string | ✅ | must match the stored hash |
| `newPassword` | string | ✅ | min **8** characters |

**Responses**

| Code | Body |
|------|------|
| `200` | `{ "message": "Password updated" }` |
| `400` | `{ "message": "currentPassword and newPassword are required" }` \| `{ "message": "New password must be at least 8 characters" }` |
| `401` | `{ "message": "Current password is incorrect" }` |
| `404` | `{ "message": "User not found" }` |

**Notes**
- Existing sessions (access/refresh tokens) stay valid after a password change.
  Use `POST /api/auth/logout` if you need to revoke them.
