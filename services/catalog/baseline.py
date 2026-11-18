"""Verify one isolated CPU lab instance and the three deployed Catalog fixtures."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import time
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
FIXTURE = (ROOT / 'src/main/resources/catalog-products.json').read_bytes()


def docker(*argv):
    return subprocess.check_output(['docker', *argv], text=True, timeout=30).strip()


def fixture(container, file):
    docker('cp', f'{container}:/app/service.jar', str(file))
    with ZipFile(file) as jar:
        found = jar.read('BOOT-INF/classes/catalog-products.json')
    assert found == FIXTURE, f'fixture mismatch in {container}'


def main():
    replicas = [docker('ps', '-q', '--filter', 'label=com.docker.compose.project=nt533-managed-v2',
                       '--filter', f'label=com.docker.compose.service=catalog-{index}') for index in range(1, 4)]
    assert len(set(replicas)) == 3 and all(replicas), replicas
    images = {f'C{index}': docker('inspect', '--format', '{{.Image}}', replica)
              for index, replica in enumerate(replicas, 1)}
    with TemporaryDirectory(prefix='nt533-catalog-baseline-') as folder:
        jar = Path(folder) / 'catalog.jar'
        for replica in replicas:
            fixture(replica, jar)
        digest = b'NT533-v1'
        for _ in range(1000):
            digest = sha256(digest).digest()
        checksum = digest.hex()
        for instance, image in images.items():
            isolated = docker('run', '-d', '--rm', '--network', 'none', '--read-only', '--tmpfs', '/tmp',
                              '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--cpus', '0.5', '--memory', '512m',
                              '--label', 'nt533.managed=catalog-baseline', '-e', 'SPRING_PROFILES_ACTIVE=lab',
                              '-e', f'INSTANCE_ID={instance}', '-e', 'NT533_BENCH_ITERATIONS=1000',
                              '-e', 'JAVA_TOOL_OPTIONS=-Xms256m -Xmx256m -XX:+UseG1GC', image)
            try:
                end = time.monotonic() + 60
                while time.monotonic() < end:
                    try:
                        docker('exec', isolated, 'wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:8082/actuator/health/readiness')
                        break
                    except subprocess.CalledProcessError:
                        time.sleep(1)
                else:
                    raise RuntimeError('isolated Catalog did not become ready')
                fixture(isolated, jar)
                work = json.loads(docker('exec', isolated, 'wget', '-q', '-O', '-',
                                         'http://127.0.0.1:8080/internal/bench?profile=cpu-fixed'))
                assert work['instanceId'] == instance and work['iterations'] == 1000 and work['checksum'] == checksum, work
            finally:
                docker('stop', '--time', '3', isolated)
    print(json.dumps({'singleInstance': 'C1', 'deployedReplicas': 3, 'images': images,
                      'fixture_sha256': sha256(FIXTURE).hexdigest(), 'cpu_checksum': checksum, 'iterations': 1000}))


if __name__ == '__main__':
    main()
