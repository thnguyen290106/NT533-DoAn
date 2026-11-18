"""Probe one disposable NGINX configuration from its verified peer."""

from hashlib import sha256
import json
import sys
import urllib.error
import urllib.request


def fetch(port, route, client='c-0123456789abcdef', ip=None):
    request_id = '1' * 32
    headers = {'X-Request-ID': request_id}
    if client is not None:
        headers['X-Lab-Client-ID'] = client
    if ip is not None:
        headers['X-Lab-Source-IP'] = ip
    try:
        with urllib.request.urlopen(urllib.request.Request(f'http://gateway:{port}{route}', headers=headers), timeout=5) as r:
            assert r.headers['X-Request-ID'] == request_id, r.headers
            return r.status, json.load(r)
    except urllib.error.HTTPError as error:
        return error.code, None


def check(algorithm, membership, simulated=False):
    route = '/bench/inventory?profile=mapping'
    source = '10.250.0.10' if simulated else None
    assert fetch(8080, route)[0] == 404
    assert fetch(8081, route, client=None, ip=source)[0] == 400
    assert fetch(8081, route, client='c-INVALID', ip=source)[0] == 400
    if simulated:
        assert fetch(8081, route, ip='8.8.8.8')[0] == 400
    ids = ['c-' + sha256(f'fixture-{j}'.encode()).hexdigest()[:16] for j in range(60)]

    def instance(client):
        status, body = fetch(8081, route, client, source)
        assert status == 200 and body['profile'] == 'mapping', (status, body)
        return body['instanceId']

    first = [instance(client) for client in ids]
    expected = {f'I{n}' for n in range(1, membership + 1)}
    if algorithm == 'iph':
        assert len(set(first)) == 1 and set(first) <= expected, set(first)
    else:
        assert set(first) == expected, set(first)
    if algorithm in ('ch-id', 'gh-id'):
        assert first == [instance(client) for client in ids], 'Key moved without membership change'
    digest = sha256(json.dumps(list(zip(ids, first)), separators=(',', ':')).encode()).hexdigest()
    print(json.dumps({'algorithm': algorithm, 'members': list(sorted(set(first))), 'samples': len(first),
                      'mapping_sha256': digest}))


if __name__ == '__main__':
    check(sys.argv[1], int(sys.argv[2]), len(sys.argv) > 3)
