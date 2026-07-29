# Orbit mini-shop environment

The default public environment for [Orbit](https://github.com/iml885203/orbit).
One checkout crosses a browser app, three host-side Python APIs, three SQLite
databases, and a Redis container. It is large enough to make orchestration
useful while remaining a zero-package first run.

## Requirements

- Orbit v0.0.23 or newer
- Docker
- Python 3

Python is intentionally not installed by `orbit init`. Orbit coordinates the
tools a project already uses; it does not manage language runtimes or project
packages.

## Run

```bash
orbit init --yes
orbit up
orbit open demo-shop
```

Choose **Run checkout**. The page shows the product loaded from catalog, the
stock reservation created by inventory, and the order linked to that
reservation. **Try 99 items** measures stock and record counts before and after
the rejected attempt: stock stays unchanged, new reservations and orders both
remain `+0`, and the earlier successful order remains visible.

Orbit starts the APIs in dependency order, injects their actual runtime URLs,
and keeps the whole graph working if preferred ports are occupied. The
application code never duplicates those selected ports.

Useful follow-up commands:

```bash
orbit logs shop-order-api
orbit open demo-shop
orbit inspect --json
orbit down
```

## What the repository contains

- `envs/quickstart.yaml`: the complete environment graph.
- `envs/seeds/mini-shop/`: the synced frontend, APIs, and repeatable smoke
  journey, implemented with Python's standard library.

There is no `pip install`. Orbit syncs the demo source with the environment so
the quickstart works from an empty directory; real projects point `path` at
their own checkouts.

The topology is:

```text
demo-shop
  ├─ shop-catalog-api ─ SQLite
  ├─ shop-inventory-api ─ SQLite + Redis
  └─ shop-order-api
       ├─ shop-catalog-api
       └─ shop-inventory-api
```

With the environment running, contributors can verify the complete business
path:

```bash
python3 ~/.orbit/envs/seeds/mini-shop/smoke.py
```

## License

[MIT](LICENSE)
