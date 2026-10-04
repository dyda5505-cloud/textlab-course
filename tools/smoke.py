"""Run against the real Compose entry point, fail on queue/HTTP errors."""
import json
import time
from urllib.request import Request, urlopen

def read(request):
    with urlopen(request, timeout=5) as response:
        return json.load(response)

job = read(Request('http://127.0.0.1:8080/api/jobs',
                   data=json.dumps({'text': 'Привет привет мир'}).encode(),
                   headers={'Content-Type': 'application/json'}))
for _ in range(60):
    result = read('http://127.0.0.1:8080/api/jobs/' + job['id'])
    if result['status'] == 'done':
        if result['result']['words'] != 3:
            raise RuntimeError('Unexpected word count')
        print('HTTP smoke passed: nginx -> backend -> queue -> worker -> result')
        break
    if result['status'] == 'failed':
        raise RuntimeError(result['error'])
    time.sleep(0.5)
else:
    raise TimeoutError('Worker did not finish the job')
