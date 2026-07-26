# Orbit demo environment

A zero-package demo for [Orbit](https://github.com/iml885203/orbit). It runs a
Python HTTP service on the host and Redis in a container, showing the mixed
local/container workflow without adding application dependencies.

## Requirements

- Orbit
- Docker
- Python 3

Python is intentionally not installed by `orbit init`. Orbit coordinates the
tools a project already uses; it does not manage language runtimes or project
packages.

## Run

```bash
orbit init --yes \
  --env-repo https://github.com/iml885203/orbit-demo.git \
  --env quickstart
orbit up
orbit status --json
```

Open <http://localhost:28080>. The response reports whether the host-side
Python service can reach the Redis container through the connection settings
Orbit injects.

Useful follow-up commands:

```bash
orbit logs demo-api
orbit inspect --json
orbit down
```

## What the repository contains

- `envs/quickstart.yaml`: the environment graph.
- `envs/quickstart/server.py`: a standard-library-only host service.

Both live under `envs/` because `orbit env sync` copies that tree into
`~/.orbit/envs/`, preserving relative paths.

## License

[MIT](LICENSE)
