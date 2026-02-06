"""
Pages controller: create product, products list, cart, users, products sold.
"""
from flask import Blueprint, render_template, session
from models import Product, Sale, User
from controllers.decorators import login_required, admin_required

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/create')
@login_required
def create_product_page():
    return render_template('create_product.html', username=session.get('username'))


@pages_bp.route('/products')
@login_required
def products():
    products_list = [p.to_dict() for p in Product.query.all()]
    return render_template('products.html', products=products_list, username=session.get('username'))


@pages_bp.route('/cart')
@login_required
def cart_page():
    cart = session.get('cart', [])
    cart_total = sum(item['price'] for item in cart)
    return render_template('cart.html', cart=cart, cart_total=cart_total, username=session.get('username'))


@pages_bp.route('/users')
@login_required
@admin_required
def users_page():
    users_list = User.query.order_by(User.created_at.desc()).all()
    users_data = [{'id': u.id, 'username': u.username, 'role': u.role, 'created_at': u.created_at} for u in users_list]
    return render_template('users.html', users=users_data, username=session.get('username'))


@pages_bp.route('/products-sold')
@login_required
def products_sold_page():
    sales = Sale.query.filter_by(user_id=session.get('user_id')).order_by(Sale.created_at.desc()).all()
    sales_data = []
    for s in sales:
        items = [{'name': i.name, 'price': i.price} for i in s.items]
        total = sum(i.price for i in s.items)
        sales_data.append({
            'id': s.id,
            'created_at': s.created_at,
            'line_items': items,
            'total': total,
        })
    return render_template('products_sold.html', sales=sales_data, username=session.get('username'))
