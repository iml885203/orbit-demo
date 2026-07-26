# Orbit demo 環境

這是 [Orbit](https://github.com/iml885203/orbit) 的零套件 demo。Python HTTP
service 在本機執行，Redis 則在 container 內執行，用來展示本機 runtime 與
container 的混合開發環境。

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

開啟 <http://localhost:28080>。回應會顯示本機 Python service 是否能透過
Orbit 注入的連線設定連到 Redis container。

其他常用指令：

```bash
orbit logs demo-api
orbit inspect --json
orbit down
```

## Repo 內容

- `envs/quickstart.yaml`：環境拓樸。
- `envs/quickstart/server.py`：只使用 Python 標準函式庫的本機 service。

兩個檔案都放在 `envs/` 下，因為 `orbit env sync` 會把整棵目錄複製到
`~/.orbit/envs/`，並保留相對路徑。

## License

[MIT](LICENSE)
