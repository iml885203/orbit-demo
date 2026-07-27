# Orbit demo environment

A zero-package demo for [Orbit](https://github.com/iml885203/orbit). A local
Python service stores its visit counter in a Redis container, demonstrating
Orbit's mixed host/container workflow and dependency injection without adding
application packages.

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
orbit init --yes
orbit up
```

Open <http://localhost:28080> and refresh it. The counter is stored in Redis,
proving that the host-side Python process can use the container dependency
Orbit started and configured for it.

Useful follow-up commands:

```bash
orbit logs demo-api
orbit inspect --json
orbit down
```

## What the repository contains

- `envs/quickstart.yaml`: the complete environment graph.
- `envs/seeds/demo/app.py`: the synced local service, implemented with
  Python's standard library.

There is no `pip install`: the service uses only Python's standard library.
Orbit syncs this tiny source file with the environment so the quickstart also
works from an empty directory; real projects point `path` at their own checkout.

## License

[MIT](LICENSE)
