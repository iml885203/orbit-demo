# Orbit mini-shop demo

一個刻意做得很小的商店：兩個商品、一顆 **Buy** 按鈕、庫存數字和一份訂單
清單。商品寫在程式碼裡、即時庫存放在 Redis container、訂單存進本機的
SQLite。它是 [Orbit](https://github.com/iml885203/orbit) 的公開 demo，但
應用程式本身不依賴 Orbit——每個 service 都只用 Python 標準函式庫，設定
全部走一般的環境變數並有 localhost 預設值。

```text
demo-shop (瀏覽器 app)
  └─ shop-order-api ── SQLite（訂單持久保存）
       ├─ shop-catalog-api      （商品，寫在程式碼裡）
       └─ shop-inventory-api ── redis container（即時庫存）
```

## 需求

- Python 3
- Docker
- [Orbit](https://github.com/iml885203/orbit)（只有 Orbit 管理的路徑需要）

不需要 `pip install`；demo 只使用 Python 標準函式庫。

## 用 Orbit 執行

```bash
git clone https://github.com/iml885203/orbit-demo.git
cd orbit-demo
orbit up
orbit open demo-shop
```

Orbit 會讀取 project-root 的 `orbit.yaml`、依 dependency 順序啟動
container 與四個 host service、等待真正 ready，並注入每個 service 的 URL。

## 兩分鐘旅程

1. **買一個馬克杯。** 這筆訂單會穿過整張 graph——catalog 提供商品、
   inventory 扣庫存、SQLite 寫入訂單——然後出現在訂單清單裡。
2. **一直買到賣完。** 被拒絕的 checkout 不會改變任何狀態；按 **Restock**
   補貨。
3. **弄壞一個服務。** 執行 `orbit down shop-inventory-api` 再買一次，頁面
   會告訴你有服務掛了。`orbit status` 會指出是哪一個；用
   `orbit logs shop-order-api` 看請求失敗的樣子。
4. **復原。** 執行 `orbit up shop-inventory-api` 再買一次。先前的訂單都還
   在——SQLite 在你的本機上，連整套 `orbit down` / `orbit up` 都不會弄丟
   它們。

環境跑起來後，同一段旅程也有 script 版本：

```bash
python3 scripts/smoke.py
```

## 不用 Orbit 執行

```bash
./scripts/run-local.sh
```

這個 script 會在 Docker 裡啟動 Redis，並用預設 port 啟動四個 service，
商店會在 <http://127.0.0.1:28080>。Ctrl-C 會停止全部。

## Repo 內容

- `orbit.yaml`：Orbit 管理路徑使用的環境拓樸。
- `apps/`：frontend 與三個 API，只用標準函式庫。
- `envs/`：同一個環境的 `orbit init` quickstart 打包——由
  `scripts/sync-quickstart.sh` 產生，不手動編輯。
- `scripts/run-local.sh`：不透過 Orbit 啟動全部服務。
- `scripts/smoke.py`：可重複執行的 smoke journey。

要從 demo 套用到自己的專案，請接著閱讀
[在自己的專案使用 Orbit](https://github.com/iml885203/orbit/blob/main/docs/local-first.zh-TW.md)。
本機試用和這個 repo 一樣，只從 project-root `orbit.yaml` 開始。

## License

[MIT](LICENSE)
