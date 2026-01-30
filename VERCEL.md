# Deploying AltPay on Vercel with persistent data

On Vercel, the app runs as serverless functions. **Without a database**, it uses SQLite in `/tmp`, which is **ephemeral**: each request can run on a different instance, so users, products, and sessions can disappear between visits. That’s why “the registry seems to destroy” after one login.

To keep **auth and data persistent**, you need a real database and to set `DATABASE_URL`.

---

## 1. Add a database

### Option A: Vercel Postgres (recommended)

1. In the [Vercel Dashboard](https://vercel.com/dashboard), open your project.
2. Go to **Storage** → **Create Database** → **Postgres**.
3. Create the database and connect it to your project.
4. Vercel will add `POSTGRES_URL` (or `DATABASE_URL`) to your project’s environment variables. The app reads either one.

### Option B: External Postgres (Neon, Supabase, etc.)

1. Create a Postgres database (e.g. [Neon](https://neon.tech), [Supabase](https://supabase.com)).
2. Copy the connection string (e.g. `postgresql://user:pass@host/dbname?sslmode=require`).
3. In your Vercel project: **Settings** → **Environment Variables** → add:
   - **Name:** `DATABASE_URL`
   - **Value:** your full Postgres URL (use `postgresql://`, not `postgres://`; the app normalizes it if needed).

---

## 2. Required environment variables (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` or `POSTGRES_URL` | Yes, for persistent data | Postgres connection string. Without this, the app uses SQLite in `/tmp` and data is not persistent. |
| `APP_ENCRYPTION_KEY` | Yes on Vercel | Base64 Fernet key for encrypting usernames/emails. Generate one: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `SECRET_KEY` | Recommended | Flask secret for sessions and password hashing. Use a long random string in production. |

Set these in **Settings** → **Environment Variables** for your project, then **redeploy**.

---

## 3. After setting `DATABASE_URL`

- Tables are created automatically on first request (SQLAlchemy `create_all`).
- User accounts, products, and cart data persist across requests and deployments.
- The in-app “Data is not persistent” warning disappears.

---

## Summary

- **No `DATABASE_URL`** → SQLite in `/tmp` → data is ephemeral, “registry” can disappear.
- **With `DATABASE_URL`** (Vercel Postgres or external Postgres) → data is persistent.

Add a Postgres database, set `DATABASE_URL` (and `APP_ENCRYPTION_KEY`), redeploy, and your auth and data will persist.
