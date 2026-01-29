from flask import Flask, render_template, request, jsonify, session, send_file
import qrcode
import io
import json
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Global products storage (shared across all users)
# In production, replace with a database
products = [
    {'id': '1', 'name': 'Latte', 'price': 4.5},
    {'id': '2', 'name': 'Cappuccino', 'price': 5.2},
    {'id': '3', 'name': 'Espresso', 'price': 3.0},
]


@app.before_request
def initialize_session():
    """Initialize cart in session if it doesn't exist"""
    if 'cart' not in session:
        session['cart'] = []


@app.route('/')
def index():
    cart = session.get('cart', [])
    cart_total = sum(item['price'] for item in cart)
    return render_template('index.html', products=products, cart=cart, cart_total=cart_total)


@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    name = data.get('name', '').strip()
    price = data.get('price', 0)
    
    try:
        price = float(price)
        if not name or price <= 0:
            return jsonify({'error': 'Invalid name or price'}), 400
        
        product = {
            'id': str(uuid.uuid4()),
            'name': name,
            'price': round(price, 2)
        }
        
        products.append(product)
        
        return jsonify(product), 201
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid price format'}), 400


@app.route('/api/products/<product_id>/qr')
def get_product_qr(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Generate QR code with product data
    qr_data = json.dumps({
        'id': product['id'],
        'name': product['name'],
        'price': product['price']
    })
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')


@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    
    # Check if it's a product ID from the list
    product_id = data.get('product_id')
    if product_id:
        product = next((p for p in products if p['id'] == product_id), None)
        if product:
            cart = session.get('cart', [])
            cart.append({
                'id': str(uuid.uuid4()),
                'name': product['name'],
                'price': product['price']
            })
            session['cart'] = cart
            return jsonify({'message': 'Added to cart', 'cart': cart}), 200
    
    # Check if it's scanned QR data
    if 'name' in data and 'price' in data:
        cart = session.get('cart', [])
        cart.append({
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'price': float(data['price'])
        })
        session['cart'] = cart
        return jsonify({'message': 'Added to cart', 'cart': cart}), 200
    
    return jsonify({'error': 'Invalid data'}), 400


@app.route('/api/cart', methods=['GET'])
def get_cart():
    cart = session.get('cart', [])
    cart_total = sum(item['price'] for item in cart)
    return jsonify({'cart': cart, 'total': cart_total})


@app.route('/api/cart', methods=['DELETE'])
def clear_cart():
    session['cart'] = []
    return jsonify({'message': 'Cart cleared'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
