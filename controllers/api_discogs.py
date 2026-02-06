"""
API controller: Discogs price suggestions.
"""
import json
import os
import urllib.request
import urllib.parse
from flask import Blueprint, request, jsonify
from config import get_discogs_credentials, is_discogs_configured
from utils.i18n import t as _t
from controllers.decorators import login_required

api_discogs_bp = Blueprint('api_discogs', __name__, url_prefix='/api')


def discogs_request(path, params=None):
    base = 'https://api.discogs.com'
    url = base + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    token, key, secret = get_discogs_credentials()
    headers = {'User-Agent': 'AltPayShop/1.0 +https://github.com/altpay'}
    if token:
        headers['Authorization'] = f'Discogs token={token}'
    elif key and secret:
        headers['Authorization'] = f'Discogs key={key}, secret={secret}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        from flask import current_app
        current_app.logger.warning('Discogs request failed: %s', e)
        return None


@api_discogs_bp.route('/discogs/price-suggestions')
@login_required
def discogs_price_suggestions():
    q = (request.args.get('q') or '').strip()
    if not q or len(q) < 2:
        return jsonify({'error': _t('discogs_query_too_short'), 'suggestions': []}), 400
    if not is_discogs_configured():
        return jsonify({'error': _t('discogs_not_configured'), 'suggestions': []}), 503
    search = discogs_request('/database/search', {'q': q, 'type': 'release', 'per_page': 8})
    if not search or 'results' not in search:
        return jsonify({'suggestions': []}), 200
    suggestions = []
    curr = (request.args.get('curr') or 'USD').upper()[:3]
    for r in search.get('results', [])[:6]:
        rid = r.get('id')
        title = r.get('title', '')
        if not rid:
            continue
        release = discogs_request(f'/releases/{rid}', {'curr_abbr': curr})
        if not release:
            suggestions.append({'title': title, 'price': None, 'currency': curr, 'release_id': rid})
            continue
        low = release.get('lowest_price')
        price = None
        if low is not None:
            if isinstance(low, dict) and 'value' in low:
                try:
                    price = float(low['value'])
                except (TypeError, ValueError):
                    pass
            else:
                try:
                    price = float(low)
                except (TypeError, ValueError):
                    pass
        curr_code = (release.get('lowest_price') or {}).get('currency') if isinstance(release.get('lowest_price'), dict) else release.get('currency', curr)
        suggestions.append({
            'title': title,
            'price': round(price, 2) if price is not None else None,
            'currency': curr_code or curr,
            'release_id': rid,
        })
    return jsonify({'suggestions': suggestions}), 200
