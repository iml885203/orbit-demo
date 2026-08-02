# Orbit mini-shop demo

一個小而完整的商店應用程式：一個瀏覽器 app、三個 Python API、三個 SQLite
database，以及一個 Redis container。它是
[Orbit](https://github.com/iml885203/orbit) 的公開 demo，但應用程式本身
不依賴 Orbit——每個 service 都只用 Python 標準函式庫，設定全部走一般的
環境變數並有 localhost 預設值。你可以手動啟動 runtime，也可以交給 Orbit
協調。

## 需求

- Python 3
- Docker
- [Orbit](https://github.com/iml885203/orbit) v0.5.0 或更新版本（只有
  Orbit 管理的路徑需要）

不需要 `pip install`；demo 只使用 Python 標準函式庫。

## 用 Orbit 執行

```bash
git clone https://github.com/iml885203/orbit-demo.git
cd orbit-demo
orbit up
orbit open demo-shop
```

Orbit 會讀取 project-root 的 `orbit.yaml`、依 dependency 順序啟動 API、
注入實際 runtime URL；即使偏好 port 已被占用，整張 graph 仍能正常運作，
application code 不需要重複維護那些 port。

其他常用指令：

```bash
orbit status
orbit doctor
orbit logs shop-order-api
orbit down
```

## 不用 Orbit 執行

```bash
./scripts/run-local.sh
```

這個 script 會在 Docker 裡啟動 Redis，並用預設 port 啟動四個 service，
商店會在 <http://127.0.0.1:28080>。Ctrl-C 會停止全部。也可以自己逐個啟動：

```bash
docker run -d --name mini-shop-redis -p 26379:6379 redis:7.4-alpine
python3 apps/catalog.py &
python3 apps/inventory.py &
python3 apps/orders.py &
python3 apps/web.py &
```

## Demo journey

選擇 **Run checkout**。畫面會顯示從 catalog 讀取的商品、inventory 建立的
庫存 reservation，以及與 reservation 關聯的 order。**Try 99 items** 會重新
量測失敗前後的庫存與 records：庫存保持不變，新增 reservation 與 order 都是
`+0`，先前成功的 order 也會繼續顯示。

若 dependency 停止回應，下一次點擊會把上一筆成功證據替換成
**Checkout unavailable**，不會繼續誤稱舊結果是最新嘗試。頁面會把最後確認的
order 保留在 **Durable state**、標示環境需要處理，並在 dependency 恢復且下一次
checkout 成功後回到 ready。

不論用哪種方式啟動，都可以驗證完整 business path：

```bash
python3 scripts/smoke.py
```

smoke script 會從 `DEMO_SHOP_URL`、`SHOP_CATALOG_API_URL`、
`SHOP_INVENTORY_API_URL`、`SHOP_ORDER_API_URL` 讀取 service URL，
沒有設定時使用預設的本機 port。

## Repo 內容

- `orbit.yaml`：Orbit 管理路徑使用的環境拓樸。
- `apps/`：只使用 Python 標準函式庫的 frontend 與 APIs。
- `scripts/run-local.sh`：不透過 Orbit 啟動全部服務。
- `scripts/smoke.py`：可重複執行的 smoke journey。

拓樸如下：

```text
demo-shop
  ├─ shop-catalog-api ─ SQLite
  ├─ shop-inventory-api ─ SQLite + Redis
  └─ shop-order-api
       ├─ shop-catalog-api
       └─ shop-inventory-api
```

要從 demo 套用到自己的專案，請接著閱讀
[在自己的專案使用 Orbit](https://github.com/iml885203/orbit/blob/v0.5.0/docs/local-first.zh-TW.md)。
本機試用和這個 repo 一樣，只從 project-root `orbit.yaml` 開始，不需要
environment repository 或永久 Orbit settings。

## License

[MIT](LICENSE)
