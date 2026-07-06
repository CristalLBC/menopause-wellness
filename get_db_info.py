import base64, json, urllib.request

api_key = base64.b64decode('cm5kXzBza2ZHa05QNG1OWms5TllES3FmV3ZZQ1dYZk8=').decode()

req = urllib.request.Request(
    'https://api.render.com/v1/postgres',
    headers={'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    for db in data:
        print(f'ID: {db.get("id", "?")}')
        print(f'Name: {db.get("database", {}).get("name", "?")}')
        print(f'Service ID: {db.get("database", {}).get("serviceId", "?")}')
        print(f'Connection Info: {json.dumps(db, indent=2)[:500]}')
        print('---')
