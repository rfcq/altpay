# AltPay QR Shop (Python Flask Web App)

AltPay is a Python Flask web application with user authentication that lets you:

- **User Registration & Login** – Secure user accounts with password hashing
- **Register products** with a **name** and **price**
- Automatically generate a **QR Code** for each product containing its details
- **Scan** a product QR Code using your device's camera to add that item and its price to a **shopping cart**
- **Select products** directly from the list to add them to the cart

The app features a modern web interface with:

1. **Authentication Pages** – Login and registration with form validation
2. **Create / Register Product** – Enter a product name and price, then save to generate a QR code
3. **Registered Products & QR Codes** – View all registered products with their QR codes and an "Add to cart" button
4. **Shopping Cart** – Click "Scan product QR Code" to open the camera scanner, or add items directly from the product list. View cart total.

## Tech Stack

- **Python 3.8+**
- **Flask** – Web framework
- **Flask-SQLAlchemy** – Database ORM
- **SQLite** – Database (default, can be upgraded to PostgreSQL/MySQL)
- **Werkzeug** – Password hashing and security utilities
- **qrcode** – QR code generation
- **Pillow** – Image processing
- **jsQR** (JavaScript) – QR code scanning in the browser

## Getting Started

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or using a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize the Database

The database will be automatically created on first run. The app uses SQLite by default, which creates a local `altpay.db` file.

### 3. Run the Application

```bash
python app.py
```

The app will start on `http://localhost:5000`

Open your browser and navigate to that URL.

### 4. Using the App

**First Time Setup:**
1. **Register an Account**: Click "Register here" on the login page
   - Enter a username (min. 3 characters)
   - Enter your email address
   - Create a password (min. 6 characters)
   - Confirm your password
2. **Login**: After registration, login with your username and password

**Main Features:**
- **Register Products**: Fill in the product name and price form, then click "Save product & generate QR"
- **View QR Codes**: Each registered product displays a QR code image
- **Add to Cart**: 
  - Click "Add to cart" button next to any product, OR
  - Click "Scan product QR Code" to open the camera scanner and scan a QR code
- **View Cart**: The shopping cart shows all added items and calculates the total automatically
- **Logout**: Click the "Logout" button in the top right corner

## Features

- **User Authentication**: Secure registration and login with password hashing
- **Database Persistence**: User accounts and products are stored in SQLite database
- **Pre-registered Products**: The app starts with sample products (Latte, Cappuccino, Espresso)
- **QR Code Generation**: Each product gets a unique QR code containing `{id, name, price}`
- **QR Code Scanning**: Uses browser camera API with jsQR library for real-time scanning
- **Shopping Cart**: Add items via QR scan or direct selection, view running total (stored in session)
- **Protected Routes**: All main features require user authentication

## Database Schema

The app uses SQLite with the following tables:

- **User**: Stores user accounts (id, username, email, password_hash, created_at)
- **Product**: Stores products (id, name, price, created_at, user_id)

## Production Deployment

For production use:

1. **Change the secret key** using an environment variable:
   ```bash
   export SECRET_KEY='your-very-secure-secret-key-here'
   ```
   Or update `app.py` to use environment variables.

2. **Upgrade to PostgreSQL or MySQL** for better performance:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/altpay'
   ```

3. **Set up proper WSGI server** (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

4. **Configure HTTPS** for camera access (required in production)

5. **Add rate limiting** and other security measures for production use

## Routes

**Authentication (Public):**
- `GET /login` – Login page
- `POST /login` – Process login
- `GET /register` – Registration page
- `POST /register` – Process registration

**Main App (Protected - requires login):**
- `GET /` – Main page (product management and cart)
- `POST /api/products` – Add a new product
- `GET /api/products/<id>/qr` – Get QR code image for a product
- `POST /api/cart` – Add item to cart (by product_id or scanned QR data)
- `GET /api/cart` – Get current cart
- `DELETE /api/cart` – Clear cart
- `GET /logout` – Logout user

## Browser Compatibility

- **Chrome/Edge**: Full support (camera API works)
- **Firefox**: Full support
- **Safari**: Full support (iOS 11+)
- **Mobile browsers**: Works on iOS Safari and Chrome Android

**Note**: Camera access requires HTTPS in production environments.
