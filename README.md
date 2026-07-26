# Orbit demo environment

A zero-package demo for [Orbit](https://github.com/iml885203/orbit). It runs
Python's standard-library HTTP server on the host and Redis in a container,
showing the mixed local/container workflow without adding application
dependencies.

## Requirements

- Orbit
- Docker
- Python 3

While this repository is private, Git must also be authenticated for GitHub.
An authenticated GitHub CLI user can configure that once with
`gh auth setup-git`.

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

Open <http://localhost:28080>. The dashboard and `orbit status --json` show the
host-side Python service and Redis container in the same dependency graph.

Useful follow-up commands:

```bash
orbit logs demo-api
orbit inspect --json
orbit down
```

## What the repository contains

- `envs/quickstart.yaml`: the complete environment graph.

The service uses `python3 -m http.server`, so the synced YAML remains
self-contained and needs no separate source checkout or package installation.

## License

[MIT](LICENSE)
