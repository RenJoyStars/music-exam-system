# 排行榜后端 · 部署说明

一个 FastAPI + SQLite 的小服务，只为排行榜存在。**不跑它，网站照样能用**（自动降级成本机榜）。

## 一、接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/exam-api/health` | 探活 |
| GET | `/exam-api/board` | 回最近 3000 条交卷记录 |
| POST | `/exam-api/score` | 收一条 `{n,pid,r,t,s,at}` |

排行榜的聚合排序（做题榜 / 正确率榜 / 最高分榜）全在前端 `exam.html` 的 `aggregate()` 里算，加新榜只改前端。

## 二、本机试跑

```bash
cd server
python3 -m venv .venv && . .venv/bin/activate
pip install fastapi uvicorn
uvicorn main:app --host 127.0.0.1 --port 8010
```

数据库默认落在 `server/exam.db`，可用环境变量 `EXAM_DB` 改路径。

## 三、服务器部署（43.139.116.30 · Debian 12）

```bash
# 1) 放代码
mkdir -p /srv/exam-api && cd /srv/exam-api     # 把 main.py 传上来
python3 -m venv .venv && . .venv/bin/activate
pip install fastapi uvicorn                    # 走国内源加 -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2) 常驻
cat > /etc/systemd/system/exam-api.service <<'EOF'
[Unit]
Description=Exam leaderboard API
After=network.target

[Service]
WorkingDirectory=/srv/exam-api
Environment=EXAM_DB=/srv/exam-api/exam.db
ExecStart=/srv/exam-api/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8010
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable --now exam-api
```

```nginx
# 3) nginx 片段（注意不要用 /api/，3000 端口的 ningserver 已占用）
location /exam-api/ {
    proxy_pass http://127.0.0.1:8010;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# 静态页面（exam.html / bank.js / media/）
location / {
    root /var/www/exam;
    index exam.html;
    try_files $uri $uri/ /exam.html;
}

# 4) 顺手限个频，防刷榜
limit_req_zone $binary_remote_addr zone=examapi:10m rate=30r/m;
# 在 location /exam-api/ 内加：limit_req zone=examapi burst=10 nodelay;
```

```bash
# 5) 证书
certbot --nginx -d exam.renqiaoyi.cn
```

DNS：DNSPod 加一条 A 记录 `exam` → `43.139.116.30`。

## 四、验证

```bash
curl https://exam.renqiaoyi.cn/exam-api/health          # {"ok":true}
curl 'https://exam.renqiaoyi.cn/exam-api/board'         # {"items":[],"live":true}
```

前端首页排行榜右上角标签从「本机」变成「联机」，就成了。

## 五、备份

```bash
cp /srv/exam-api/exam.db /root/backup/exam-$(date +%F).db
```

一个班 45 人一次交卷，一年下来不到 1 MB，拷文件即可。
