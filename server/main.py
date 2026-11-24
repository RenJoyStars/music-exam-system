"""
湘珺 · 长沙市中考艺术检测机考模拟测试 —— 排行榜后端（最小实现）

只做两件事：
  POST /exam-api/score   收一条「交卷记录」
  GET  /exam-api/board   吐回最近的全部记录，排序聚合交给前端

设计取舍：
  · 不做用户体系，不存班级/姓名，只有昵称 + 卷号 + 对错数 —— 学生自娱自乐，够用且不碰个人信息。
  · 不做登录态，试题密码只在前端校验（防君子不防小人）；真要防刷靠 nginx 限频。
  · 聚合（做题榜/正确率榜/最高分榜）全在前端算，后端多一种榜不用改代码。

跑起来：
  pip install fastapi uvicorn
  uvicorn main:app --host 127.0.0.1 --port 8010
"""
import os
import sqlite3
import time
import pathlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = os.environ.get(
    "EXAM_DB", str(pathlib.Path(__file__).resolve().parent / "exam.db")
)
PREFIX = "/exam-api"

app = FastAPI(title="湘珺机考模拟 · 排行榜", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 只放行无凭证的读写，同域部署时其实用不到
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def db():
    c = sqlite3.connect(DB_PATH, timeout=5)
    c.execute(
        """CREATE TABLE IF NOT EXISTS scores(
               id  INTEGER PRIMARY KEY AUTOINCREMENT,
               n   TEXT    NOT NULL,   -- 昵称
               pid TEXT    NOT NULL,   -- 卷号
               r   INTEGER NOT NULL,   -- 答对
               t   INTEGER NOT NULL,   -- 总题
               s   INTEGER NOT NULL,   -- 用时（秒）
               at  INTEGER NOT NULL,   -- 交卷时间（毫秒）
               ip  TEXT
           )"""
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_scores_at ON scores(at)")
    return c


class Score(BaseModel):
    n: str = Field(min_length=1, max_length=12)
    pid: str = Field(min_length=1, max_length=32)
    r: int = Field(ge=0)
    t: int = Field(ge=1, le=100)
    s: int = Field(default=0, ge=0, le=36_000)


@app.get(PREFIX + "/health")
def health():
    return {"ok": True}


@app.get(PREFIX + "/board")
def board(limit: int = 3000):
    limit = max(1, min(limit, 5000))
    c = db()
    rows = c.execute(
        "SELECT n, pid, r, t, s, at FROM scores ORDER BY at DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    items = [
        {"n": n, "pid": p, "r": r, "t": t, "s": s, "at": a} for n, p, r, t, s, a in rows
    ]
    return {"items": items, "live": True}


@app.post(PREFIX + "/score")
def add_score(sc: Score, request: Request):
    if sc.r > sc.t:
        raise HTTPException(status_code=400, detail="答对数不能超过总题数")

    ip = request.client.host if request.client else ""
    now = int(time.time() * 1000)
    c = db()

    # 同一 IP + 同昵称 + 同卷，10 秒内重复提交视为重复交卷（防连点、防刷新重交）
    last = c.execute(
        "SELECT at FROM scores WHERE n=? AND pid=? AND ip=? ORDER BY id DESC LIMIT 1",
        (sc.n, sc.pid, ip),
    ).fetchone()
    if last and now - last[0] < 10_000:
        c.close()
        return {"ok": True, "dup": True}

    c.execute(
        "INSERT INTO scores(n,pid,r,t,s,at,ip) VALUES(?,?,?,?,?,?,?)",
        (sc.n, sc.pid, sc.r, sc.t, sc.s, now, ip),
    )
    c.commit()
    c.close()
    return {"ok": True}
