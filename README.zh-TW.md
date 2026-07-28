# Orbit demo 環境

這是 [Orbit](https://github.com/iml885203/orbit) 的零套件 demo。本機
Python service 會把瀏覽次數存進 Redis container，用來展示 Orbit 如何協調
本機 runtime、container dependency 與連線資訊注入。

## 需求

- Orbit
- Docker
- Python 3

`orbit init` 不會替使用者安裝 Python。Orbit 負責協調專案原本使用的工具，
不負責管理語言 runtime 或專案套件。

## 執行

```bash
orbit init --yes
orbit up
```

開啟 <http://localhost:28080> 並重新整理。計數器會保存在 Redis，證明
Orbit 啟動並設定的 container dependency，確實能被本機 Python process 使用。

其他常用指令：

```bash
orbit logs demo-api
orbit inspect --json
orbit down
```

## Repo 內容

- `envs/quickstart.yaml`：完整的環境拓樸。
- `envs/seeds/demo/app.py`：隨環境同步、只使用 Python 標準函式庫的本機
  service。

不需要執行 `pip install`；service 只使用 Python 標準函式庫。
Orbit 會隨環境同步這個小型 source，因此 quickstart 從空目錄也能執行；
真實專案則會把 `path` 指向自己的 checkout。

## License

[MIT](LICENSE)
