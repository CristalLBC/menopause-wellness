import base64, json, urllib.request, time

api_key = base64.b64decode('cm5kXzBza2ZHa05QNG1OWms5TllES3FmV3ZZQ1dYZk8=').decode()

# Check deploy status
url = 'https://api.render.com/v1/services/srv-d949tv9kh4rs73eps1c0/deploys?limit=5'
req = urllib.request.Request(url, headers={
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_key}'
})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    for d in data:
        deploy = d.get('deploy', {})
        status = deploy.get('status', '?')
        commit = deploy.get('commit', {}).get('message', '?')[:60]
        created = deploy.get('createdAt', '?')[:19]
        print(f'[{created}] {status:12s} | {commit}')
