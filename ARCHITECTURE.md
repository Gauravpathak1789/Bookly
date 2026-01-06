# Authentication System Architecture

## System Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                     BOOKLY AUTH SYSTEM                          │
│                  (7 Advanced Features)                          │
└─────────────────────────────────────────────────────────────────┘

         ┌──────────────┐
         │   Frontend   │
         │  (React/Vue) │
         └──────┬───────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Rate Limit   │  │    RBAC      │  │   Email      │      │
│  │ Middleware   │  │  (Roles)     │  │  Service     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Routers                               │    │
│  │  • /auth    - Authentication                        │    │
│  │  • /oauth   - Social Login                          │    │
│  │  • /books   - Protected Resources                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
        ┌────────────┐ ┌─────────┐ ┌──────────┐
        │ PostgreSQL │ │  SMTP   │ │  OAuth   │
        │  Database  │ │ Server  │ │ Providers│
        └────────────┘ └─────────┘ └──────────┘
```

---

## 1. Registration & Email Verification Flow

```
User                    Backend                   Email Service
  │                        │                           │
  ├─1. POST /auth/register─>                          │
  │                        │                           │
  │                        ├─2. Hash password          │
  │                        │                           │
  │                        ├─3. Generate token         │
  │                        │                           │
  │                        ├─4. Save to DB             │
  │                        │                           │
  │                        ├─5. Send verification email─>
  │                        │                           │
  │<───────201 Created─────┤                           │
  │                        │                           │
  │<────────────────────────────6. Receive email──────┤
  │                        │                           │
  ├─7. POST /auth/verify-email (token)────>          │
  │                        │                           │
  │                        ├─8. Verify token           │
  │                        │                           │
  │                        ├─9. Mark verified          │
  │                        │                           │
  │<──────200 OK───────────┤                           │
```

---

## 2. Login with Rate Limiting

```
User                    Backend                   Database
  │                        │                           │
  ├─1. POST /auth/login───>                          │
  │                        │                           │
  │                        ├─2. Check rate limit──────>│
  │                        │                           │
  │                        │<─3. Failed attempts count─┤
  │                        │                           │
  │                        ├─4. Account locked?        │
  │                        │   NO: Continue            │
  │                        │   YES: Return 429         │
  │                        │                           │
  │                        ├─5. Verify password        │
  │                        │   ❌ Wrong: Increment fails│
  │                        │   ✅ Correct: Reset counter│
  │                        │                           │
  │                        ├─6. Create JWT tokens      │
  │                        │   • Access (30 min)       │
  │                        │   • Refresh (7 days)      │
  │                        │                           │
  │                        ├─7. Store refresh token───>│
  │                        │                           │
  │<──────Tokens───────────┤                           │
```

---

## 3. Two-Factor Authentication (2FA) Setup

```
User                    Backend                   User Device
  │                        │                           │
  ├─1. POST /2fa/setup────>                          │
  │                        │                           │
  │                        ├─2. Generate TOTP secret   │
  │                        │                           │
  │                        ├─3. Create QR code         │
  │                        │                           │
  │                        ├─4. Generate backup codes  │
  │                        │                           │
  │                        ├─5. Hash backup codes      │
  │                        │                           │
  │<──────QR + Codes───────┤                           │
  │                        │                           │
  ├─────────────────────────────6. Scan QR in app────>│
  │                        │                           │
  │<────────────────────────────7. Generate code──────┤
  │                        │                           │
  ├─8. POST /2fa/verify (code)───>                   │
  │                        │                           │
  │                        ├─9. Verify TOTP            │
  │                        │                           │
  │                        ├─10. Enable 2FA in DB      │
  │                        │                           │
  │<──────200 OK───────────┤                           │
```

---

## 4. Password Reset Flow

```
User                    Backend                   Email Service
  │                        │                           │
  ├─1. POST /password-reset-request───>              │
  │                        │                           │
  │                        ├─2. Find user by email     │
  │                        │                           │
  │                        ├─3. Generate reset token   │
  │                        │   (expires 1 hour)        │
  │                        │                           │
  │                        ├─4. Send reset email──────>│
  │                        │                           │
  │<───────200 OK──────────┤                           │
  │                        │                           │
  │<────────────────────────────5. Receive email──────┤
  │                        │                           │
  ├─6. POST /password-reset-confirm (token, new_pass)>│
  │                        │                           │
  │                        ├─7. Verify token           │
  │                        │                           │
  │                        ├─8. Hash new password      │
  │                        │                           │
  │                        ├─9. Revoke all refresh     │
  │                        │    tokens (security)      │
  │                        │                           │
  │<──────200 OK───────────┤                           │
```

---

## 5. OAuth Social Login (Google/GitHub)

```
User              Backend            OAuth Provider        Database
  │                  │                      │                 │
  ├─1. GET /oauth/google/login─>          │                 │
  │                  │                      │                 │
  │                  ├─2. Generate state    │                 │
  │                  │                      │                 │
  │<─3. Redirect to Google──────────────────>                │
  │                  │                      │                 │
  ├─────────────4. Login & Authorize──────>│                 │
  │                  │                      │                 │
  │<─────────5. Redirect with code──────────┤                 │
  │                  │                      │                 │
  ├─6. GET /oauth/google/callback (code)──>│                 │
  │                  │                      │                 │
  │                  ├─7. Exchange code for token────>       │
  │                  │                      │                 │
  │                  │<─8. Access token─────┤                 │
  │                  │                      │                 │
  │                  ├─9. Get user info────>│                 │
  │                  │                      │                 │
  │                  │<─10. User data───────┤                 │
  │                  │                      │                 │
  │                  ├─11. Find/Create user────────────────>│
  │                  │                      │                 │
  │                  ├─12. Generate JWT tokens               │
  │                  │                      │                 │
  │<─13. Redirect to frontend with tokens──┤                 │
```

---

## 6. Refresh Token Flow

```
User                    Backend                   Database
  │                        │                           │
  ├─1. Request with expired access token─>           │
  │                        │                           │
  │<───────401 Unauthorized┤                           │
  │                        │                           │
  ├─2. POST /auth/refresh (refresh_token)───>        │
  │                        │                           │
  │                        ├─3. Lookup token in DB───>│
  │                        │                           │
  │                        │<─4. Token data + user────┤
  │                        │                           │
  │                        ├─5. Verify not expired     │
  │                        │                           │
  │                        ├─6. Verify not revoked     │
  │                        │                           │
  │                        ├─7. Generate new access    │
  │                        │    token (30 min)         │
  │                        │                           │
  │<──────New Access Token─┤                           │
```

---

## 7. Role-Based Access Control (RBAC)

```
User Request            Middleware              Protected Endpoint
     │                      │                           │
     ├─1. GET /admin/users──>                          │
     │                      │                           │
     │                      ├─2. Extract JWT            │
     │                      │                           │
     │                      ├─3. Decode & verify        │
     │                      │                           │
     │                      ├─4. Load user from DB      │
     │                      │                           │
     │                      ├─5. Check role             │
     │                      │   ├─ USER      → ❌ 403   │
     │                      │   ├─ MODERATOR → ❌ 403   │
     │                      │   └─ ADMIN     → ✅ Allow │
     │                      │                           │
     │                      ├─────────Pass user────────>│
     │                      │                           │
     │                      │                  Execute endpoint
     │<─────────────────────┴───────200 OK──────────────┤
```

---

## Database Schema

```
┌─────────────────────────────────────┐
│            USERS TABLE              │
├─────────────────────────────────────┤
│ uid                   UUID PK       │
│ username              VARCHAR       │
│ email                 VARCHAR       │
│ hashed_password       VARCHAR       │
│ role                  ENUM          │ ◄─┐
│ is_active             BOOLEAN       │   │
│ is_verified           BOOLEAN       │   │
│ is_2fa_enabled        BOOLEAN       │   │
│ totp_secret           VARCHAR       │   │
│ backup_codes          VARCHAR       │   │
│ verification_token    VARCHAR       │   │
│ verification_expiry   TIMESTAMP     │   │
│ reset_token           VARCHAR       │   │
│ reset_expiry          TIMESTAMP     │   │
│ oauth_provider        VARCHAR       │   │
│ oauth_id              VARCHAR       │   │
│ failed_login_attempts INT           │   │
│ last_failed_login     TIMESTAMP     │   │
│ account_locked_until  TIMESTAMP     │   │
│ created_at            TIMESTAMP     │   │
│ updated_at            TIMESTAMP     │   │
└─────────────────────────────────────┘   │
                                          │
                                          │
┌─────────────────────────────────────┐   │
│       REFRESH_TOKENS TABLE          │   │
├─────────────────────────────────────┤   │
│ id                    SERIAL PK     │   │
│ token                 VARCHAR       │   │
│ user_id               UUID FK  ─────┼───┘
│ expires_at            TIMESTAMP     │
│ is_revoked            BOOLEAN       │
│ device_info           VARCHAR       │
│ created_at            TIMESTAMP     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│           BOOKS TABLE               │
├─────────────────────────────────────┤
│ uid                   UUID PK       │
│ title                 VARCHAR       │
│ author                VARCHAR       │
│ publisher             VARCHAR       │
│ published_date        VARCHAR       │
│ page_count            INT           │
│ language              VARCHAR       │
│ created_at            TIMESTAMP     │
│ updated_at            TIMESTAMP     │
└─────────────────────────────────────┘
```

---

## Security Layers

```
┌────────────────────────────────────────────────────┐
│                 Request Flow                       │
└────────────────────────────────────────────────────┘

Client Request
     │
     ▼
┌─────────────────────┐
│ 1. Rate Limiting    │ ◄─── IP-based throttling
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. JWT Validation   │ ◄─── Token verification
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. User Loading     │ ◄─── Database lookup
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Account Checks   │ ◄─── Active, verified, not locked
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Role Check       │ ◄─── RBAC permissions
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 6. 2FA Verification │ ◄─── TOTP if enabled
└──────────┬──────────┘
           │
           ▼
     Execute Endpoint
```

---

## Configuration Hierarchy

```
Environment Variables (.env)
         │
         ├─> config.py (Settings class)
         │      │
         │      ├─> Database settings
         │      ├─> JWT settings
         │      ├─> Email (SMTP) settings
         │      ├─> OAuth credentials
         │      └─> Rate limit thresholds
         │
         ├─> routers/auth.py (Authentication logic)
         │
         ├─> routers/oauth.py (Social login)
         │
         ├─> utils/email.py (Email service)
         │
         ├─> utils/rbac.py (Permission checks)
         │
         └─> middleware/rate_limit.py (Rate limiting)
```

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────┐
│                   PRODUCTION                     │
└──────────────────────────────────────────────────┘

                    ┌──────────┐
                    │  CDN/    │
                    │ Frontend │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │  Nginx   │
                    │ (HTTPS)  │
                    └─────┬────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    ┌───▼───┐        ┌────▼────┐      ┌────▼────┐
    │FastAPI│        │ FastAPI │      │ FastAPI │
    │Server │        │ Server  │      │ Server  │
    └───┬───┘        └────┬────┘      └────┬────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    ┌───▼────┐      ┌─────▼──────┐   ┌─────▼────┐
    │PostgreSQL     │   Redis    │   │  SMTP    │
    │ (Primary)     │ (Sessions) │   │ Service  │
    └───────┘       └────────────┘   └──────────┘
```

---

## Feature Matrix

| Feature              | Status | Endpoints | Models | Security |
|---------------------|--------|-----------|--------|----------|
| Email Verification  | ✅     | 3         | User   | Medium   |
| Password Reset      | ✅     | 3         | User   | High     |
| Refresh Tokens      | ✅     | 3         | Token  | High     |
| Rate Limiting       | ✅     | All       | User   | High     |
| 2FA/TOTP           | ✅     | 3         | User   | Very High|
| RBAC               | ✅     | Util      | User   | High     |
| OAuth Social Login  | ✅     | 4         | User   | High     |

---

**All 7 features fully implemented with production-grade security!**
