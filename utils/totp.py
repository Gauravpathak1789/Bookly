"""
Two-Factor Authentication (2FA) utilities using TOTP
"""
import pyotp
import qrcode
from io import BytesIO
import base64
from typing import List
import secrets


def generate_totp_secret() -> str:
    """Generate a random TOTP secret key"""
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str, issuer: str = "Bookly") -> str:
    """Generate TOTP URI for QR code"""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=issuer
    )


def generate_qr_code(totp_uri: str) -> str:
    """
    Generate QR code image from TOTP URI
    Returns base64 encoded PNG image
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def verify_totp(secret: str, code: str) -> bool:
    """
    Verify a TOTP code
    Returns True if valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 30s window


def generate_backup_codes(count: int = 8) -> List[str]:
    """
    Generate backup codes for 2FA recovery
    Each code is 8 characters (alphanumeric)
    """
    codes = []
    for _ in range(count):
        # Generate 8-character code (remove dashes from UUID)
        code = secrets.token_hex(4).upper()  # 8 hex chars
        codes.append(code)
    return codes


def verify_backup_code(stored_codes: str, input_code: str) -> tuple[bool, str]:
    """
    Verify a backup code and return updated codes list
    Returns (is_valid, updated_codes_string)
    """
    import json
    
    try:
        codes = json.loads(stored_codes) if stored_codes else []
    except:
        return False, stored_codes
    
    input_code = input_code.upper().strip()
    
    if input_code in codes:
        # Remove used code
        codes.remove(input_code)
        return True, json.dumps(codes)
    
    return False, stored_codes
