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

# Restock first so the journey is repeatable no matter what ran before.
restock_status, full = post(urls["shop-inventory-api"] + "/restock", {})
assert restock_status == 200, (restock_status, full)
available = {item["product_id"]: item["available"] for item in full["stock"]}
assert all(count > 0 for count in available.values()), available

orders_before = load_json(urls["shop-order-api"] + "/orders")["orders"]

success_status, order = post(
    urls["shop-order-api"] + "/checkout",
    {"product_id": 1, "quantity": 1},
)
assert success_status == 201, (success_status, order)
assert order["product"]["id"] == 1, order
assert order["quantity"] == 1, order
assert order["total"] == order["product"]["price"], order
assert order["remaining"] == available[1] - 1, (order, available)

stock_after = load_json(urls["shop-inventory-api"] + "/stock")["stock"]
assert {item["product_id"]: item["available"] for item in stock_after}[1] == available[1] - 1
orders_after = load_json(urls["shop-order-api"] + "/orders")["orders"]
assert len(orders_after) == len(orders_before) + 1
assert orders_after[-1]["id"] == order["id"]

failed_status, failure = post(
    urls["shop-order-api"] + "/checkout",
    {"product_id": 1, "quantity": 9999},
)
assert failed_status == 409, (failed_status, failure)
assert failure["error"] == "insufficient stock", failure
assert load_json(urls["shop-inventory-api"] + "/stock")["stock"] == stock_after
assert load_json(urls["shop-order-api"] + "/orders")["orders"] == orders_after

restock_status, restored = post(urls["shop-inventory-api"] + "/restock", {})
assert restock_status == 200, (restock_status, restored)
assert {item["product_id"]: item["available"] for item in restored["stock"]} == available

print(
    "mini-shop smoke passed: "
    f"order #{order['id']} committed and persisted; "
    "oversell was rejected with stock and orders unchanged; "
    "restock restored full stock"
)
