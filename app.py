#!/usr/bin/env python3
"""標準ライブラリのみで動作する足し算フォームのWSGIアプリ。"""

import html
import os
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server


def application(environ, start_response):
    query = parse_qs(environ.get("QUERY_STRING", ""))

    a_raw = query.get("a", [""])[0]
    b_raw = query.get("b", [""])[0]

    result = ""
    error = ""

    if a_raw or b_raw:
        try:
            a = float(a_raw)
            b = float(b_raw)
            total = a + b
            if total.is_integer():
                total_text = str(int(total))
            else:
                total_text = str(total)
            result = f"結果: {total_text}"
        except ValueError:
            error = "a と b には数値を入力してください。"

    body = f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>足し算フォーム</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; }}
    form {{ display: grid; gap: .75rem; max-width: 24rem; }}
    label {{ display: grid; gap: .25rem; }}
    input {{ padding: .5rem; font-size: 1rem; }}
    button {{ width: fit-content; padding: .5rem 1rem; }}
    .result {{ margin-top: 1rem; font-weight: bold; color: #0a5; }}
    .error {{ margin-top: 1rem; font-weight: bold; color: #b00; }}
  </style>
</head>
<body>
  <h1>足し算フォーム</h1>
  <form method=\"get\">
    <label>a
      <input type=\"number\" step=\"any\" name=\"a\" value=\"{html.escape(a_raw)}\" required />
    </label>
    <label>b
      <input type=\"number\" step=\"any\" name=\"b\" value=\"{html.escape(b_raw)}\" required />
    </label>
    <button type=\"submit\">計算する</button>
  </form>
  {f'<p class="result">{html.escape(result)}</p>' if result else ''}
  {f'<p class="error">{html.escape(error)}</p>' if error else ''}
</body>
</html>
"""

    encoded = body.encode("utf-8")
    start_response(
        "200 OK",
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(encoded))),
        ],
    )
    return [encoded]


if __name__ == "__main__":
    port = int(os.environ.get("port", "8000"))
    host = "0.0.0.0"
    print(f"Starting server on http://{host}:{port}")
    with make_server(host, port, application) as httpd:
        httpd.serve_forever()
