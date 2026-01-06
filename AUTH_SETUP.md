# Advanced Authentication System - Installation & Setup Guide

## 📦 Required Packages

Install all required dependencies:

```bash
pip install fastapi-mail pyotp qrcode[pil] pillow httpx
```

Or using the requirements file:
```bash
pip install -r requirements.txt
```

## 🔧 Environment Configuration

Add these variables to your `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/bookly

# JWT Settings
SECRET_KEY=your-super-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
VERIFICATION_TOKEN_EXPIRE_HOURS=24
RESET_TOKEN_EXPIRE_HOURS=1

# Email Settings (Gmail example)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=Bookly
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

# OAuth - Google
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/google/callback

# OAuth - GitHub
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/oauth/github/callback

# Rate Limiting
LOGIN_RATE_LIMIT_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_MINUTES=15
ACCOUNT_LOCKOUT_MINUTES=30

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

## 🗄️ Database Setup

Run migrations to create all tables:

```bash
python migrate.py
```

## 🚀 Run the Application

```bash
uvicorn main:app --reload
```

Access the API documentation at: http://localhost:8000/docs

## 📧 Email Setup (Gmail)

1. Enable 2-Step Verification in your Google Account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password as `MAIL_PASSWORD` in `.env`

## 🔐 OAuth Setup

### Google OAuth:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/oauth/google/callback`
6. Copy Client ID and Client Secret to `.env`

### GitHub OAuth:
1. Go to https://github.com/settings/developers
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:8000/oauth/github/callback`
4. Copy Client ID and Client Secret to `.env`

## 🎯 Features Implemented

### ✅ 1. Email Verification
- Automatic email sent on registration
- 24-hour expiration on verification tokens
- Resend verification email endpoint

### ✅ 2. Password Reset
- Forgot password flow with email
- 1-hour expiration on reset tokens
- Secure token-based reset

### ✅ 3. Refresh Tokens
- Long-lived tokens (7 days default)
- Device tracking
- Token revocation on logout

### ✅ 4. Rate Limiting
- 5 failed attempts allowed in 15 minutes
- 30-minute account lockout after limit
- Automatic reset after successful login

### ✅ 5. Two-Factor Authentication (2FA)
- TOTP-based (works with Google Authenticator, Authy, etc.)
- QR code generation for easy setup
- 8 backup codes for recovery
- Enable/disable with password confirmation

### ✅ 6. Role-Based Access Control (RBAC)
- Three roles: USER, MODERATOR, ADMIN
- Role-based endpoint protection
- Admin panel for user management

### ✅ 7. Social Login
- Google OAuth 2.0
- GitHub OAuth
- Automatic user creation
- Link social accounts

## 🔗 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with email/password
- `POST /auth/login/2fa` - Login with 2FA
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and revoke token
- `GET /auth/me` - Get current user

### Email Verification
- `POST /auth/verify-email` - Verify email with token
- `POST /auth/resend-verification` - Resend verification email

### Password Management
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token
- `POST /auth/change-password` - Change password (authenticated)

### Two-Factor Authentication
- `POST /auth/2fa/setup` - Setup 2FA (returns QR code)
- `POST /auth/2fa/verify` - Verify and enable 2FA
- `POST /auth/2fa/disable` - Disable 2FA

### OAuth Social Login
- `GET /oauth/google/login` - Initiate Google login
- `GET /oauth/google/callback` - Google callback
- `GET /oauth/github/login` - Initiate GitHub login
- `GET /oauth/github/callback` - GitHub callback

### Admin (Requires ADMIN role)
- `GET /auth/admin/users` - List all users
- `PATCH /auth/admin/users/{id}/role` - Update user role
- `PATCH /auth/admin/users/{id}/deactivate` - Deactivate user

## 📱 Testing 2FA

1. Register a user and verify email
2. Call `POST /auth/2fa/setup`
3. Scan the QR code with Google Authenticator app
4. Verify with `POST /auth/2fa/verify` using the 6-digit code
5. Login with `POST /auth/login/2fa` providing TOTP code

## 🔒 Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ TOTP-based 2FA
- ✅ Rate limiting & account lockout
- ✅ Secure token generation
- ✅ Password reset expiration
- ✅ Email verification required
- ✅ Role-based access control
- ✅ OAuth 2.0 integration

## 📊 Database Models

### User Table
- uid (UUID, primary key)
- username, email (unique, indexed)
- hashed_password
- role (USER, MODERATOR, ADMIN)
- is_active, is_verified
- 2FA fields (totp_secret, is_2fa_enabled, backup_codes)
- OAuth fields (oauth_provider, oauth_id)
- Rate limiting fields (failed_login_attempts, account_locked_until)
- Token fields (verification_token, reset_token)

### RefreshToken Table
- token (unique, indexed)
- user_id (foreign key)
- expires_at
- is_revoked
- device_info

## 🧪 Example Usage

### Register
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -d "username=john@example.com&password=SecurePass123!"
```

### Protected Request
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🎓 Next Steps

1. Customize email templates in `utils/email.py`
2. Set up production-ready email service (SendGrid, Mailgun)
3. Implement Redis for OAuth state storage
4. Add logging and monitoring
5. Set up HTTPS in production
6. Implement user profile management
7. Add password strength validation
8. Implement session management UI

## 📝 Notes

- Change `SECRET_KEY` in production (use `openssl rand -hex 32`)
- Use environment variables, never commit `.env` file
- Set up proper CORS for frontend integration
- Consider implementing refresh token rotation
- Add webhook support for user events
- Implement audit logging for security events

## 🐛 Troubleshooting

**Email not sending:**
- Check SMTP credentials
- Verify app password (Gmail)
- Check firewall/network settings

**2FA QR code not working:**
- Ensure system time is synchronized
- Verify TOTP secret is stored correctly
- Try manual entry of secret key

**OAuth not working:**
- Verify redirect URIs match exactly
- Check client ID and secret
- Ensure OAuth is enabled in provider console

**Rate limiting issues:**
- Check database timestamp columns
- Verify timezone settings
- Review rate limit configuration

## 📚 Documentation

Full API documentation available at: http://localhost:8000/docs
ReDoc format: http://localhost:8000/redoc

For questions or issues, please create an issue on GitHub.
