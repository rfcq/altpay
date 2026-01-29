# AltPay QR Shop (Python Flask Web App)

AltPay is a Python Flask web application that lets you:

- **Register products** with a **name** and **price**
- Automatically generate a **QR Code** for each product containing its details
- **Scan** a product QR Code using your device's camera to add that item and its price to a **shopping cart**
- **Select products** directly from the list to add them to the cart

The app features a modern web interface with three main sections:

1. **Create / Register Product** – Enter a product name and price, then save to generate a QR code
2. **Registered Products & QR Codes** – View all registered products with their QR codes and an "Add to cart" button
3. **Shopping Cart** – Click "Scan product QR Code" to open the camera scanner, or add items directly from the product list. View cart total.

## Tech Stack

- **Python 3.8+**
- **Flask** – Web framework
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

### 2. Run the Application

```bash
python app.py
```

The app will start on `http://localhost:5000`

Open your browser and navigate to that URL.

### 3. Using the App

- **Register Products**: Fill in the product name and price form, then click "Save product & generate QR"
- **View QR Codes**: Each registered product displays a QR code image
- **Add to Cart**: 
  - Click "Add to cart" button next to any product, OR
  - Click "Scan product QR Code" to open the camera scanner and scan a QR code
- **View Cart**: The shopping cart shows all added items and calculates the total automatically

## Features

- **Pre-registered Products**: The app starts with sample products (Latte, Cappuccino, Espresso)
- **QR Code Generation**: Each product gets a unique QR code containing `{id, name, price}`
- **QR Code Scanning**: Uses browser camera API with jsQR library for real-time scanning
- **Shopping Cart**: Add items via QR scan or direct selection, view running total
- **Session Storage**: Products and cart are stored in Flask session (upgrade to database for production)

## Production Deployment

For production use:

1. **Change the secret key** in `app.py`:
   ```python
   app.secret_key = 'your-secret-key-change-in-production'
   ```

2. **Use a database** instead of session storage for products and cart

3. **Set up proper WSGI server** (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

4. **Configure HTTPS** for camera access (required in production)

## API Endpoints

- `GET /` – Main page
- `POST /api/products` – Add a new product
- `GET /api/products/<id>/qr` – Get QR code image for a product
- `POST /api/cart` – Add item to cart (by product_id or scanned QR data)
- `GET /api/cart` – Get current cart
- `DELETE /api/cart` – Clear cart

## Browser Compatibility

- **Chrome/Edge**: Full support (camera API works)
- **Firefox**: Full support
- **Safari**: Full support (iOS 11+)
- **Mobile browsers**: Works on iOS Safari and Chrome Android

**Note**: Camera access requires HTTPS in production environments.
