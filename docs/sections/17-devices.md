# 17. Devices API — `/api/devices`

> File: `app/api/devices.py` → `app/services/device_service.py` · Blueprint: `devices_bp` · **3 endpoints** · **JWT-protected**

Expo push-token registration so scheduled reminders can reach the device
(see [18-reminders.md](18-reminders.md)).

---

## 17.1 `POST /api/devices/` — Register a device

- **Auth:** 🔒 JWT · **Content-Type:** `application/json`

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `expoPushToken` | string | ✅ | e.g. `ExponentPushToken[xxxxxxxx]` |
| `platform` | string | ❌ | `ios` \| `android` \| `web` |

**Responses**

| Code | Body |
|------|------|
| `201` | device object |
| `400` | `{ "message": "expoPushToken is required" }` \| `{ "message": "platform must be one of: ios, android, web" }` |

```json
{ "deviceId": "…", "userId": "…", "expoPushToken": "ExponentPushToken[…]",
  "platform": "ios", "enabled": true, "registeredAt": "…", "updatedAt": "…" }
```

> **One physical device = one row.** A token that already exists is **re-owned** by the caller
> (e.g. a user logs in on a shared phone) rather than duplicated.

---

## 17.2 `GET /api/devices/` — Caller's devices

- **Auth:** 🔒 JWT → array, newest registration first.

## 17.3 `DELETE /api/devices/<device_id>` — Unregister

- **Responses:** `200 { "message": "Device unregistered" }` · `404 { "message": "Device not found" }`
- Tokens Expo later reports as `DeviceNotRegistered` are pruned automatically during reminder delivery.
