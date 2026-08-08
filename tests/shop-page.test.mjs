import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import test from "node:test";
import vm from "node:vm";

class Element {
  className = "";
  disabled = false;
  innerHTML = "";
  textContent = "";
  style = {};

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

test("every beginner surface links to the adoption guide", () => {
  const english = readFileSync("README.md", "utf8");
  const traditionalChinese = readFileSync("README.zh-TW.md", "utf8");
  const page = readFileSync("apps/index.html", "utf8");

  assert.match(english, /orbit\/blob\/main\/docs\/local-first\.md/);
  assert.match(traditionalChinese, /orbit\/blob\/main\/docs\/local-first\.zh-TW\.md/);
  assert.match(page, /orbit\/blob\/main\/docs\/local-first\.md/);
});

test("the shop page buys, sells out, fails honestly, and recovers", async () => {
  const html = readFileSync("apps/index.html", "utf8");
  const source = html.match(/<script>([\s\S]*?)<\/script>/)[1]
    .replaceAll("{{CATALOG_URL}}", "http://catalog")
    .replaceAll("{{INVENTORY_URL}}", "http://inventory")
    .replaceAll("{{ORDER_URL}}", "http://order");
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]);
  const elements = new Map(ids.map((id) => [id, new Element()]));
  const state = {orderApiUp: true, stock: 2, orders: []};

  async function fetch(url, options = {}) {
    if (!state.orderApiUp && url.startsWith("http://order")) {
      throw new TypeError("fetch failed");
    }
    if (url === "http://catalog/products") {
      return response({
        products: [{id: 1, name: "Orbit Mug", description: "A mug.", price: 18}]
      });
    }
    if (url === "http://inventory/stock") {
      return response({stock: [{product_id: 1, available: state.stock}]});
    }
    if (url === "http://order/orders") {
      return response({orders: state.orders});
    }
    if (url === "http://inventory/restock" && options.method === "POST") {
      state.stock = 2;
      return response({stock: [{product_id: 1, available: state.stock}]});
    }
    if (url === "http://order/checkout" && options.method === "POST") {
      if (state.stock < 1) return response({error: "insufficient stock"}, false);
      state.stock -= 1;
      const id = state.orders.length + 1;
      state.orders.push({id, product_id: 1, product_name: "Orbit Mug", quantity: 1, total: 18});
      return response({
        id,
        product: {id: 1, name: "Orbit Mug", price: 18},
        quantity: 1,
        total: 18,
        remaining: state.stock
      });
    }
    throw new Error(`unexpected request: ${options.method || "GET"} ${url}`);
  }

  const context = {
    console,
    document: {
      getElementById(id) {
        return elements.get(id);
      }
    },
    fetch,
    setInterval() {},
    setTimeout,
    structuredClone
  };
  vm.runInNewContext(source, context);
  await eventually(() => elements.get("status-text").textContent === "All 5 resources ready");
  assert.match(elements.get("products").innerHTML, /2 in stock/);
  assert.match(elements.get("orders-empty").style.display, /block/);

  await context.buy(1);
  assert.match(elements.get("message").innerHTML, /Order #1 confirmed/);
  assert.match(elements.get("orders-list").innerHTML, /Order #1/);
  assert.equal(elements.get("orders-empty").style.display, "none");

  await context.buy(1);
  assert.match(elements.get("message").innerHTML, /Order #2 confirmed/);
  assert.match(elements.get("products").innerHTML, /Sold out/);

  await context.buy(1);
  assert.match(elements.get("message").innerHTML, /Checkout rejected/);
  assert.match(elements.get("message").innerHTML, /insufficient stock/);
  assert.match(elements.get("orders-list").innerHTML, /Order #2/);

  state.orderApiUp = false;
  await context.buy(1);
  assert.match(elements.get("message").innerHTML, /orbit status/);
  assert.equal(
    elements.get("status-text").textContent,
    "A service is down — run orbit status"
  );

  state.orderApiUp = true;
  await context.restock();
  assert.match(elements.get("message").innerHTML, /Restocked/);
  await context.buy(1);
  assert.match(elements.get("message").innerHTML, /Order #3 confirmed/);
  assert.equal(elements.get("status-text").textContent, "All 5 resources ready");
});
