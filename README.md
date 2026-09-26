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

周长层高+花匹配 → 干算卷数 + 一次性回执 → 确认回执才落库 → 历史新增一行 → 展开示意

- `POST /api/estimate`：干算，返回卷数与回执令牌（绑定墙/卷材编号与签发时快照，历史不增行）
- `POST /api/estimate/confirm`：携带未使用回执才写入一条 run；回执缺失/已核销/墙或卷材已变更均失败且不增行
- 回执签发、核销、写 run 分别在 `modules/receipt_issue`、`modules/receipt_redeem`、`modules/run_writer`

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。
