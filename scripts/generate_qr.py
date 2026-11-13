import socket
import os
import sys
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_lan_ip():
    """Detect current active LAN IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def create_card_image(qr_img, title, subtitle, target_url, badge_text, badge_color):
    """Wrap a QR code inside a clean card with title, badge, and URL text."""
    qr_w, qr_h = qr_img.size
    padding = 24
    card_w = max(qr_w + padding * 2, 310)
    card_h = qr_h + 155
    qr_x = (card_w - qr_w) // 2
    
    # Load fonts if available
    try:
        font_title = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 15)
        font_badge = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 12)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 13)
        font_url = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 12)
        font_foot = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 12)
    except Exception:
        font_title = font_badge = font_sub = font_url = font_foot = ImageFont.load_default()
    
    # White card background
    card = Image.new("RGB", (card_w, card_h), (255, 255, 255))
    draw = ImageDraw.Draw(card)
    
    # Border
    draw.rectangle([(0, 0), (card_w - 1, card_h - 1)], outline=(203, 213, 225), width=2)
    
    # Header background bar
    draw.rectangle([(0, 0), (card_w, 50)], fill=(4, 41, 84))
    
    # Header title
    draw.text((padding, 16), title, font=font_title, fill=(255, 255, 255))
    
    # Badge (right side of header)
    badge_w = 76
    badge_x = card_w - padding - badge_w
    draw.rounded_rectangle([(badge_x, 12), (card_w - padding, 38)], radius=5, fill=badge_color)
    draw.text((badge_x + 9, 16), badge_text, font=font_badge, fill=(255, 255, 255))
    
    # Paste centered QR Code
    card.paste(qr_img, (qr_x, 66))
    
    # Subtitle / instructions below QR
    draw.text((padding, 66 + qr_h + 10), subtitle, font=font_sub, fill=(15, 23, 42))
    draw.text((padding, 66 + qr_h + 32), target_url, font=font_url, fill=(2, 132, 199))
    draw.text((padding, 66 + qr_h + 54), "Scan with camera or mobile app", font=font_foot, fill=(100, 116, 139))
    
    return card

def main():
    root_dir = Path(__file__).resolve().parent.parent
    ip = get_lan_ip()
    
    web_url = f"http://{ip}:5173"
    expo_url = f"exp://{ip}:8081"
    api_url = f"http://{ip}:8000"
    
    print("=" * 60)
    print("  Sunrise School ERP — Dev Environment & QR Generator")
    print("=" * 60)
    print(f"  Detected Active LAN IP : {ip}")
    print(f"  Web ERP Frontend       : {web_url}")
    print(f"  Expo Metro URL         : {expo_url}")
    print(f"  Backend API Endpoint   : {api_url}")
    print("=" * 60)

    # 1. Update mobile/.env
    mobile_env = root_dir / "mobile" / ".env"
    env_content = f"# Local Development API URL for physical mobile devices and web\nEXPO_PUBLIC_API_URL={api_url}\n"
    with open(mobile_env, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f" [OK] Updated mobile/.env -> {api_url}")

    # 2. Update backend/.env CORS_ORIGINS to include this IP
    backend_env = root_dir / "backend" / ".env"
    if backend_env.exists():
        with open(backend_env, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.startswith("CORS_ORIGINS="):
                origins = line.strip().split("=")[1].split(",")
                for extra in [f"http://{ip}:5173", f"http://{ip}:8081", f"http://{ip}:19006"]:
                    if extra not in origins:
                        origins.append(extra)
                new_lines.append(f"CORS_ORIGINS={','.join(origins)}\n")
            else:
                new_lines.append(line)
        with open(backend_env, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f" [OK] Verified backend/.env CORS_ORIGINS includes {ip}")

    # 3. Generate QR Codes
    try:
        import qrcode

        # A. Web QR Code
        qr_web = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr_web.add_data(web_url)
        qr_web.make(fit=True)
        img_web_raw = qr_web.make_image(fill_color="#042954", back_color="white").convert("RGB")
        card_web = create_card_image(
            img_web_raw,
            title="Sunrise ERP - Web",
            subtitle="Web ERP & Public Website",
            target_url=web_url,
            badge_text="Browser",
            badge_color=(14, 116, 144)
        )

        # B. Expo Mobile App QR Code
        qr_expo = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr_expo.add_data(expo_url)
        qr_expo.make(fit=True)
        img_expo_raw = qr_expo.make_image(fill_color="#042954", back_color="white").convert("RGB")
        card_expo = create_card_image(
            img_expo_raw,
            title="Sunrise ERP - Mobile",
            subtitle="Expo Mobile Client",
            target_url=expo_url,
            badge_text="Expo Go",
            badge_color=(217, 119, 6)
        )

        # C. Standalone Android APK QR Code
        apk_download_url = "https://expo.dev/artifacts/eas/WpvEepEkhGN4NRYntwo_YxI_pPdrP4U8T40UQtSDPmM.apk"
        qr_apk = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr_apk.add_data(apk_download_url)
        qr_apk.make(fit=True)
        img_apk_raw = qr_apk.make_image(fill_color="#042954", back_color="white").convert("RGB")
        card_apk = create_card_image(
            img_apk_raw,
            title="Sunrise ERP - Standalone APK",
            subtitle="Android Release APK",
            target_url="expo.dev/artifacts/eas/...apk",
            badge_text="APK v1.0.1",
            badge_color=(16, 185, 129)
        )

        # D. Combined image
        gap = 20
        combined_w = card_web.width + card_expo.width + card_apk.width + gap * 2 + 40
        combined_h = max(card_web.height, card_expo.height, card_apk.height) + 85
        combined = Image.new("RGB", (combined_w, combined_h), (248, 250, 252))
        draw_comb = ImageDraw.Draw(combined)
        
        # Banner
        try:
            banner_font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 15)
        except Exception:
            banner_font = ImageFont.load_default()
        draw_comb.rectangle([(0, 0), (combined_w, 50)], fill=(4, 41, 84))
        draw_comb.text((24, 16), "SUNRISE SCHOOL ERP - LOCAL DEV & TESTING PORTAL", font=banner_font, fill=(255, 255, 255))
        
        # Paste cards
        combined.paste(card_web, (20, 65))
        combined.paste(card_expo, (20 + card_web.width + gap, 65))
        combined.paste(card_apk, (20 + card_web.width + gap + card_expo.width + gap, 65))

        # Save paths
        root_web_qr = root_dir / "website_qr_code.png"
        root_expo_qr = root_dir / "expo_qr_code.png"
        root_apk_qr = root_dir / "apk_download_qr.png"
        root_combined_qr = root_dir / "combined_qr_codes.png"

        card_web.save(root_web_qr)
        card_expo.save(root_expo_qr)
        card_apk.save(root_apk_qr)
        combined.save(root_combined_qr)

        # Also save to parent workspace root
        parent_root = root_dir.parent
        card_web.save(parent_root / "website_qr_code.png")
        card_expo.save(parent_root / "expo_qr_code.png")
        card_apk.save(parent_root / "apk_download_qr.png")
        combined.save(parent_root / "combined_qr_codes.png")

        # Also save to web/public
        web_public = root_dir / "web" / "public"
        if web_public.exists():
            card_web.save(web_public / "website_qr_code.png")
            card_expo.save(web_public / "expo_qr_code.png")
            card_apk.save(web_public / "apk_download_qr.png")
            combined.save(web_public / "combined_qr_codes.png")

        print(f" [OK] Saved Website QR Code : {root_web_qr}")
        print(f" [OK] Saved Mobile App QR Code: {root_expo_qr}")
        print(f" [OK] Saved APK Download QR Code: {root_apk_qr}")
        print(f" [OK] Saved Combined QR Image : {root_combined_qr}")

    except Exception as e:
        print(f" [!] Error generating QR code images: {e}")
        import traceback
        traceback.print_exc()

    # 4. Generate Interactive test_links.html
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sunrise School ERP — Local Test Links & QR Codes</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    body {{ background: #f8fafc; color: #1e293b; padding: 32px 16px; }}
    .container {{ max-width: 960px; margin: 0 auto; }}
    .header {{ background: #042954; color: white; padding: 24px 32px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
    .header h1 {{ font-size: 24px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 6px; }}
    .header p {{ color: #cbd5e1; font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 24px; margin-bottom: 24px; }}
    .card {{ background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .card h2 {{ font-size: 18px; color: #042954; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; }}
    .card h2 .badge {{ font-size: 11px; padding: 3px 8px; border-radius: 9999px; font-weight: 700; }}
    .badge-blue {{ background: #e0f2fe; color: #0369a1; }}
    .badge-amber {{ background: #fef3c7; color: #b45309; }}
    .badge-green {{ background: #dcfce7; color: #15803d; }}
    .qr-container {{ text-align: center; margin: 16px 0; }}
    .qr-container img {{ max-width: 240px; height: auto; border: 1px solid #e2e8f0; border-radius: 8px; }}
    .link-list {{ list-style: none; margin-top: 16px; }}
    .link-list li {{ margin-bottom: 10px; font-size: 14px; }}
    .link-list a {{ color: #0284c7; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }}
    .link-list a:hover {{ text-decoration: underline; }}
    .code-box {{ background: #f1f5f9; padding: 8px 12px; border-radius: 6px; font-family: monospace; font-size: 13px; margin-top: 4px; word-break: break-all; }}
    .credentials {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-top: 16px; font-size: 13px; }}
    .credentials table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    .credentials th, .credentials td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid #e2e8f0; }}
    .credentials th {{ color: #64748b; font-size: 11px; text-transform: uppercase; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Sunrise School ERP — Dev & Test Portal</h1>
      <p>Active LAN Host: <strong>{ip}</strong> | All systems operational on local network</p>
    </div>

    <div class="grid">
      <!-- Website Card -->
      <div class="card">
        <h2>Web ERP & Public Site <span class="badge badge-blue">Port 5173</span></h2>
        <p style="font-size: 13px; color: #64748b;">Scan to open ERP or Public Website on phone, tablet, or external laptop:</p>
        <div class="qr-container">
          <img src="website_qr_code.png" alt="Website QR Code">
        </div>
        <ul class="link-list">
          <li><strong>Public Website:</strong> <br><a href="{web_url}/#/" target="_blank">{web_url}/#/ &rarr;</a></li>
          <li><strong>Admissions (Steps & Enquiry):</strong> <br><a href="{web_url}/#/admissions" target="_blank">{web_url}/#/admissions &rarr;</a></li>
          <li><strong>Document Exceptions Queue:</strong> <br><a href="{web_url}/#/admin/admission-exceptions" target="_blank">{web_url}/#/admin/admission-exceptions &rarr;</a></li>
          <li><strong>User Access & Roles (/user-access):</strong> <br><a href="{web_url}/#/admin/users" target="_blank">{web_url}/#/admin/users &rarr;</a></li>
          <li><strong>Library Desk:</strong> <br><a href="{web_url}/#/library" target="_blank">{web_url}/#/library &rarr;</a></li>
          <li><strong>Admin Dashboard:</strong> <br><a href="{web_url}/#/dashboard" target="_blank">{web_url}/#/dashboard &rarr;</a></li>
          <li><strong>Localhost:</strong> <br><a href="http://localhost:5173" target="_blank">http://localhost:5173 &rarr;</a></li>
        </ul>
      </div>

      <!-- Mobile App Card -->
      <div class="card">
        <h2>Mobile App (Expo Go) <span class="badge badge-amber">Port 8081</span></h2>
        <p style="font-size: 13px; color: #64748b;">Scan with the Expo Go camera (Android) or native Camera app (iOS):</p>
        <div class="qr-container">
          <img src="expo_qr_code.png" alt="Expo App QR Code">
        </div>
        <ul class="link-list">
          <li><strong>Expo URL:</strong> <br><div class="code-box">{expo_url}</div></li>
          <li><strong>Metro Bundler Web:</strong> <br><a href="http://localhost:8081" target="_blank">http://localhost:8081 &rarr;</a></li>
          <li><strong>Backend API Docs:</strong> <br><a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs &rarr;</a></li>
        </ul>
      </div>

      <!-- Standalone Production APK Card -->
      <div class="card">
        <h2>Standalone Android APK <span class="badge badge-green">Release v1.0.1</span></h2>
        <p style="font-size: 13px; color: #64748b;">Direct installable APK for Android phones (Offline Hermes engine, zero Expo Go required):</p>
        <div class="qr-container">
          <img src="apk_download_qr.png" alt="APK Download QR Code">
        </div>
        <ul class="link-list">
          <li><strong>Direct Download Link:</strong> <br><a href="{apk_download_url}" target="_blank" style="background: #042954; color: #fff; padding: 6px 14px; border-radius: 6px; font-size: 12px; text-decoration: none; margin-top: 4px; display: inline-block;">Download APK (88 MB) &darr;</a></li>
          <li><strong>Package ID:</strong> <br><code>edu.sunrisepublic.app</code> (VersionCode: 2)</li>
          <li><strong>Cloud Backend:</strong> <br><a href="https://school-management-system-12ks.onrender.com" target="_blank">Render Live Backend &rarr;</a></li>
        </ul>
      </div>
    </div>

    <!-- Credentials Card -->
    <div class="card" style="grid-column: 1 / -1;">
      <h2>Demo Login Credentials <span class="badge badge-green">Unified Password: Admin@123 / Role Passwords</span></h2>
      
      <div style="margin-top: 16px;">
        <h3 style="font-size: 15px; color: #042954; margin-bottom: 8px;">1. Mobile App Credentials (Expo Go / Physical Phone)</h3>
        <p style="font-size: 13px; color: #64748b; margin-bottom: 8px;">Switch between Teacher, Parent, and Student tabs on the mobile login screen:</p>
        <div class="credentials">
          <table>
            <thead>
              <tr><th>Role Tab</th><th>Login Identifier</th><th>Hint / Type</th><th>Password</th><th>Key Features</th></tr>
            </thead>
            <tbody>
              <tr><td><strong style="color: #4338ca;">Teacher</strong></td><td><code>TCH001</code></td><td>Teacher ID</td><td><code>Teacher@123</code></td><td>Attendance, Marks Entry, Homework Grading, Stock/Inventory</td></tr>
              <tr><td><strong style="color: #0284c7;">Parent</strong></td><td><code>9876500001</code></td><td>Registered Mobile</td><td><code>Parent@123</code></td><td>CBSE Report Card, Direct UPI Fees, Attendance & Notices</td></tr>
              <tr><td><strong style="color: #059669;">Student</strong></td><td><code>2024000001</code></td><td>Admission Number</td><td><code>Student@123</code></td><td>Timetable, Homework Turn-in, Subject Marks & Report Cards</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div style="margin-top: 24px;">
        <h3 style="font-size: 15px; color: #042954; margin-bottom: 8px;">2. Web ERP Credentials (Desktop & Tablet)</h3>
        <p style="font-size: 13px; color: #64748b; margin-bottom: 8px;">Log in at <a href="{web_url}/#/login" target="_blank">{web_url}/#/login</a> with email and password:</p>
        <div class="credentials">
          <table>
            <thead>
              <tr><th>Role</th><th>Login Email</th><th>Password</th><th>Scope & Access</th></tr>
            </thead>
            <tbody>
              <tr><td><strong>Admin / Management</strong></td><td><code>admin@sunrisepublic.edu</code></td><td><code>Admin@123</code></td><td>Full ERP Access (All Modules, Exceptions, Settings)</td></tr>
              <tr><td><strong>Librarian</strong></td><td><code>librarian@sunrisepublic.edu</code></td><td><code>Admin@123</code></td><td>Library Catalogue & Circulation Desk, Notices</td></tr>
              <tr><td><strong>Admission Officer</strong></td><td><code>admission@sunrisepublic.edu</code></td><td><code>Admin@123</code></td><td>Enquiries, Applications, Exceptions, Merit, Reports</td></tr>
              <tr><td><strong>Front Desk Receptionist</strong></td><td><code>receptionist@sunrisepublic.edu</code></td><td><code>Admin@123</code></td><td>Enquiries, Gate Passes, Visitors, Directory</td></tr>
              <tr><td><strong>Senior Teacher</strong></td><td><code>anita@sunrisepublic.edu</code></td><td><code>Admin@123</code></td><td>Attendance, Marks Entry, Homework Grading</td></tr>
              <tr><td><strong>Parent</strong></td><td><code>parent@sunrisepublic.edu</code></td><td><code>Admin@123</code></td><td>Fee Ledger, Attendance, CBSE Report Card</td></tr>
              <tr><td><strong>Student</strong></td><td><code>student@sunrisepublic.edu</code></td><td><code>Admin@123</code></td><td>Timetable, Homework Turn-in, Results</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""
    test_html_path = root_dir / "test_links.html"
    with open(test_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    if (root_dir / "web" / "public").exists():
        with open(root_dir / "web" / "public" / "test_links.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    print(f" [OK] Generated test_links.html : {test_html_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
