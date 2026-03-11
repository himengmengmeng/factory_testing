import csv
import io
import json
import time

import jwt
import requests
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

INSTAVIEW_STAGING_URL = 'https://staging.instaview.ai'
INSTAVIEW_PROD_URL = 'https://api-us.instaview.ai'
CLIENT_ID = 'testing_tool'
PARTNER_ID = 'instaview'


# ──────────────────────────── helpers ────────────────────────────

def _api_headers(access_token=None):
    h = {
        'Client-ID': CLIENT_ID,
        'Partner-ID': PARTNER_ID,
        'Content-Type': 'application/json',
    }
    if access_token:
        h['Authorization'] = f'Bearer {access_token}'
    return h


def _decode_jwt(token):
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.InvalidTokenError:
        return None


def _seller_id_from_token(token):
    decoded = _decode_jwt(token)
    if decoded and 'seller_id' in decoded:
        return decoded['seller_id']
    return None


def _token_expired(exp_ts):
    if not exp_ts:
        return True
    return time.time() > (exp_ts - 300)


def _refresh_token(session):
    rt = session.get('tbft_refresh_token')
    if not rt:
        return False
    if _token_expired(session.get('tbft_refresh_token_exp')):
        return False

    base = session.get('tbft_base_url', INSTAVIEW_STAGING_URL)
    resp = requests.post(
        f"{base}/zeus/v2/sellers/auth/login",
        json={"grant_type": "refresh_token", "refresh_token": rt},
        headers=_api_headers(),
        timeout=30,
    )
    if resp.status_code != 200:
        return False

    data = resp.json()
    session['tbft_access_token'] = data['access_token']
    session['tbft_access_token_exp'] = data.get('access_token_exp')
    session['tbft_refresh_token'] = data.get('refresh_token', rt)
    session['tbft_refresh_token_exp'] = data.get('refresh_token_exp')
    sid = _seller_id_from_token(data['access_token'])
    if sid:
        session['tbft_seller_id'] = sid
    return True


def _valid_token(request):
    """Return a valid access-token or None."""
    at = request.session.get('tbft_access_token')
    if not at:
        return None
    if _token_expired(request.session.get('tbft_access_token_exp')):
        if not _refresh_token(request.session):
            return None
        at = request.session.get('tbft_access_token')
    return at


def _base_url(request):
    return request.session.get('tbft_base_url', INSTAVIEW_STAGING_URL)


def _seller_id(request):
    return request.session.get('tbft_seller_id', '')


# ──────────────────────────── decorators ─────────────────────────

def login_required_page(fn):
    @wraps(fn)
    def inner(request, *a, **kw):
        if not _valid_token(request):
            return redirect('tbft_login')
        return fn(request, *a, **kw)
    return inner


def login_required_api(fn):
    @wraps(fn)
    def inner(request, *a, **kw):
        if not _valid_token(request):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return fn(request, *a, **kw)
    return inner


# ──────────────────────────── page views ─────────────────────────

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        base_url = request.POST.get('base_url', INSTAVIEW_STAGING_URL).strip()

        if not email or not password:
            return render(request, 'token_based_factory_tool/login.html', {
                'error': 'Email and password are required',
                'base_url': base_url,
            })

        try:
            resp = requests.post(
                f"{base_url}/zeus/v2/sellers/auth/login",
                json={
                    "email": email,
                    "grant_type": "password",
                    "password": password,
                    "refresh_token": "",
                },
                headers=_api_headers(),
                timeout=30,
            )
        except requests.RequestException as e:
            return render(request, 'token_based_factory_tool/login.html', {
                'error': f'Connection error: {e}',
                'email': email,
                'base_url': base_url,
            })

        if resp.status_code != 200:
            err = f'Login failed (HTTP {resp.status_code})'
            try:
                d = resp.json()
                err = d.get('message', d.get('error', err))
            except Exception:
                pass
            return render(request, 'token_based_factory_tool/login.html', {
                'error': err,
                'email': email,
                'base_url': base_url,
            })

        data = resp.json()
        s = request.session
        s['tbft_access_token'] = data['access_token']
        s['tbft_access_token_exp'] = data.get('access_token_exp')
        s['tbft_refresh_token'] = data.get('refresh_token')
        s['tbft_refresh_token_exp'] = data.get('refresh_token_exp')
        s['tbft_first_name'] = data.get('first_name', '')
        s['tbft_last_name'] = data.get('last_name', '')
        s['tbft_email'] = email
        s['tbft_base_url'] = base_url
        s['tbft_seller_id'] = _seller_id_from_token(data['access_token'])
        return redirect('tbft_dashboard')

    return render(request, 'token_based_factory_tool/login.html', {
        'base_url': INSTAVIEW_PROD_URL,
    })


def logout_view(request):
    keys = [k for k in request.session.keys() if k.startswith('tbft_')]
    for k in keys:
        del request.session[k]
    return redirect('tbft_login')


@login_required_page
def dashboard_view(request):
    return render(request, 'token_based_factory_tool/dashboard.html', _page_ctx(request))


@login_required_page
def operations_view(request):
    return render(request, 'token_based_factory_tool/operations.html', _page_ctx(request))


def _page_ctx(request):
    return {
        'first_name': request.session.get('tbft_first_name', ''),
        'last_name': request.session.get('tbft_last_name', ''),
        'email': request.session.get('tbft_email', ''),
        'seller_id': request.session.get('tbft_seller_id', ''),
    }


# ──────────────────────────── API views ──────────────────────────

@login_required_api
def api_get_variants(request):
    token = _valid_token(request)
    url = f"{_base_url(request)}/zeus/v2/sellers/{_seller_id(request)}/device-variants"
    try:
        r = requests.get(url, headers=_api_headers(token), timeout=30)
        return JsonResponse(r.json(), status=r.status_code, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_api
def api_get_sub_sellers(request):
    token = _valid_token(request)
    url = f"{_base_url(request)}/zeus/v2/sellers/{_seller_id(request)}/sub-sellers"
    try:
        r = requests.get(url, headers=_api_headers(token), timeout=30)
        return JsonResponse(r.json(), status=r.status_code, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_api
def api_get_sub_seller_variants(request, sub_seller_id):
    token = _valid_token(request)
    url = (
        f"{_base_url(request)}/zeus/v2/sellers/{_seller_id(request)}"
        f"/sub-sellers/{sub_seller_id}/device-variants?status=Published"
    )
    try:
        r = requests.get(url, headers=_api_headers(token), timeout=30)
        return JsonResponse(r.json(), status=r.status_code, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_api
def api_query_did(request):
    token = _valid_token(request)
    device_id = request.GET.get('device_id', '').strip()
    if not device_id:
        return JsonResponse({'error': 'device_id is required'}, status=400)

    url = f"{_base_url(request)}/zeus/v3/sellers/{_seller_id(request)}/devices/{device_id}"
    try:
        r = requests.get(url, headers=_api_headers(token), timeout=30)
        return JsonResponse(r.json(), status=r.status_code, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_api
@require_http_methods(["POST"])
def api_bind_did(request):
    """Assign or update a single DID's variant (auto-detects action by default)."""
    token = _valid_token(request)
    base = _base_url(request)
    sid = _seller_id(request)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    did = body.get('did', '').strip()
    variant_id = body.get('variant_id', '').strip()
    sub_seller_id = body.get('sub_seller_id', '').strip()
    action = body.get('action', 'auto')

    if not did or not variant_id:
        return JsonResponse({'error': 'did and variant_id are required'}, status=400)

    headers = _api_headers(token)

    query_data = {}
    if action == 'auto':
        action, query_data = _detect_action(base, sid, did, headers)

        existing_vid = query_data.get('device_variant_id', '')
        if existing_vid == variant_id:
            return JsonResponse({
                'status': 'Success',
                'performed_action': 'none',
                'existing_variant_id': existing_vid,
                'existing_variant_name': query_data.get('device_variant_name', ''),
                'target_variant_id': variant_id,
            })

    if sub_seller_id:
        url = f"{base}/zeus/v2/sellers/{sid}/sub-sellers/{sub_seller_id}/floating-dids/{action}-variant"
    else:
        url = f"{base}/zeus/v2/sellers/{sid}/floating-dids/{action}-variant"

    try:
        r = requests.post(url, json={"did": did, "variant_id": variant_id}, headers=headers, timeout=30)
        resp_data = r.json()
        resp_data['performed_action'] = action
        resp_data['target_variant_id'] = variant_id
        return JsonResponse(resp_data, status=r.status_code, safe=False)
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required_api
@require_http_methods(["POST"])
def api_batch_bind(request):
    """Process CSV of DIDs: auto-detect assign/update for each row."""
    token = _valid_token(request)
    base = _base_url(request)
    sid = _seller_id(request)
    headers = _api_headers(token)

    variant_id = request.POST.get('variant_id', '').strip()
    sub_seller_id = request.POST.get('sub_seller_id', '').strip()
    csv_file = request.FILES.get('csv_file')

    if not variant_id:
        return JsonResponse({'error': 'variant_id is required'}, status=400)
    if not csv_file:
        return JsonResponse({'error': 'CSV file is required'}, status=400)

    try:
        text = csv_file.read().decode('utf-8-sig')
        rows = list(csv.DictReader(io.StringIO(text)))
    except Exception as e:
        return JsonResponse({'error': f'CSV parse error: {e}'}, status=400)

    if not rows:
        return JsonResponse({'error': 'CSV is empty'}, status=400)

    results = []
    for idx, row in enumerate(rows, 1):
        did = (row.get('Device Id') or row.get('device_id') or '').strip()
        if not did:
            results.append(_row_result(idx, '', 'skipped', '', 'Missing Device Id'))
            continue

        action, _ = _detect_action(base, sid, did, headers)

        if sub_seller_id:
            url = f"{base}/zeus/v2/sellers/{sid}/sub-sellers/{sub_seller_id}/floating-dids/{action}-variant"
        else:
            url = f"{base}/zeus/v2/sellers/{sid}/floating-dids/{action}-variant"

        try:
            r = requests.post(url, json={"did": did, "variant_id": variant_id}, headers=headers, timeout=30)
            if r.status_code == 200:
                results.append(_row_result(idx, did, 'success', action, f'{action.capitalize()} successful'))
            else:
                msg = f'HTTP {r.status_code}'
                try:
                    d = r.json()
                    msg = d.get('message', d.get('error', msg))
                except Exception:
                    pass
                results.append(_row_result(idx, did, 'failed', action, msg))
        except requests.RequestException as e:
            results.append(_row_result(idx, did, 'failed', action, str(e)))

    ok = sum(1 for r in results if r['status'] == 'success')
    fail = sum(1 for r in results if r['status'] == 'failed')
    skip = sum(1 for r in results if r['status'] == 'skipped')
    return JsonResponse({'total': len(results), 'success': ok, 'failed': fail, 'skipped': skip, 'results': results})


# ──────────────────────────── internal ───────────────────────────

def _detect_action(base, seller_id, did, headers):
    """Query DID status -> ('assign'|'update', query_data_dict)."""
    try:
        r = requests.get(
            f"{base}/zeus/v3/sellers/{seller_id}/devices/{did}",
            headers=headers, timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            action = 'update' if data.get('device_variant_id') else 'assign'
            return action, data
    except requests.RequestException:
        pass
    return 'assign', {}


def _row_result(row, did, status, action, message):
    return {'row': row, 'device_id': did, 'status': status, 'action': action, 'message': message}
