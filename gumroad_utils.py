"""
Gumroad license verification utilities.

API reference: https://app.gumroad.com/api
"""

import os
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode


GUMROAD_API_BASE = 'https://api.gumroad.com/v2'


def get_product_id():
    """Return the configured Gumroad product permalink/ID."""
    return os.environ.get('GUMROAD_PRODUCT_ID', '')


def get_api_key():
    """Return the Gumroad API key (optional, for admin operations)."""
    return os.environ.get('GUMROAD_API_KEY', '')


def verify_license(license_key, product_id=None):
    """
    Verify a license key against Gumroad's API.

    Returns a dict with:
      - success (bool): whether the key is valid
      - purchase (dict): purchase info if valid (email, product_name, etc.)
      - error (str): error message if failed

    Docs: https://app.gumroad.com/api#license
    """
    if not product_id:
        product_id = get_product_id()

    if not product_id:
        return {'success': False, 'error': 'Gumroad product not configured.'}

    if not license_key or not license_key.strip():
        return {'success': False, 'error': 'License key is required.'}

    data = urlencode({
        'product_id': product_id,
        'license_key': license_key.strip()
    }).encode('utf-8')

    try:
        req = Request(f'{GUMROAD_API_BASE}/licenses/verify', data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))

        if result.get('success'):
            purchase = result.get('purchase', {})
            return {
                'success': True,
                'purchase': purchase,
                'uses': result.get('uses', 0),
                'email': purchase.get('email', ''),
                'product_name': purchase.get('product_name', ''),
                'subscription_id': purchase.get('subscription_id', ''),
                'subscription_cancelled_at': purchase.get('subscription_cancelled_at'),
                'subscription_failed_at': purchase.get('subscription_failed_at'),
                'sale_id': purchase.get('sale_id', '')
            }
        else:
            return {
                'success': False,
                'error': result.get('message', 'Invalid license key.')
            }

    except Exception as e:
        return {'success': False, 'error': f'Could not verify license: {str(e)}'}


def check_subscription_active(license_key, product_id=None):
    """
    Check if a subscription license is still active (not cancelled/failed).
    Returns (is_active, details_dict).
    """
    result = verify_license(license_key, product_id)
    if not result['success']:
        return False, result

    purchase = result.get('purchase', {})
    # For subscription products, check cancellation / failure status
    cancelled = purchase.get('subscription_cancelled_at')
    failed = purchase.get('subscription_failed_at')

    if cancelled or failed:
        return False, {
            'success': False,
            'error': 'Your subscription is no longer active. Please renew on Gumroad.',
            'cancelled_at': cancelled,
            'failed_at': failed
        }

    return True, result
