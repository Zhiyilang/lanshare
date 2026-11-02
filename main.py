#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lanshare — 零依赖局域网文件快传

同 WiFi / 局域网内，一台机器运行本程序开 HTTP 服务，
手机或其他电脑浏览器打开地址即可上传 / 下载 / 删除文件。
无需安装任何第三方库，标准库即可运行。

用法:
    python lanshare.py                 # 默认端口 8000，共享当前目录
    python lanshare.py -p 9000         # 指定端口
    python lanshare.py -d /path/share  # 指定共享目录
    python lanshare.py --host 0.0.0.0  # 绑定所有网卡(默认已绑定 0.0.0.0)

停止: Ctrl+C
"""
import argparse
import html
import http.server
import os
import posixpath
import re
import socketserver
import urllib.parse
from http import HTTPStatus

DEFAULT_PORT = 8000
MAX_UPLOAD_MB = 2000  # 单个文件上限 2GB(由客户端/磁盘决定, 仅作提示)


def human_size(n):
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    for u in units:
        if f < 1024 or u == units[-1]:
            return f"{f:.1f}{u}" if u != "B" else f"{int(n)}B"
        f /= 1024


class LANShareHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "lanshare/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _page(self, body_html, title="lanshare 局域网快传", status=HTTPStatus.OK):
        """渲染一个带基础样式的 HTML 页面。"""
        doc = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
*{{box-sizing:border-box}} body{{font-family:-apple-system,system-ui,"Microsoft YaHei",sans-serif;margin:0;background:#0f1115;color:#e6e6e6}}
.header{{padding:18px 20px;background:#161a22;border-bottom:1px solid #232a36;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
.header h1{{font-size:18px;margin:0;flex:1}}
.tag{{font-size:12px;color:#7ee787;background:#10261a;padding:3px 8px;border-radius:6px}}
.wrap{{max-width:860px;margin:0 auto;padding:20px}}
.card{{background:#161a22;border:1px solid #232a36;border-radius:12px;padding:16px;margin-bottom:16px}}
input[type=file],input[type=text]{{color:#e6e6e6}}
.btn{{display:inline-block;padding:8px 14px;border:none;border-radius:8px;background:#2f81f7;color:#fff;cursor:pointer;font-size:14px;text-decoration:none}}
.btn:hover{{background:#4493f8}}
.btn.danger{{background:#da3633}}
table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid #232a36;font-size:14px}}
a.dl{{color:#58a6ff;text-decoration:none}}
.hint{{color:#8b949e;font-size:13px}}
code{{background:#0d1117;padding:2px 6px;border-radius:4px}}
</style></head>
<body>
<div class="header"><h1>📡 lanshare 局域网快传</h1><span class="tag">零依赖 · 标准库</span></div>
<div class="wrap">{body_html}</div>
</body></html>"""
        data = doc.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _list_body(self):
        base = self.directory
        items = []
        try:
            entries = sorted(os.listdir(base))
        except OSError:
            entries = []
        for name in entries:
            if name == os.path.basename(__file__) or name == "lanshare.py":
                continue  # 不显示自身
            p = os.path.join(base, name)
            if os.path.isdir(p):
                continue
            try:
                st = os.stat(p)
                size = human_size(st.st_size)
                mtime = __import__("time").strftime("%Y-%m-%d %H:%M", __import__("time").localtime(st.st_mtime))
            except OSError:
                size, mtime = "-", "-"
            safe = urllib.parse.quote(name)
            items.append(
                f"<tr><td><a class='dl' href='/download?f={safe}'>📥 {html.escape(name)}</a></td>"
                f"<td class='hint'>{size}</td><td class='hint'>{mtime}</td>"
                f"<td><a class='btn danger' href='/delete?f={safe}' onclick=\"return confirm('确认删除 {html.escape(name)}?')\">删除</a></td></tr>"
            )
        rows = "".join(items) if items else "<tr><td colspan='4' class='hint'>目录为空，上传第一个文件吧。</td></tr>"
        upload_url = self.path if self.path.startswith("/upload") else "/upload"
        return f"""
<div class="card">
  <h3 style="margin-top:0">⬆️ 上传文件</h3>
  <form method="post" action="/upload" enctype="multipart/form-data">
    <input type="file" name="file" multiple required>
    <p><button class="btn" type="submit">上传到本机</button>
    <span class="hint">单文件上限约 {MAX_UPLOAD_MB}MB · 支持多选</span></p>
  </form>
</div>
<div class="card">
  <h3 style="margin-top:0">📂 共享文件 ({len(items)})</h3>
  <table><thead><tr><th>文件名</th><th>大小</th><th>修改时间</th><th>操作</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>
<p class="hint">提示：手机扫码或浏览器打开上方「本机地址」即可访问本页面。文件保存在 <code>{html.escape(base)}</code></p>
"""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self._page(self._list_body())
        elif parsed.path == "/download":
            self._serve_file(parsed)
        elif parsed.path == "/delete":
            self._delete_file(parsed)
        else:
            # 兜底：标准库静态文件服务
            super().do_GET()

    def _safe_path(self, parsed):
        q = urllib.parse.parse_qs(parsed.query)
        name = q.get("f", [""])[0]
        if not name:
            return None
        # 防目录穿越
        name = posixpath.normpath(name).lstrip("./\\")
        if name.startswith("..") or "/" in name or "\\" in name:
            return None
        return os.path.join(self.directory, name)

    def _serve_file(self, parsed):
        p = self._safe_path(parsed)
        if not p or not os.path.isfile(p):
            self._page("<p class='hint'>文件不存在。</p>", status=HTTPStatus.NOT_FOUND)
            return
        try:
            sz = os.path.getsize(p)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(sz))
            self.send_header("Content-Disposition",
                             f"attachment; filename*=UTF-8''{urllib.parse.quote(os.path.basename(p))}")
            self.end_headers()
            with open(p, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except OSError as e:
            self._page(f"<p class='hint'>读取失败: {html.escape(str(e))}</p>", status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _delete_file(self, parsed):
        p = self._safe_path(parsed)
        if p and os.path.isfile(p):
            try:
                os.remove(p)
                self._page("<p>✅ 已删除。</p>" + self._list_body())
                return
            except OSError as e:
                self._page(f"<p class='hint'>删除失败: {html.escape(str(e))}</p>", status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
        self._page("<p class='hint'>文件不存在。</p>", status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/upload":
            self._page("<p class='hint'>未知操作。</p>", status=HTTPStatus.NOT_FOUND)
            return
        # 解析 multipart/form-data
        ctype = self.headers.get("Content-Type", "")
        m = re.match(r"multipart/form-data; boundary=(.+)", ctype)
        if not m:
            self._page("<p class='hint'>仅支持 multipart 上传。</p>", status=HTTPStatus.BAD_REQUEST)
            return
        boundary = m.group(1).encode()
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length <= 0:
            self._page("<p class='hint'>空请求。</p>", status=HTTPStatus.BAD_REQUEST)
            return
        raw = self.rfile.read(length)
        saved = self._parse_multipart(raw, boundary)
        if saved:
            names = "、".join(html.escape(n) for n in saved)
            msg = f"<p>✅ 已接收 {len(saved)} 个文件：{names}</p>"
        else:
            msg = "<p class='hint'>未解析到文件。</p>"
        self._page(msg + self._list_body())

    def _parse_multipart(self, raw, boundary):
        """极简 multipart 解析，仅提取 filename + 文件内容。"""
        saved = []
        delim = b"--" + boundary
        parts = raw.split(delim)
        for part in parts:
            if part in (b"", b"--", b"--\r\n"):
                continue
            # 头部与正文以 \r\n\r\n 分隔
            if b"\r\n\r\n" not in part:
                continue
            head, _, body = part.partition(b"\r\n\r\n")
            if b"filename=" not in head:
                continue
            fn_m = re.search(rb'filename="([^"]*)"', head)
            if not fn_m:
                continue
            fname = fn_m.group(1).decode("utf-8", "ignore")
            if not fname:
                continue
            fname = os.path.basename(fname)
            # body 末尾可能有 \r\n
            if body.endswith(b"\r\n"):
                body = body[:-2]
            dest = os.path.join(self.directory, fname)
            # 避免覆盖：重名加后缀
            if os.path.exists(dest):
                base, ext = os.path.splitext(fname)
                i = 1
                while os.path.exists(os.path.join(self.directory, f"{base}({i}){ext}")):
                    i += 1
                dest = os.path.join(self.directory, f"{base}({i}){ext}")
                fname = os.path.basename(dest)
            with open(dest, "wb") as f:
                f.write(body)
            saved.append(fname)
        return saved

    def log_message(self, fmt, *args):
        # 简化日志，仅打印关键行
        msg = fmt % args
        if "GET / " in msg or "POST /upload" in msg:
            print(f"[lanshare] {msg}")


def get_lan_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser(description="零依赖局域网文件快传")
    ap.add_argument("-p", "--port", type=int, default=DEFAULT_PORT, help="端口(默认 8000)")
    ap.add_argument("-d", "--directory", default=os.getcwd(), help="共享目录(默认当前目录)")
    ap.add_argument("--host", default="0.0.0.0", help="绑定地址(默认 0.0.0.0)")
    args = ap.parse_args()

    share_dir = os.path.abspath(args.directory)
    os.makedirs(share_dir, exist_ok=True)

    handler = lambda *a, **k: LANShareHandler(*a, directory=share_dir, **k)
    with socketserver.ThreadingTCPServer((args.host, args.port), handler) as httpd:
        ip = get_lan_ip()
        print("=" * 52)
        print("  lanshare 已启动 — 局域网文件快传")
        print("=" * 52)
        print(f"  本机地址 :  http://{ip}:{args.port}/")
        print(f"  本机回环 :  http://127.0.0.1:{args.port}/")
        print(f"  共享目录 :  {share_dir}")
        print(f"  手机/其他电脑连同一 WiFi 后，浏览器打开上方「本机地址」即可。")
        print("  按 Ctrl+C 停止。")
        print("=" * 52)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[lanshare] 已停止。")


if __name__ == "__main__":
    main()
