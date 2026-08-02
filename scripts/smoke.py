import json
import os
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


urls = {
    "demo-shop": os.environ.get("DEMO_SHOP_URL", "http://127.0.0.1:28080"),
    "shop-catalog-api": os.environ.get(
        "SHOP_CATALOG_API_URL", "http://127.0.0.1:28101"
    ),
    "shop-inventory-api": os.environ.get(
        "SHOP_INVENTORY_API_URL", "http://127.0.0.1:28102"
    ),
    "shop-order-api": os.environ.get(
        "SHOP_ORDER_API_URL", "http://127.0.0.1:28103"
    ),
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
inventory_before = load_json(urls["shop-inventory-api"] + "/state")
orders_before = load_json(urls["shop-order-api"] + "/state")
success_status, order = post(
    urls["shop-order-api"] + "/checkout",
    {"product_id": 1, "quantity": 1},
)
assert success_status == 201, (success_status, order)
assert order["status"] == "confirmed", order
assert order["product"]["id"] == order["reservation"]["product_id"] == 1, order
assert order["reservation"]["quantity"] == order["quantity"] == 1, order

stock_after_success = load_json(urls["shop-inventory-api"] + "/stock")
inventory_after_success = load_json(urls["shop-inventory-api"] + "/state")
orders_after_success = load_json(urls["shop-order-api"] + "/state")
assert len(inventory_after_success["reservations"]) == len(
    inventory_before["reservations"]
) + 1
assert len(orders_after_success["orders"]) == len(orders_before["orders"]) + 1
assert orders_after_success["orders"][-1]["id"] == order["id"]
assert (
    orders_after_success["orders"][-1]["reservation_id"]
    == inventory_after_success["reservations"][-1]["id"]
    == order["reservation"]["id"]
)
failed_status, failure = post(
    urls["shop-order-api"] + "/checkout",
    {"product_id": 1, "quantity": 9999},
)
assert failed_status == 409, (failed_status, failure)
assert failure["error"] == "insufficient stock", failure
stock_after_failure = load_json(urls["shop-inventory-api"] + "/stock")
inventory_after_failure = load_json(urls["shop-inventory-api"] + "/state")
orders_after_failure = load_json(urls["shop-order-api"] + "/state")
assert stock_after_failure == stock_after_success, (
    before,
    stock_after_success,
    stock_after_failure,
)
assert inventory_after_failure == inventory_after_success
assert orders_after_failure == orders_after_success

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
    "failure added +0 reservations and +0 orders while preserving stock; "
    "compensation restored stock"
)
