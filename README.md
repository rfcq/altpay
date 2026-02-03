# AltPay Shop

Flask web app for product management, QR codes, and shopping cart. Supports login, roles (admin/user), multilanguage (EN / pt-BR), and optional Discogs price suggestions.

## Features

- **Products**: Create, edit, delete, import from CSV/JSON, search, bulk add to cart, print with QR codes
- **Cart**: Add via QR scan or from product list, finish buy (checkout), products sold history
- **Auth**: Login, encrypted usernames/emails, role-based access (admin can add users)
- **Configuration**: Database URL (admin), danger zone (erase all users)
- **Discogs**: Price suggestions on Create Product (optional)

## Quick start

```bash
pip install -r requirements.txt
# Set SECRET_KEY and optionally DATABASE_URL, APP_ENCRYPTION_KEY (see below)
python app.py
# Or with HTTPS (for iOS camera): python run_https.py
```

Open `http://127.0.0.1:5000` (or the HTTPS URL shown by `run_https.py`).

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Recommended | Flask session secret; use a long random string in production. |
| `DATABASE_URL` or `POSTGRES_URL` | For persistent DB | Postgres connection string. If unset, uses SQLite (`altpay.db` locally; on Vercel uses `/tmp`, so data is ephemeral). |
| `APP_ENCRYPTION_KEY` | Yes on Vercel | Base64 Fernet key for encrypting usernames/emails. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

See **VERCEL.md** for deployment and **HTTPS_SETUP.md** for local HTTPS (e.g. iOS camera).

---

## Discogs configuration (optional)

The **Create Product** page can show **price suggestions from Discogs** (search by product name, then “Suggest price from Discogs”). To enable it, configure one of the following.

### Option 1: Personal access token (simplest)

1. Log in at [Discogs](https://www.discogs.com).
2. Go to [Developer Settings](https://www.discogs.com/settings/developers).
3. Click **Generate new token** and copy the token.
4. Set the environment variable:
   - **Name:** `DISCOGS_TOKEN`
   - **Value:** your token

### Option 2: Consumer key and secret

1. At [Developer Settings](https://www.discogs.com/settings/developers), create an application if you don’t have one.
2. Copy the **Consumer Key** and **Consumer Secret**.
3. Set:
   - **Name:** `DISCOGS_CONSUMER_KEY` → **Value:** your consumer key  
   - **Name:** `DISCOGS_CONSUMER_SECRET` → **Value:** your consumer secret  

### Where to set them

- **Local:** in a `.env` file (if you use something like `python-dotenv`) or export in the shell before running the app.
- **Vercel:** **Settings** → **Environment Variables** → add `DISCOGS_TOKEN` or both `DISCOGS_CONSUMER_KEY` and `DISCOGS_CONSUMER_SECRET`, then redeploy.

If neither option is set, the “Suggest price from Discogs” button still appears but the API will return “Discogs is not configured.” Discogs applies rate limits (e.g. 60 requests/minute with auth).
