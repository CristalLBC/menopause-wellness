import base64, json, urllib.request

api_key = base64.b64decode('cm5kXzBza2ZHa05QNG1OWms5TllES3FmV3ZZQ1dYZk8=').decode()

# Get connection info for the database
req = urllib.request.Request(
    'https://api.render.com/v1/postgres/dpg-d949u28js32c73e0prdg-a',
    headers={'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    print(json.dumps(data, indent=2)[:3000])
