import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import test from "node:test";
import vm from "node:vm";

class Element {
  className = "";
  disabled = false;
  innerHTML = "";
  textContent = "";

  addEventListener() {}
}

function response(payload, ok = true) {
  return {
    ok,
    async json() {
      return structuredClone(payload);
    }
  };
}

async function eventually(predicate) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  assert.fail("page did not reach the expected state");
}

test("beginner surfaces share one versioned adoption handoff", () => {
  const english = readFileSync("README.md", "utf8");
  const traditionalChinese = readFileSync("README.zh-TW.md", "utf8");
  const page = readFileSync("envs/seeds/mini-shop/index.html", "utf8");
  const handoffs = [
    english.match(/orbit\/blob\/(v[^/]+)\/docs\/local-first\.md/),
    traditionalChinese.match(/orbit\/blob\/(v[^/]+)\/docs\/local-first\.zh-TW\.md/),
    page.match(/orbit\/blob\/(v[^/]+)\/docs\/local-first\.md/)
  ];

  assert.ok(handoffs.every(Boolean), "every beginner surface must link to the adoption guide");
  assert.deepEqual(
    new Set(handoffs.map((match) => match[1])),
    new Set(["v0.0.44"]),
    "all adoption links must match the demo's Orbit release"
  );
  assert.doesNotMatch(english, /orbit inspect --json/);
  assert.doesNotMatch(traditionalChinese, /orbit inspect --json/);
});

test("a failed checkout replaces stale success while preserving durable state", async () => {
  const html = readFileSync("envs/seeds/mini-shop/index.html", "utf8");
  const source = html.match(/<script>([\s\S]*?)<\/script>/)[1]
    .replaceAll("{{CATALOG_URL}}", "http://catalog")
    .replaceAll("{{INVENTORY_URL}}", "http://inventory")
    .replaceAll("{{ORDER_URL}}", "http://order");
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]);
  const elements = new Map(ids.map((id) => [id, new Element()]));
  const state = {
    dependencyUp: true,
    inventory: {
      stock: [{product_id: 1, available: 8}],
      reservations: []
    },
    orders: {orders: []}
  };

  async function fetch(url, options = {}) {
    if (!state.dependencyUp && url.startsWith("http://inventory")) {
      throw new TypeError("fetch failed");
    }
    if (url.endsWith("/health")) return response({ok: true});
    if (url === "http://catalog/products") {
      return response({products: [{id: 1, name: "Orbit Mug", price: 18}]});
    }
    if (url === "http://inventory/state") return response(state.inventory);
    if (url === "http://order/state") return response(state.orders);
    if (url === "http://order/checkout" && options.method === "POST") {
      const id = state.orders.orders.length + 1;
      state.inventory.stock[0].available -= 1;
      state.inventory.reservations.push({id, product_id: 1, quantity: 1});
      state.orders.orders.push({id, reservation_id: id});
      return response({
        id,
        quantity: 1,
        total: 18,
        product: {name: "Orbit Mug"}
      });
    }
    throw new Error(`unexpected request: ${options.method || "GET"} ${url}`);
  }

  const context = {
    console,
    Date,
    document: {
      getElementById(id) {
        return elements.get(id);
      }
    },
    fetch,
    setTimeout,
    structuredClone
  };
  vm.runInNewContext(source, context);
  await eventually(() => elements.get("status-text").textContent === "5 resources ready");

  await context.checkout(1);
  assert.equal(elements.get("attempt-title").textContent, "1 item checkout committed");
  assert.equal(elements.get("order").textContent, "Order #1");

  state.dependencyUp = false;
  await context.checkout(1);

  assert.equal(elements.get("attempt-title").textContent, "Checkout unavailable");
  assert.match(elements.get("result-detail").innerHTML, /orbit status/);
  assert.doesNotMatch(elements.get("result-detail").innerHTML, /shop-order-api/);
  assert.match(elements.get("attempt-detail").textContent, /1 item requested at/);
  assert.match(elements.get("attempt-detail").textContent, /no deltas are claimed/);
  assert.equal(elements.get("stock-change").textContent, "Unknown");
  assert.equal(elements.get("reservation-change").textContent, "Unknown");
  assert.equal(elements.get("order-change").textContent, "Unknown");
  assert.equal(elements.get("order").textContent, "Order #1");
  assert.equal(elements.get("status-text").textContent, "A dependency needs attention");

  state.dependencyUp = true;
  await context.checkout(1);

  assert.equal(elements.get("attempt-title").textContent, "1 item checkout committed");
  assert.equal(elements.get("order").textContent, "Order #2");
  assert.equal(elements.get("status-text").textContent, "5 resources ready");
});
