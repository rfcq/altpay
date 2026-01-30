# Running AltPay with HTTPS (for iOS camera)

On **iOS Safari**, the camera for the QR scanner usually only works on **HTTPS** (or `localhost`). If you can't use a tunnel (ngrok, etc.), you can run the app with HTTPS on your machine.

## Option 1: Run with built-in HTTPS (recommended)

Install dependencies (PyOpenSSL is required for HTTPS):

```bash
pip install -r requirements.txt
```

From the project root:

```bash
python run_https.py
```

This starts the Flask app with a **self-signed certificate** (HTTPS). Then:

1. Open **https://localhost:5000** in your browser.
2. You will see a certificate warning (e.g. "Your connection is not private"). Click **Advanced** → **Proceed to localhost** (or similar).
3. On your **iPhone/iPad**, open **https://YOUR_COMPUTER_IP:5000** (e.g. `https://192.168.1.10:5000`). Accept the certificate warning when asked.
4. The camera/scanner should then work on iOS.

To find your computer’s IP: run `ipconfig` (Windows) or `ifconfig` / `ip addr` (Mac/Linux).

## Option 2: Run with HTTP only

```bash
USE_HTTPS=0 python run_https.py
```

Or run your app as usual (e.g. `python app.py`). The scanner will open on HTTP, but **the camera may not work on iOS** because of browser security rules.

## Notes

- The self-signed certificate is only for local/testing. Browsers will always show a warning; that’s expected.
- If `run_https.py` fails with "No module named 'app'", ensure you have `app.py` in the project root and run the command from that directory.
