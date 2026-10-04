"""Run inside backend after starting the monitoring Compose overlay."""
import json
import time
from urllib.parse import urlencode
from urllib.request import urlopen, Request

def read(url, data=None):
    request = Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=5) as response:
        return json.load(response)

def wait_for(label, check):
    last_error = None
    for _ in range(60):
        try:
            if check():
                print(label + ': passed')
                return
        except (OSError, ValueError, KeyError) as error:
            last_error = error
        time.sleep(1)
    raise RuntimeError(f'{label}: not ready; {last_error}')

job = read('http://backend:8000/api/jobs', json.dumps({'text': 'one two two'}).encode())
wait_for('Worker', lambda: read('http://backend:8000/api/jobs/' + job['id'])['status'] == 'done')
query = urlencode({'query': 'textlab_jobs_submitted_total'})
wait_for('Prometheus metric', lambda: bool(read('http://prometheus:9090/api/v1/query?' + query)['data']['result']))
query = urlencode({'query': '{job="textlab",service="backend"}'})
wait_for('Loki logs', lambda: bool(read('http://loki:3100/loki/api/v1/query_range?' + query)['data']['result']))
wait_for('Grafana', lambda: read('http://grafana:3000/api/health')['database'] == 'ok')
wait_for('Grafana dashboard', lambda: read('http://grafana:3000/api/dashboards/uid/textlab')['dashboard']['title'] == 'TextLab')
