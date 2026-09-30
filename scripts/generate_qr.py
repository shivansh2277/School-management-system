import socket
import os
import sys
from pathlib import Path

def get_lan_ip():
    """Detect current active LAN IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connecting to a public address (doesn't actually send packets) routes via the default gateway
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    root_dir = Path(__file__).resolve().parent.parent
    ip = get_lan_ip()
    print(f"==================================================")
    print(f"  Sunrise School ERP - Mobile Dev Environment")
    print(f"==================================================")
    print(f"  Detected Active LAN IP : {ip}")
    print(f"  Backend API Endpoint   : http://{ip}:8000")
    print(f"  Web ERP Frontend       : http://{ip}:5173")
    print(f"  Expo Metro URL         : exp://{ip}:8081")
    print(f"==================================================")

    # 1. Update mobile/.env
    mobile_env = root_dir / "mobile" / ".env"
    env_content = f"# Local Development API URL for physical mobile devices and web\nEXPO_PUBLIC_API_URL=http://{ip}:8000\n"
    with open(mobile_env, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f" [OK] Updated mobile/.env -> http://{ip}:8000")

    # 2. Generate QR code
    try:
        import qrcode
        url = f"exp://{ip}:8081"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to root and web public
        root_qr = root_dir / "expo_qr_code.png"
        web_qr = root_dir / "web" / "public" / "expo_qr_code.png"
        img.save(root_qr)
        if web_qr.parent.exists():
            img.save(web_qr)
        print(f" [OK] Saved QR code image: {root_qr}")
    except Exception as e:
        print(f" [!] Could not generate QR image: {e}")

if __name__ == "__main__":
    main()
