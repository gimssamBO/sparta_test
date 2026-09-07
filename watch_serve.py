#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md 저장 -> html 자동 재생성 -> 브라우저 자동 새로고침

사용법:
    1) 이 프로젝트 폴더(build_html.py 가 있는 폴더)에서 실행:
         python watch_serve.py
    2) 콘솔에 뜨는 주소(기본 http://127.0.0.1:8765/)를 브라우저에서 열어둔다.
    3) 옵시디언(또는 다른 편집기)에서 01_교안의 md 파일을 저장할 때마다
       html이 자동으로 다시 만들어지고, 열어둔 브라우저 탭도 자동으로 새로고침된다.
    4) 종료하려면 터미널에서 Ctrl+C.

주의:
    - html 파일을 더블클릭해서 직접 열면(file://) 이 기능이 동작하지 않는다.
      반드시 위 주소(http://127.0.0.1:8765/)로 열어야 자동 새로고침된다.
    - build_html.py 와 같은 폴더에 있어야 한다 (내부적으로 build_html.py를 그대로 사용).
"""

import http.server
import json
import socketserver
import threading
import time
import urllib.parse
from pathlib import Path

import build_html

OUT_DIR = build_html.OUT_DIR
OUT_FILE = build_html.OUT_FILE
MD_DIR = build_html.MD_DIR
PORT = 8765

RELOAD_SNIPPET = """
<script>
(function(){
  var last = null;
  setInterval(function(){
    fetch('/__status__', {cache:'no-store'}).then(function(r){ return r.json(); }).then(function(data){
      if (last === null) { last = data.mtime; return; }
      if (data.mtime !== last) { location.reload(); }
    }).catch(function(){});
  }, 1000);
})();
</script>
"""

state = {"mtime": 0.0, "error": None}


def rebuild(reason=""):
    try:
        build_html.main()
        state["mtime"] = OUT_FILE.stat().st_mtime
        state["error"] = None
    except SystemExit as e:
        state["error"] = str(e)
        print(f"[오류] {e}")
    except Exception as e:
        state["error"] = str(e)
        print(f"[오류] {e}")


def watch_loop():
    mtimes = {}
    while True:
        try:
            changed = False
            for f in MD_DIR.glob("*.md"):
                m = f.stat().st_mtime
                if mtimes.get(f) != m:
                    if f in mtimes:
                        changed = True
                    mtimes[f] = m
            if changed:
                time.sleep(0.3)  # 저장이 끝날 때까지 짧게 대기
                rebuild("md 변경 감지")
                print(f"[재생성] {OUT_FILE.name} 갱신 완료 ({time.strftime('%H:%M:%S')})")
        except Exception as e:
            print(f"[감시 오류] {e}")
        time.sleep(1)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUT_DIR), **kwargs)

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])
        if path == "/__status__":
            body = json.dumps({"mtime": state["mtime"], "error": state["error"]}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if path in ("/", "/index.html", f"/{OUT_FILE.name}"):
            html_text = OUT_FILE.read_text(encoding="utf-8")
            if "</body>" in html_text:
                html_text = html_text.replace("</body>", RELOAD_SNIPPET + "</body>")
            body = html_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        pass


def main():
    rebuild("서버 시작")
    print(f"[초기 빌드] {OUT_FILE.name} 준비 완료")
    t = threading.Thread(target=watch_loop, daemon=True)
    t.start()
    try:
        with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
            url = f"http://127.0.0.1:{PORT}/"
            print(f"[서버 시작] {url}  <- 이 주소를 브라우저에서 열어두세요 (Ctrl+C로 종료)")
            httpd.serve_forever()
    except OSError as e:
        print(f"[오류] 포트 {PORT}를 사용할 수 없습니다: {e}")
        print("watch_serve.py 상단의 PORT 값을 다른 숫자로 바꿔 다시 실행해보세요.")
    except KeyboardInterrupt:
        print("\n[종료]")


if __name__ == "__main__":
    main()
