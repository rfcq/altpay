"""
API controller: products (CRUD, import, QR).
"""
import csv
import io
import json
import os
import uuid
from flask import Blueprint, request, session, jsonify, send_file, current_app
from extensions import db
from models import Product
from utils.i18n import t as _t
from controllers.decorators import login_required
import qrcode

api_products_bp = Blueprint('api_products', __name__, url_prefix='/api')

ALLOWED_COVER_MIMETYPES = {'image/jpeg', 'image/png'}
COVER_EXT = {'image/jpeg': '.jpg', 'image/png': '.png'}


def _parse_product_payload():
    """Return (name, price, grading, publisher, year) from JSON or form."""
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form
    name = (data.get('name') or '').strip()
    try:
        price = float(data.get('price', 0))
    except (TypeError, ValueError):
        price = 0
    grading = (data.get('grading') or '').strip() or None
    publisher = (data.get('publisher') or '').strip() or None
    year_val = data.get('year')
    year = None
    if year_val is not None and year_val != '':
        try:
            year = int(year_val)
        except (TypeError, ValueError):
            pass
    return name, price, grading, publisher, year


def _save_cover_file(product_id, file_storage):
    """Save cover file to static/uploads; return relative path or None."""
    if not file_storage or not file_storage.filename:
        return None
    mimetype = (file_storage.content_type or '').split(';')[0].strip().lower()
    if mimetype not in ALLOWED_COVER_MIMETYPES:
        return None
    ext = COVER_EXT.get(mimetype, '.jpg')
    uploads_dir = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    safe_name = product_id + ext
    path = os.path.join(uploads_dir, safe_name)
    file_storage.save(path)
    return 'uploads/' + safe_name


def _remove_cover_file(cover_path):
    """Remove cover file from static/uploads if it exists."""
    if not cover_path:
        return
    try:
        full = os.path.join(current_app.static_folder, cover_path)
        if os.path.isfile(full):
            os.remove(full)
    except Exception:
        pass


def parse_import_row(row):
    key_map = {}
    for k in row:
        if k is None:
            continue
        s = (k if isinstance(k, str) else str(k)).strip().lstrip('\ufeff')
        if s:
            key_map[s.lower()] = k
    name_key = next((key_map[k] for k in ('name', 'nome', 'product', 'produto') if k in key_map), None)
    price_key = next((key_map[k] for k in ('price', 'preco', 'preço') if k in key_map), None)
    if not name_key or not price_key:
        return None, None
    name = (row.get(name_key) or '').strip()
    if not name:
        return None, None
    try:
        price = float(str(row.get(price_key) or '0').replace(',', '.').strip())
    except (TypeError, ValueError):
        return name, None
    if price <= 0:
        return name, None
    return name, round(price, 2)


@api_products_bp.route('/products', methods=['POST'])
@login_required
def add_product():
    name, price, grading, publisher, year = _parse_product_payload()
    if not name or price <= 0:
        return jsonify({'error': _t('err_invalid_name_price')}), 400
    user_id = session.get('user_id')
    existing = Product.query.filter(Product.user_id == user_id).all()
    if any(p.name.lower() == name.lower() for p in existing):
        return jsonify({'error': _t('err_product_already_exists')}), 409
    product_id = str(uuid.uuid4())
    cover_path = None
    cover_file = request.files.get('cover')
    if cover_file and cover_file.filename:
        mimetype = (cover_file.content_type or '').split(';')[0].strip().lower()
        if mimetype not in ALLOWED_COVER_MIMETYPES:
            return jsonify({'error': _t('err_cover_format')}), 400
        cover_path = _save_cover_file(product_id, cover_file)
    product = Product(
        id=product_id,
        name=name,
        price=round(price, 2),
        grading=grading,
        publisher=publisher,
        year=year,
        cover_path=cover_path,
        user_id=user_id,
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@api_products_bp.route('/products/import', methods=['POST'])
@login_required
def import_products():
    if 'file' not in request.files:
        return jsonify({'error': _t('import_no_file')}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': _t('import_no_file')}), 400
    fn = (f.filename or '').lower()
    if not (fn.endswith('.csv') or fn.endswith('.json')):
        return jsonify({'error': _t('import_bad_type')}), 400
    try:
        content = f.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='replace')
        if content.startswith('\ufeff'):
            content = content[1:]
        created = 0
        skipped = 0
        errors = []
        user_id = session.get('user_id')
        existing_names = {p.name.lower() for p in Product.query.filter(Product.user_id == user_id).all()}
        if fn.endswith('.csv'):
            for delimiter in (';', ','):
                reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
                if not reader.fieldnames or len(reader.fieldnames) < 2:
                    continue
                rows = list(reader)
                if not rows:
                    continue
                for i, row in enumerate(rows):
                    name, price = parse_import_row(row)
                    if name is None and price is None:
                        continue
                    if price is None:
                        errors.append(_t('import_row_invalid', row=i + 2))
                        continue
                    if name.lower() in existing_names:
                        skipped += 1
                        continue
                    db.session.add(Product(id=str(uuid.uuid4()), name=name, price=price, user_id=user_id))
                    created += 1
                    existing_names.add(name.lower())
                break
        else:
            data = json.loads(content)
            if isinstance(data, dict) and 'products' in data:
                items = data['products']
            elif isinstance(data, list):
                items = data
            else:
                return jsonify({'error': _t('import_json_format')}), 400
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(_t('import_row_invalid', row=i + 1))
                    continue
                name, price = parse_import_row(item)
                if name is None and price is None:
                    continue
                if price is None:
                    errors.append(_t('import_row_invalid', row=i + 1))
                    continue
                if name.lower() in existing_names:
                    skipped += 1
                    continue
                db.session.add(Product(id=str(uuid.uuid4()), name=name, price=price, user_id=user_id))
                created += 1
                existing_names.add(name.lower())
        db.session.commit()
        msg = _t('import_success_skipped', created=created, skipped=skipped) if skipped else _t('import_success', count=created)
        return jsonify({'message': msg, 'created': created, 'skipped': skipped, 'errors': errors[:20]}), 200
    except json.JSONDecodeError as e:
        return jsonify({'error': _t('import_json_invalid') + ' ' + str(e)}), 400
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(e)
        return jsonify({'error': _t('import_error') + ' ' + str(e)}), 500


@api_products_bp.route('/products/<product_id>/qr')
@login_required
def get_product_qr(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': _t('err_product_not_found')}), 404
    qr_data = json.dumps({'id': product.id, 'name': product.name, 'price': product.price})
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@api_products_bp.route('/products/<product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    name, price, grading, publisher, year = _parse_product_payload()
    if not name or price <= 0:
        return jsonify({'error': _t('err_invalid_name_price')}), 400
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': _t('err_product_not_found')}), 404
    product.name = name
    product.price = round(price, 2)
    product.grading = grading
    product.publisher = publisher
    product.year = year
    cover_file = request.files.get('cover')
    if cover_file and cover_file.filename:
        mimetype = (cover_file.content_type or '').split(';')[0].strip().lower()
        if mimetype not in ALLOWED_COVER_MIMETYPES:
            return jsonify({'error': _t('err_cover_format')}), 400
        _remove_cover_file(product.cover_path)
        product.cover_path = _save_cover_file(product_id, cover_file)
    db.session.commit()
    return jsonify(product.to_dict()), 200


@api_products_bp.route('/products/<product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': _t('err_product_not_found')}), 404
    _remove_cover_file(product.cover_path)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': _t('msg_product_deleted')}), 200


@api_products_bp.route('/products/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_products():
    data = request.get_json() or {}
    product_ids = data.get('product_ids') or []
    if not isinstance(product_ids, list):
        return jsonify({'error': _t('err_invalid_product_ids')}), 400
    if not product_ids:
        return jsonify({'error': _t('err_no_valid_products')}), 400
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    for p in products:
        _remove_cover_file(p.cover_path)
        db.session.delete(p)
    db.session.commit()
    n = len(products)
    msg = _t('msg_one_product_deleted') if n == 1 else _t('msg_products_deleted', n=n)
    return jsonify({'message': msg, 'deleted_count': n}), 200
