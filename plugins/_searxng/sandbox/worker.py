"""Run SearXNG's WSGI search endpoint inside the guest without a listening port."""
import os
import secrets

os.environ['SEARXNG_SETTINGS_PATH'] = '/plugin/sandbox/settings.yml'
os.environ['SEARXNG_SECRET'] = secrets.token_hex(32)

from searx.webapp import app


def handle(payload):
    query = payload.get('query')
    if not isinstance(query, str) or not query.strip() or len(query) > 8192:
        raise ValueError('Search query must contain between 1 and 8192 characters')
    with app.test_client() as client:
        response = client.post('/search', data={'q': query, 'format': 'json'})
        if response.status_code != 200:
            raise RuntimeError(f'SearXNG returned HTTP {response.status_code}')
        result = response.get_json()
        if not isinstance(result, dict) or not isinstance(result.get('results'), list):
            raise RuntimeError('SearXNG returned an invalid search response')
        return result
