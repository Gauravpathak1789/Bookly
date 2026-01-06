"""
Quick setup script for advanced authentication system
Installs all required packages
"""
import subprocess
import sys

packages = [
    "fastapi-mail",
    "pyotp",
    "qrcode[pil]",
    "pillow",
    "httpx"
]

def install_packages():
    print("🚀 Installing advanced authentication packages...\n")
    
    for package in packages:
        print(f"📦 Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully\n")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}\n")
            return False
    
    print("✅ All packages installed successfully!")
    return True

if __name__ == "__main__":
    success = install_packages()
    
    if success:
        print("\n" + "="*60)
        print("🎉 Setup Complete!")
        print("="*60)
        print("\n📝 Next steps:")
        print("1. Configure your .env file (see AUTH_SETUP.md)")
        print("2. Run database migrations: python migrate.py")
        print("3. Start the server: uvicorn main:app --reload")
        print("4. Visit http://localhost:8000/docs for API documentation")
        print("\n📚 Full setup guide: AUTH_SETUP.md")
    else:
        print("\n❌ Setup failed. Please check errors above.")
        sys.exit(1)
