# -*- coding: utf-8 -*-
"""打开教材平台验证码登录页，填手机号、发验证码，等待 /tmp/sms_code.txt 出现后完成登录，
   并把登录态存到 tools/hnwy_state.json 供后续批量下载使用。"""
from playwright.sync_api import sync_playwright
import os, time, json, sys

EXE = '/Users/joyren/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell'
PHONE = '19522648565'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(BASE, 'tools', 'hnwy_state.json')
CODE_FILE = '/tmp/sms_code.txt'

def log(*a):
    print(*a, flush=True)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    ctx = b.new_context(viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    pg.goto('https://www.hnwymusic.com/web/user/login', wait_until='domcontentloaded', timeout=40000)
    pg.wait_for_timeout(1500)
    pg.get_by_text('验证码登录', exact=True).first.click(timeout=8000)
    pg.wait_for_timeout(1200)
    pg.fill('input[name=memberPhone]', PHONE)
    log('已填手机号')
    pg.get_by_text('获取验证码', exact=True).first.click(timeout=8000)
    log('已点击获取验证码')
    pg.wait_for_timeout(3000)
    pg.screenshot(path='/tmp/hnwy_sent.png')
    log('提示文本:', pg.inner_text('body').replace('\n', ' | ')[:200])

    code = None
    for _ in range(180):          # 最多等 6 分钟
        if os.path.exists(CODE_FILE):
            c = open(CODE_FILE).read().strip()
            if c:
                code = c
                break
        time.sleep(2)
    if not code:
        log('超时未收到验证码')
        b.close(); sys.exit(1)

    log('收到验证码', code)
    pg.fill('input[name=verifyCode]', code)
    pg.wait_for_timeout(300)
    try:
        pg.get_by_text('登录', exact=True).last.click(timeout=8000)
    except Exception as e:
        log('点登录失败，尝试提交表单', e)
        pg.keyboard.press('Enter')
    pg.wait_for_timeout(4000)
    log('登录后 URL:', pg.url)
    log('登录后标题:', pg.title())
    pg.screenshot(path='/tmp/hnwy_after.png')
    ctx.storage_state(path=STATE)
    log('登录态已保存', STATE, os.path.exists(STATE))
    b.close()
