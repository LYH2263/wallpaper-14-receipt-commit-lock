# 18-wallpaper（墙纸卷数）

Wallpaper — 幅宽分幅 + 花高匹配损耗后的卷数向上取整

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4700 |
| API | http://localhost:9700 |

## 主链

周长层高+花匹配 → 干算卷数 → 签发一次性回执 → 凭回执确认入账 → 历史新行

- `POST /api/estimate/dry-run`：只算卷数并签发一次性回执（绑定墙面/卷材编号与卷数，服务端登记），历史表不增行
- `POST /api/estimate/confirm`：凭未使用且签发后墙周长/卷材未变的回执，核销并写入一条 run；回执缺失/已使用/输入已变均失败且不落库
- 回执签发（`receipt_issue`）、核销（`receipt_redeem`）与写 run（`run_writer`）分模块，一次性由服务端核销保证

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
