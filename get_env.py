import base64, json, urllib.request

api_key = base64.b64decode('cm5kXzBza2ZHa05QNG1OWms5TllES3FmV3ZZQ1dYZk8=').decode()

# Try to get env vars for the menopause-wellness service
url = 'https://api.render.com/v1/services/srv-d949tv9kh4rs73eps1c0/env-vars'
req = urllib.request.Request(url, headers={
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_key}'
})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        print(json.dumps(data, indent=2)[:4000])
except urllib.error.HTTPError as e:
    print(f'HTTP Error: {e.code}')
    print(e.read().decode())
