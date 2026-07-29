import json
import os
import subprocess
from urllib import error, request


def load(url):
    with request.urlopen(url, timeout=5) as response:
        return response.read(), response.headers.get_content_type()


def load_json(url):
    body, _ = load(url)
    return json.loads(body)


def post(url, payload):
    req = request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as response:
            return response.status, json.load(response)
    except error.HTTPError as response:
        return response.code, json.load(response)


orbit_command = ["orbit"]
if os.environ.get("ORBIT_CONFIG"):
    orbit_command.extend(["-c", os.environ["ORBIT_CONFIG"]])
status = json.loads(
    subprocess.check_output(orbit_command + ["status", "--json"], text=True)
)
assert status["ok"] is True, status
resources = {
    resource["name"]: resource
    for resource in status["data"]["resources"]
}
expected = {
    "demo-shop",
    "shop-catalog-api",
    "shop-inventory-api",
    "shop-order-api",
    "redis",
}
assert expected == resources.keys(), resources.keys()
assert all(resource["state"] == "healthy" for resource in resources.values()), resources

urls = {
    name: resources[name]["url"]
    for name in expected - {"redis"}
}
page, content_type = load(urls["demo-shop"])
assert content_type == "text/html", content_type
page = page.decode()
for name in ("shop-catalog-api", "shop-inventory-api", "shop-order-api"):
    assert urls[name] in page, (name, urls[name])

for name in ("shop-catalog-api", "shop-inventory-api", "shop-order-api", "demo-shop"):
    health = load_json(urls[name] + "/health")
    assert health["ok"] is True, (name, health)

before = load_json(urls["shop-inventory-api"] + "/stock")
success_status, order = post(
    urls["shop-order-api"] + "/checkout",
    {"product_id": 1, "quantity": 1},
)
assert success_status == 201, (success_status, order)
assert order["status"] == "confirmed", order
assert order["product"]["id"] == order["reservation"]["product_id"] == 1, order
assert order["reservation"]["quantity"] == order["quantity"] == 1, order

stock_after_success = load_json(urls["shop-inventory-api"] + "/stock")
failed_status, failure = post(
    urls["shop-order-api"] + "/checkout",
    {"product_id": 1, "quantity": 9999},
)
assert failed_status == 409, (failed_status, failure)
assert failure["error"] == "insufficient stock", failure
stock_after_failure = load_json(urls["shop-inventory-api"] + "/stock")
assert stock_after_failure == stock_after_success, (
    before,
    stock_after_success,
    stock_after_failure,
)

reservation_status, reservation = post(
    urls["shop-inventory-api"] + "/reservations",
    {"product_id": 1, "quantity": 1},
)
assert reservation_status == 201, (reservation_status, reservation)
release_status, release = post(
    "%s/reservations/%d/release"
    % (urls["shop-inventory-api"], reservation["id"]),
    {},
)
assert release_status == 200 and release["released"] is True, (release_status, release)
assert load_json(urls["shop-inventory-api"] + "/stock") == stock_after_success

print(
    "mini-shop smoke passed: "
    f"order #{order['id']} → reservation #{order['reservation']['id']}; "
    "failure and compensation preserved stock"
)
