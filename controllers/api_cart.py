"""
API controller: cart (get, add, clear, checkout).
"""
import uuid
from flask import Blueprint, request, session, jsonify
from extensions import db
from models import Product, Sale, SaleItem
from utils.i18n import t as _t
from controllers.decorators import login_required

api_cart_bp = Blueprint('api_cart', __name__, url_prefix='/api')


@api_cart_bp.route('/cart', methods=['GET'])
@login_required
def get_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] for item in cart)
    return jsonify({'cart': cart, 'total': total})


@api_cart_bp.route('/cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if product_id:
        product = Product.query.get(product_id)
        if product:
            cart = session.get('cart', [])
            cart.append({'id': str(uuid.uuid4()), 'name': product.name, 'price': product.price, 'product_id': product.id})
            session['cart'] = cart
            return jsonify({'message': _t('msg_added_to_cart'), 'cart': cart}), 200
    if 'name' in data and 'price' in data:
        cart = session.get('cart', [])
        cart.append({
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'price': float(data['price']),
            'product_id': data.get('id'),
        })
        session['cart'] = cart
        return jsonify({'message': _t('msg_added_to_cart'), 'cart': cart}), 200
    return jsonify({'error': _t('err_invalid_data')}), 400


@api_cart_bp.route('/cart', methods=['DELETE'])
@login_required
def clear_cart():
    session['cart'] = []
    return jsonify({'message': _t('msg_cart_cleared')}), 200


@api_cart_bp.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    cart = session.get('cart', [])
    if not cart:
        return jsonify({'error': _t('checkout_cart_empty')}), 400
    user_id = session.get('user_id')
    try:
        sale = Sale(user_id=user_id)
        db.session.add(sale)
        db.session.flush()
        for item in cart:
            si = SaleItem(sale_id=sale.id, name=item.get('name', ''), price=float(item.get('price', 0)), product_id=item.get('product_id'))
            db.session.add(si)
        db.session.commit()
        session['cart'] = []
        return jsonify({
            'message': _t('checkout_success'),
            'sale_id': sale.id,
            'items_count': len(cart),
        }), 200
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(e)
        return jsonify({'error': _t('checkout_error') + ' ' + str(e)}), 500
