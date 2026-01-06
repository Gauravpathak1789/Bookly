# 🔐 Advanced Authentication System Documentation

## Overview
Complete enterprise-grade authentication system with all modern security features implemented.

---

## ✅ Features Implemented

### 1️⃣ **Email Verification**
- ✅ Send verification email on registration
- ✅ Token-based email confirmation
- ✅ Resend verification email
- ✅ 24-hour token expiry

**Endpoints:**
- `POST /auth/register` - Register & send verification email
- `POST /auth/verify-email` - Verify email with token
- `POST /auth/resend-verification` - Resend verification link

---

### 2️⃣ **Password Reset**
- ✅ Email-based password reset flow
- ✅ Secure token generation
- ✅ 1-hour reset token expiry
- ✅ Revoke all refresh tokens on reset

**Endpoints:**
- `POST /auth/password-reset-request` - Request reset email
- `POST /auth/password-reset-confirm` - Reset with token
- `POST /auth/change-password` - Change password when logged in

---

### 3️⃣ **Refresh Tokens**
- ✅ Long-lived refresh tokens (7 days)
- ✅ Store in database with device info
- ✅ Token rotation support
- ✅ Revoke on logout/password reset

**Endpoints:**
- `POST /auth/login` - Returns access + refresh token
- `POST /auth/refresh` - Get new access token
- `POST /auth/logout` - Revoke refresh token

**Models:**
```python
RefreshToken:
  - token (unique, indexed)
  - user_id (foreign key)
  - expires_at
  - is_revoked
  - device_info
```

---

### 4️⃣ **Rate Limiting**
- ✅ Login attempt tracking per user
- ✅ Account lockout after 5 failed attempts
- ✅ 30-minute lockout period
- ✅ 15-minute rate limit window
- ✅ IP-based rate limiting for registration/reset

**Configuration:**
```python
LOGIN_RATE_LIMIT_ATTEMPTS = 5
LOGIN_RATE_LIMIT_WINDOW_MINUTES = 15
ACCOUNT_LOCKOUT_MINUTES = 30
```

**Features:**
- Failed login counter
- Last failed login timestamp
- Account locked until timestamp
- Automatic reset after window

---

### 5️⃣ **Two-Factor Authentication (2FA/TOTP)**
- ✅ TOTP using pyotp (Google Authenticator compatible)
- ✅ QR code generation for easy setup
- ✅ 8 backup codes (hashed)
- ✅ Verification during login
- ✅ Email notification on enable/disable

**Endpoints:**
- `POST /auth/2fa/setup` - Generate QR code & backup codes
- `POST /auth/2fa/verify` - Verify TOTP code & enable 2FA
- `POST /auth/2fa/disable` - Disable 2FA with password

**Setup Flow:**
1. User calls `/2fa/setup` → receives QR code + backup codes
2. User scans QR in authenticator app
3. User verifies with code from app → 2FA enabled
4. Save backup codes securely!

---

### 6️⃣ **Role-Based Access Control (RBAC)**
- ✅ Three roles: USER, MODERATOR, ADMIN
- ✅ Role hierarchy system
- ✅ Permission checking utilities
- ✅ Dependency decorators for endpoints

**Roles:**
```python
class UserRole(enum.Enum):
    USER = "user"          # Default role
    MODERATOR = "moderator"  # Can moderate content
    ADMIN = "admin"         # Full access
```

**Usage Examples:**
```python
from utils.rbac import require_admin, require_verified_email

# Require admin role
@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: uuid.UUID):
    ...

# Require verified email
@router.post("/books", dependencies=[Depends(require_verified_email)])
async def create_book(book: BookCreate):
    ...

# Check in function
if not is_admin(current_user):
    raise PermissionDenied("Admin only")
```

---

### 7️⃣ **Social Login (OAuth)**
- ✅ Google OAuth 2.0
- ✅ GitHub OAuth
- ✅ Auto-create accounts
- ✅ Link existing accounts
- ✅ Email verified by default

**Endpoints:**
- `GET /oauth/google/login` - Redirect to Google
- `GET /oauth/google/callback` - Handle Google response
- `GET /oauth/github/login` - Redirect to GitHub
- `GET /oauth/github/callback` - Handle GitHub response

**Setup Required:**
1. Create Google OAuth app: https://console.cloud.google.com/
2. Create GitHub OAuth app: https://github.com/settings/developers
3. Add credentials to `.env`:
```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-secret
```

---

## 📊 Database Models Updated

### User Model Additions:
```python
# Role-Based Access
role: UserRole = USER

# Email Verification
verification_token: str
verification_token_expiry: datetime

# Password Reset
reset_token: str
reset_token_expiry: datetime

# Two-Factor Authentication
totp_secret: str
is_2fa_enabled: bool
backup_codes: str (JSON)

# OAuth
oauth_provider: str (google/github)
oauth_id: str

# Rate Limiting
failed_login_attempts: int
last_failed_login: datetime
account_locked_until: datetime
```

### New RefreshToken Model:
```python
id: int (primary key)
token: str (unique)
user_id: UUID (foreign key)
expires_at: datetime
is_revoked: bool
device_info: str
created_at: datetime
```

---

## 🚀 Quick Start

### 1. Update Environment Variables
Edit [.env](.env):
```env
# Existing
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
SECRET_KEY=your-secret-key-here

# Email (SMTP - Gmail example)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@bookly.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# OAuth (Optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### 2. Run Database Migration
```bash
python migrate.py
```

### 3. Start Server
```bash
uvicorn main:app --reload
```

### 4. Access API Docs
Open: http://localhost:8000/docs

---

## 📧 Email Setup (Gmail Example)

1. Enable 2-Step Verification in Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in `.env`:
```env
MAIL_USERNAME=youremail@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

---

## 🔒 Security Best Practices

✅ **Implemented:**
- Bcrypt password hashing with salt
- JWT token expiration
- Rate limiting on sensitive endpoints
- Account lockout after failed attempts
- Email verification required
- 2FA for high-security accounts
- HTTPS only in production
- Token rotation on password reset
- Secure random token generation

⚠️ **Production Recommendations:**
1. Use Redis for rate limiting (not in-memory)
2. Enable HTTPS/TLS
3. Use environment-specific secrets
4. Enable CORS properly
5. Add request logging
6. Monitor failed login attempts
7. Implement CAPTCHA for public endpoints
8. Use Celery for background email tasks

---

## 📝 API Usage Examples

### Registration Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "secure123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# 2. Check email for verification link
# 3. Verify email
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "received-token-from-email"}'
```

### Login with 2FA
```bash
# 1. Login (if 2FA enabled, will require code)
curl -X POST http://localhost:8000/auth/login \
  -d "username=john@example.com&password=secure123"

# Returns: access_token, refresh_token
```

### Setup 2FA
```bash
# 1. Setup 2FA (requires authentication)
curl -X POST http://localhost:8000/auth/2fa/setup \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Returns: QR code (base64), secret, backup_codes

# 2. Scan QR in Google Authenticator

# 3. Verify with code from app
curl -X POST http://localhost:8000/auth/2fa/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"totp_code": "123456"}'
```

### Password Reset
```bash
# 1. Request reset
curl -X POST http://localhost:8000/auth/password-reset-request \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com"}'

# 2. Check email for reset link

# 3. Reset password
curl -X POST http://localhost:8000/auth/password-reset-confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset-token-from-email",
    "new_password": "newsecure456"
  }'
```

### Refresh Access Token
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### Social Login
```
1. Navigate to: http://localhost:8000/oauth/google/login
2. Authorize with Google
3. Get redirected to frontend with tokens
```

---

## 🛠️ Customization

### Add More Roles
Edit [models.py](models.py):
```python
class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"  # Add new role
```

### Change Token Expiry
Edit [config.py](config.py) or [.env](.env):
```env
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
VERIFICATION_TOKEN_EXPIRE_HOURS=48
```

### Add More OAuth Providers
Copy pattern from [routers/oauth.py](routers/oauth.py) and add Twitter, Facebook, etc.

---

## 📂 File Structure
```
Bookly/
├── routers/
│   ├── auth.py          # Enhanced auth endpoints
│   ├── oauth.py         # Google/GitHub OAuth
│   └── books.py         # Book routes
├── utils/
│   ├── email.py         # Email service
│   └── rbac.py          # Role-based access control
├── middleware/
│   └── rate_limit.py    # Rate limiting logic
├── models.py            # Enhanced User + RefreshToken models
├── schemas.py           # Enhanced request/response models
├── config.py            # Settings with email/OAuth config
├── database.py          # Database connection
├── main.py              # FastAPI app with all routers
├── migrate.py           # Database migration script
├── requirements.txt     # All dependencies
└── .env                 # Environment variables
```

---

## 🐛 Troubleshooting

### Emails Not Sending
- Check SMTP credentials in `.env`
- For Gmail, use App Password not regular password
- Verify `MAIL_SERVER` and `MAIL_PORT`
- Check firewall/antivirus blocking port 587

### OAuth Not Working
- Verify redirect URIs match exactly in OAuth app settings
- Check CLIENT_ID and CLIENT_SECRET
- Ensure HTTPS in production
- Google: Add authorized domains

### Rate Limiting Too Strict
- Adjust in [config.py](config.py):
```python
LOGIN_RATE_LIMIT_ATTEMPTS = 10  # Increase
ACCOUNT_LOCKOUT_MINUTES = 15    # Decrease
```

### 2FA QR Code Not Scanning
- Ensure QR code image is displayed properly
- Try manual entry with secret key
- Check time sync on device

---

## 🎯 Next Steps

1. ✅ **All 7 features implemented!**
2. Configure email SMTP settings
3. Set up OAuth apps (optional)
4. Run migrations: `python migrate.py`
5. Test all endpoints in Swagger UI
6. Customize roles and permissions
7. Add production-grade rate limiting with Redis
8. Implement frontend integration

---

## 📚 Additional Resources

- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **OAuth 2.0**: https://oauth.net/2/
- **TOTP Spec**: https://tools.ietf.org/html/rfc6238
- **JWT Best Practices**: https://tools.ietf.org/html/rfc8725

---

**🎉 All requested features have been successfully implemented!**
