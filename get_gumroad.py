import base64, json, urllib.request

api_key = base64.b64decode('cm5kXzBza2ZHa05QNG1OWms5TllES3FmV3ZZQ1dYZk8=').decode()

url = 'https://api.render.com/v1/services/srv-d949tv9kh4rs73eps1c0/env-vars'
req = urllib.request.Request(url, headers={
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_key}'
})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    for item in data:
        env = item.get('envVar', {})
        key = env.get('key', '?')
        val = env.get('value', '?')
        if 'GUMROAD' in key or 'PRODUCT' in key:
            print(f'{key}: {val}')
