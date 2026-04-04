"""
HELPER TDIU - Hech qanday kutubxona kerak emas!
"""
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.getenv("PORT", 8000))

HTML = b"""<!DOCTYPE html>
<html lang="uz"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HELPER TDIU</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0f0f14;color:#fff;
min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{text-align:center;padding:40px 24px}
.logo{font-size:72px;font-weight:900;color:#6c63ff;margin-bottom:16px}
.title{font-size:28px;font-weight:700;margin-bottom:8px}
.sub{font-size:14px;color:#888;margin-bottom:32px}
.badge{display:inline-block;background:rgba(34,197,94,.15);color:#22c55e;
border:1px solid rgba(34,197,94,.3);padding:10px 24px;border-radius:999px;
font-size:14px;font-weight:600}
</style></head>
<body><div class="card">
<div class="logo">H</div>
<div class="title">HELPER TDIU</div>
<div class="sub">TDIU Talaba Yordamchisi</div>
<div class="badge">Server ishlayapti!</div>
</div>
<script>window.Telegram?.WebApp?.expand();</script>
</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path in ('/', '/health'):
            b = json.dumps({"status":"ok","app":"HELPER TDIU"}).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',len(b))
            self.end_headers()
            self.wfile.write(b)
        elif self.path.startswith('/app'):
            self.send_response(200)
            self.send_header('Content-Type','text/html;charset=utf-8')
            self.send_header('Content-Length',len(HTML))
            self.end_headers()
            self.wfile.write(HTML)
        else:
            b = b'not found'
            self.send_response(404)
            self.send_header('Content-Length',len(b))
            self.end_headers()
            self.wfile.write(b)
    def do_POST(self):
        b = json.dumps({"ok":True}).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',len(b))
        self.end_headers()
        self.wfile.write(b)

if __name__ == '__main__':
    print(f"HELPER TDIU port {PORT} da ishlamoqda")
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
