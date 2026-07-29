# Orbit mini-shop 環境

這是 [Orbit](https://github.com/iml885203/orbit) 預設的公開 environment。
一次 checkout 會經過瀏覽器 app、三個在 host 執行的 Python API、三個 SQLite
database，以及一個 Redis container。規模足以呈現 orchestration 的價值，
同時維持零套件的 first run。

## 需求

- Orbit v0.0.23 或更新版本
- Docker
- Python 3

`orbit init` 不會替使用者安裝 Python。Orbit 負責協調專案原本使用的工具，
不負責管理語言 runtime 或專案套件。

## 執行

```bash
orbit init --yes
orbit up
orbit open demo-shop
```

選擇 **Run checkout**。畫面會顯示從 catalog 讀取的商品、inventory 建立的
庫存 reservation，以及與 reservation 關聯的 order。**Try 99 items** 會重新
量測失敗前後的庫存與 records：庫存保持不變，新增 reservation 與 order 都是
`+0`，先前成功的 order 也會繼續顯示。

若 dependency 停止回應，下一次點擊會把上一筆成功證據替換成
**Checkout unavailable**，不會繼續誤稱舊結果是最新嘗試。頁面會把最後確認的
order 保留在 **Durable state**、標示環境需要處理，並在 dependency 恢復且下一次
checkout 成功後回到 ready。

Orbit 會依 dependency 順序啟動 API、注入實際 runtime URL；即使偏好 port
已被占用，整張 graph 仍能正常運作，application code 不需要重複維護那些 port。

其他常用指令：

```bash
orbit status
orbit logs shop-order-api
orbit open demo-shop
orbit inspect --json
orbit down
```

要從 demo 套用到真實 checkout，請接著閱讀
[在自己的專案使用 Orbit](https://github.com/iml885203/orbit/blob/v0.0.33/docs/local-first.zh-TW.md)。
本機試用只從 project-root `orbit.yaml` 開始，不需要 environment repository
或永久 Orbit settings。

## Repo 內容

- `envs/quickstart.yaml`：完整的環境拓樸。
- `envs/seeds/mini-shop/`：隨環境同步、只使用 Python 標準函式庫的 frontend、
  APIs 與可重複 smoke journey。

不需要執行 `pip install`。Orbit 會隨 environment 同步 demo source，
因此 quickstart 從空目錄也能執行；
真實專案則會把 `path` 指向自己的 checkout。

拓樸如下：

```text
demo-shop
  ├─ shop-catalog-api ─ SQLite
  ├─ shop-inventory-api ─ SQLite + Redis
  └─ shop-order-api
       ├─ shop-catalog-api
       └─ shop-inventory-api
```

Environment 執行中時，contributor 可以驗證完整 business path：

```bash
python3 ~/.orbit/envs/seeds/mini-shop/smoke.py
```

## License

[MIT](LICENSE)
