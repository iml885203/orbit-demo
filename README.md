# Orbit mini-shop demo

A deliberately tiny shop: two products, a **Buy** button, a stock count, and an
order list. Products live in code, live stock lives in a Redis container, and
orders persist in SQLite on your host. It is the public demo for
[Orbit](https://github.com/iml885203/orbit), yet the application has no
dependency on Orbit — every service is plain Python standard library,
configured through ordinary environment variables with localhost defaults.

```text
demo-shop (browser app)
  └─ shop-order-api ── SQLite (orders persist)
       ├─ shop-catalog-api      (products, in code)
       └─ shop-inventory-api ── redis container (live stock)
```

## Requirements

- Python 3
- Docker
- [Orbit](https://github.com/iml885203/orbit) (only for the Orbit-managed path)

There is no `pip install`; the demo uses Python's standard library only.

## Run with Orbit

```bash
git clone https://github.com/iml885203/orbit-demo.git
cd orbit-demo
orbit up
orbit open demo-shop
```

Orbit reads the project-root `orbit.yaml`, starts the container and the four
host services in dependency order, waits for real readiness, and injects every
service URL.

## The two-minute journey

1. **Buy a mug.** The order crosses the whole graph — catalog for the product,
   inventory for stock, SQLite for the order — and shows up in the order list.
2. **Buy until it sells out.** The rejected checkout changes nothing; hit
   **Restock** to refill.
3. **Break something.** Run `orbit down shop-inventory-api`, buy again, and the
   page tells you a service is down. `orbit status` names it; watch a request
   fail with `orbit logs shop-order-api`.
4. **Recover.** Run `orbit up shop-inventory-api` and buy again. Orders made
   earlier are still there — SQLite lives on your host, so they even survive a
   full `orbit down` / `orbit up`.

With the stack running, the same journey is scripted:

```bash
python3 scripts/smoke.py
```

## Run without Orbit

```bash
./scripts/run-local.sh
```

The script starts Redis in Docker and the four services on their default
ports, then serves the shop at <http://127.0.0.1:28080>. Ctrl-C stops
everything.

## What the repository contains

- `orbit.yaml`: the environment graph for the Orbit-managed path.
- `apps/`: the frontend and the three APIs, standard library only.
- `scripts/run-local.sh`: start everything without Orbit.
- `scripts/smoke.py`: the repeatable smoke journey.

To move from the demo to your own project, follow
[Use Orbit with your project](https://github.com/iml885203/orbit/blob/main/docs/local-first.md).
The local trial starts with one project-root `orbit.yaml`, exactly like this
repository.

## License

[MIT](LICENSE)
