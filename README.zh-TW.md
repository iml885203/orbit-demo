# Orbit demo 環境

這是 [Orbit](https://github.com/iml885203/orbit) 的零套件 demo。Python
標準函式庫 HTTP server 在本機執行，Redis 則在 container 內執行，用來展示
本機 runtime 與 container 的混合開發環境。

## 需求

- Orbit
- Docker
- Python 3

`orbit init` 不會替使用者安裝 Python。Orbit 負責協調專案原本使用的工具，
不負責管理語言 runtime 或專案套件。

## 執行

```bash
orbit init --yes \
  --env-repo https://github.com/iml885203/orbit-demo.git \
  --env quickstart
orbit up
orbit status --json
```

開啟 <http://localhost:28080>。Dashboard 與 `orbit status --json` 會在同一份
dependency graph 顯示本機 Python service 與 Redis container。

其他常用指令：

```bash
orbit logs demo-api
orbit inspect --json
orbit down
```

## Repo 內容

- `envs/quickstart.yaml`：完整的環境拓樸。

Service 使用 `python3 -m http.server`，因此同步後的 YAML 本身就是完整環境，
不需要另外 checkout source 或安裝 package。

## License

[MIT](LICENSE)
