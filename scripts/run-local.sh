#!/usr/bin/env bash
# Start the whole mini-shop without Orbit: one Redis container plus the four
# Python services on their default ports. Ctrl-C stops everything.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
redis_container="mini-shop-redis"

docker rm -f "$redis_container" >/dev/null 2>&1 || true
docker run -d --name "$redis_container" -p 26379:6379 redis:7.4-alpine >/dev/null
echo "redis ready on 127.0.0.1:26379"

pids=()
cleanup() {
  kill "${pids[@]}" >/dev/null 2>&1 || true
  docker rm -f "$redis_container" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for app in catalog inventory orders web; do
  python3 "$root/apps/$app.py" &
  pids+=($!)
done

echo "demo-shop ready on http://127.0.0.1:28080 (Ctrl-C to stop)"
wait
