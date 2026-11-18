"""Audit the same Quote cohort in client, NGINX, app logs and live metrics."""

import collections
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request


def docker(*args):
    return subprocess.check_output(['docker', *args], text=True, timeout=25)


def engine(project):
    ids = docker('ps', '-q', '--filter', 'label=com.docker.compose.project=' + project).split()
    return {d['Config']['Labels']['com.docker.compose.service']: d['Id'] for d in json.loads(docker('inspect', *ids))}


def metrics(containers):
    totals = collections.Counter()
    for name, container in containers.items():
        service = name.split('-')[0]
        if service not in ('catalog', 'inventory', 'order'):
            continue
        text = docker('exec', container, 'wget', '-q', '-O-', 'http://127.0.0.1:8082/actuator/prometheus')
        assert 'jvm_memory_used_bytes' in text, name
        for line in text.splitlines():
            match = re.fullmatch(r'(nt533_(?:requests_total|request_duration_seconds_count|downstream_duration_seconds_count))\{(.*)\} ([0-9.]+)', line)
            if match:
                metric, labels, value = match.groups()
                assert 'request_id=' not in labels and 'exported_instance=' not in labels
                totals[(service, metric)] += int(float(value))
    return totals


def quote(base, product, quantity, expected):
    payload = json.dumps({'productId': product, 'quantity': quantity}).encode()
    request = urllib.request.Request(base + '/api/orders/quote', data=payload,
                                     headers={'Content-Type':'application/json'})
    try:
        response = urllib.request.urlopen(request, timeout=7)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = json.load(response)
        assert response.status == expected and re.fullmatch('[0-9a-f]{32}', body['requestId'])
        assert response.headers['X-Request-ID'] == body['requestId']
        return body['requestId']


def lines(container):
    for line in docker('logs', '--tail', '4000', container).splitlines():
        if line.startswith('{'):
            yield json.loads(line)


def audit(base):
    live = engine('nt533-managed-v2')
    before = metrics(live)
    ok, absent, bad = (quote(base, 'P001', 2, 200), quote(base, 'P999', 2, 404), quote(base, 'P001', 0, 400))
    cohort = {ok, absent, bad}
    seen = collections.Counter((row['request_id'], row['service'], row['call_id'], row['status'])
                               for name, container in live.items() if name.startswith(('catalog-', 'inventory-', 'order-'))
                               for row in lines(container) if row.get('request_id') in cohort)
    expected = {(ok, 'order', None, 200): 1, (absent, 'order', None, 404): 1, (bad, 'order', None, 400): 1,
                (ok, 'catalog', ok+'-catalog', 200): 1, (absent, 'catalog', absent+'-catalog', 404): 1,
                (ok, 'inventory', ok+'-inventory', 200): 1}
    assert seen == expected, (seen, expected)
    gateway = [row for row in lines(live['nginx']) if row.get('request_id') in cohort]
    assert len(gateway) == 6 and {row['request_id'] for row in gateway} == cohort, gateway
    after = metrics(live)
    counts = {service: after[(service, 'nt533_requests_total')] - before[(service, 'nt533_requests_total')]
              for service in ('catalog', 'inventory', 'order')}
    assert counts == {'catalog': 2, 'inventory': 1, 'order': 3}, counts
    for service in counts:
        key = (service, 'nt533_request_duration_seconds_count')
        assert after[key] - before[key] == counts[service], (service, before[key], after[key])
    key = ('order', 'nt533_downstream_duration_seconds_count')
    assert after[key] - before[key] == 3
    print(json.dumps({'clientRequests': 3, 'appRecords': len(seen), 'gatewayRecords': len(gateway),
                      'requestCounters': counts, 'downstreamObservations': 3}))


if __name__ == '__main__':
    audit(sys.argv[1])
