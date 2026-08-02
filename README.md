# Orbit mini-shop demo

A small, self-contained shop application: one browser app, three Python APIs,
three SQLite databases, and a Redis container. It is the public demo for
[Orbit](https://github.com/iml885203/orbit), yet the application itself has no
dependency on Orbit — every service is plain Python standard library,
configured through ordinary environment variables with localhost defaults.
You can start the runtimes by hand, or let Orbit orchestrate them.

## Requirements

- Python 3
- Docker
- [Orbit](https://github.com/iml885203/orbit) v0.6.0 or newer (only for the
  Orbit-managed path)

There is no `pip install`; the demo uses Python's standard library only.

## Run with Orbit

```bash
git clone https://github.com/iml885203/orbit-demo.git
cd orbit-demo
orbit up
orbit open demo-shop
```

Orbit reads the project-root `orbit.yaml`, starts the APIs in dependency
order, injects their actual runtime URLs, and keeps the whole graph working
if preferred ports are occupied. The application code never duplicates those
selected ports.

Useful follow-up commands:

```bash
orbit status
orbit doctor
orbit logs shop-order-api
orbit down
```

## Run without Orbit

```bash
./scripts/run-local.sh
```

The script starts Redis in Docker and the four services on their default
ports, then serves the shop at <http://127.0.0.1:28080>. Ctrl-C stops
everything. Equivalently, run each piece yourself:

```bash
docker run -d --name mini-shop-redis -p 26379:6379 redis:7.4-alpine
python3 apps/catalog.py &
python3 apps/inventory.py &
python3 apps/orders.py &
python3 apps/web.py &
```

## The demo journey

Choose **Run checkout**. The page shows the product loaded from catalog, the
stock reservation created by inventory, and the order linked to that
reservation. **Try 99 items** measures stock and record counts before and
after the rejected attempt: stock stays unchanged, new reservations and orders
both remain `+0`, and the earlier successful order remains visible.

If a dependency stops responding, a new click replaces the previous attempt
with **Checkout unavailable** instead of reusing stale success evidence. The
page keeps the last confirmed order under **Durable state**, marks the stack as
needing attention, and returns to ready after the dependency recovers and the
next checkout succeeds.

With the stack running (either way), verify the complete business path:

```bash
python3 scripts/smoke.py
```

The smoke script reads the service URLs from `DEMO_SHOP_URL`,
`SHOP_CATALOG_API_URL`, `SHOP_INVENTORY_API_URL`, and `SHOP_ORDER_API_URL`,
falling back to the default local ports.

## What the repository contains

- `orbit.yaml`: the environment graph for the Orbit-managed path.
- `apps/`: the frontend and APIs, implemented with Python's standard library.
- `scripts/run-local.sh`: start everything without Orbit.
- `scripts/smoke.py`: the repeatable smoke journey.

The topology is:

```text
demo-shop
  ├─ shop-catalog-api ─ SQLite
  ├─ shop-inventory-api ─ SQLite + Redis
  └─ shop-order-api
       ├─ shop-catalog-api
       └─ shop-inventory-api
```

To move from the demo to your own project, follow
[Use Orbit with your project](https://github.com/iml885203/orbit/blob/v0.6.0/docs/local-first.md).
The local trial starts with one project-root `orbit.yaml`, exactly like this
repository; it does not require an environment repository or persistent Orbit
settings.

## License

[MIT](LICENSE)
