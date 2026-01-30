#!/usr/bin/env python3
"""
Run the AltPay Flask app with HTTPS (self-signed certificate).

Use this when you need the camera to work on iOS Safari, which requires
a secure context (HTTPS). The browser will show a certificate warning—
accept it to continue.

  python run_https.py

Then open https://localhost:5000 (or https://YOUR_IP:5000 from your phone)
and accept the certificate warning. After that, the camera/scanner can work on iOS.
"""
import os
import sys

# Run from project root so "from app import app" works
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

if __name__ == "__main__":
    try:
        from app import app
    except ImportError as e:
        print("Error: Could not import app. Make sure app.py exists in the project root.")
        print("Detail:", e)
        sys.exit(1)

    port = int(os.environ.get("PORT", 3000))
    use_https = os.environ.get("USE_HTTPS", "1").strip().lower() in ("1", "true", "yes")

    if use_https:
        # adhoc: Flask generates a self-signed cert. Requires PyOpenSSL: pip install pyopenssl
        print("Starting with HTTPS (self-signed certificate)...")
        print("Open https://localhost:{} and accept the certificate warning.".format(port))
        print("From another device (e.g. iPhone), use https://<this-machine-ip>:{}".format(port))
        try:
            app.run(host="0.0.0.0", port=port, debug=True, ssl_context="adhoc")
        except Exception as e:
            if "adhoc" in str(e).lower() or "ssl" in str(e).lower():
                print("HTTPS failed (install PyOpenSSL: pip install pyopenssl). Falling back to HTTP.")
                print("Camera may not work on iOS over HTTP.")
                app.run(host="0.0.0.0", port=port, debug=True)
            else:
                raise
    else:
        app.run(host="0.0.0.0", port=port, debug=True)
