"""Smoke-test one Catalog image as three standalone Docker containers."""

import argparse
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import ZipFile

FIXTURE = Path(__file__).resolve().parent / "src/main/resources/catalog-products.json"
JAR_FIXTURE = "BOOT-INF/classes/catalog-products.json"
PRODUCTS_PATH = "/api/catalog/products"
REQUEST_ID = "0123456789abcdef0123456789abcdef"


def check_ready(base_url):
    deadline = time.monotonic() + 45
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urlopen(base_url + "/actuator/health/readiness", timeout=2) as reply:
                if json.load(reply).get("status") == "UP":
                    return
        except (URLError, TimeoutError, ConnectionError) as error:
            last_error = error
        time.sleep(0.25)
    raise RuntimeError(f"Catalog readiness timed out at {base_url}: {last_error}")


def check_response(base_url, path, instance, status=200, method="GET"):
    request = Request(
        base_url + path, method=method, headers={"X-Request-ID": REQUEST_ID},
    )
    try:
        reply = urlopen(request, timeout=5)
    except HTTPError as error:
        reply = error
    with reply:
        body = json.load(reply)
        if reply.status != status:
            raise ValueError(f"{instance} {method} {path}: HTTP {reply.status}, {body!r}")
        for field, header, expected in (
            ("requestId", "X-Request-ID", REQUEST_ID),
            ("instanceId", "X-Instance-ID", instance),
        ):
            if body.pop(field, None) != expected or reply.headers.get(header) != expected:
                raise ValueError(f"{instance} {method} {path}: invalid {field} metadata")
        return body, reply.headers


def check_errors(base_url, instance):
    for method, path, status, code in (
        ("GET", PRODUCTS_PATH + "/p001", 400, "INVALID_INPUT"),
        ("GET", PRODUCTS_PATH + "/P999", 404, "PRODUCT_NOT_FOUND"),
        ("GET", PRODUCTS_PATH + "?page=1", 400, "INVALID_INPUT"),
        ("GET", PRODUCTS_PATH + "/P001?unused", 400, "INVALID_INPUT"),
        ("GET", PRODUCTS_PATH + "/P001/other", 404, "ROUTE_NOT_FOUND"),
        ("POST", PRODUCTS_PATH, 405, "METHOD_NOT_ALLOWED"),
    ):
        body, headers = check_response(base_url, path, instance, status, method)
        if set(body) != {"error"} or not isinstance(body["error"], dict):
            raise ValueError(f"{instance} {method} {path}: invalid error envelope")
        error = body["error"]
        if (
            set(error) != {"code", "message"} or error["code"] != code
            or not isinstance(error["message"], str) or not error["message"].strip()
        ):
            raise ValueError(f"{instance} {method} {path}: unexpected error {error!r}")
        if status == 405 and "GET" not in headers.get("Allow", "").replace(" ", "").split(","):
            raise ValueError(f"{instance} {method} {path}: Allow header missing GET")


def check_replica(api_url, management_url, instance, fixture_bytes, jar_path):
    with ZipFile(jar_path) as jar:
        if jar.read(JAR_FIXTURE) != fixture_bytes:
            raise ValueError(f"{instance}: packaged fixture differs from source bytes")
    fixture = json.loads(fixture_bytes)
    check_ready(management_url)
    listing, _ = check_response(api_url, PRODUCTS_PATH, instance)
    if listing != fixture:
        raise ValueError(f"{instance}: list differs from fixture")
    products = listing["products"]
    for product in products:
        path = f"{PRODUCTS_PATH}/{product['id']}"
        detail, _ = check_response(api_url, path, instance)
        if detail != product or type(product["price"]) is not int or type(detail["price"]) is not int:
            raise ValueError(f"{instance} {path}: detail or integer price differs from fixture")
    check_errors(api_url, instance)
    digest = sha256(fixture_bytes).hexdigest()
    print(f"{instance}: readiness UP, list, {len(products)} details, six error cases, fixture SHA-256 {digest}")


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def local_url(container, port):
    return "http://" + docker("port", container, f"{port}/tcp")


def run(image):
    fixture_bytes = FIXTURE.read_bytes()
    # Resolve once so all containers use the same image even if a tag changes.
    image_id = docker("image", "inspect", "--format", "{{.Id}}", image)
    with ExitStack() as cleanup, TemporaryDirectory() as temp:
        replicas = {}
        for instance in ("C1", "C2", "C3"):
            container = docker(
                "run", "--detach", "--rm",
                "--env", f"INSTANCE_ID={instance}",
                "--publish", "127.0.0.1::8080",
                "--publish", "127.0.0.1::8082",
                image_id,
            )
            cleanup.callback(docker, "stop", "--time", "5", container)
            replicas[instance] = container
        for instance, container in replicas.items():
            jar_path = Path(temp) / f"{instance}.jar"
            docker("cp", f"{container}:/app/catalog.jar", str(jar_path))
            check_replica(
                local_url(container, 8080), local_url(container, 8082),
                instance, fixture_bytes, jar_path,
            )
    print(f"Verified Catalog image {image_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="Catalog image tag or ID")
    run(parser.parse_args().image)
