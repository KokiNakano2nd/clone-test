#!/usr/bin/env python3
"""標準ライブラリだけで動く、1ページ足し算フォームアプリ。"""

import html
import os
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server


def _format_number(value: float) -> str:
    """整数は整数表記、小数は不要な末尾0を除去して表示する。"""
    if value.is_integer():
        return str(int(value))
    return (f"{value:.12f}").rstrip("0").rstrip(".")


def _parse_and_add(a_raw: str, b_raw: str):
    """入力値をパースして合計を返す。失敗時はエラーメッセージを返す。"""
    if not a_raw and not b_raw:
        return "", ""

    if not a_raw or not b_raw:
        return "", "a と b の両方を入力してください。"

    try:
        a = float(a_raw)
        b = float(b_raw)
    except ValueError:
        return "", "a と b には数値を入力してください。"

    return _format_number(a + b), ""


def application(environ, start_response):
    query = parse_qs(environ.get("QUERY_STRING", ""))
    a_raw = query.get("a", [""])[0].strip()
    b_raw = query.get("b", [""])[0].strip()

    total, error = _parse_and_add(a_raw, b_raw)
    has_result = bool(total)

    body = f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>足し算フォーム</title>
  <style>
    :root {{
      --bg: #0b1020;
      --card: #121a30;
      --text: #eaf0ff;
      --muted: #9fb0d8;
      --accent: #4f8cff;
      --ok: #2dcc92;
      --err: #ff6b7a;
      --border: #253354;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: radial-gradient(circle at 20% 10%, #182645, var(--bg) 45%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans JP", sans-serif;
      padding: 1rem;
    }}
    .card {{
      width: min(100%, 520px);
      background: linear-gradient(160deg, #17233f, var(--card));
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, .35);
      padding: 1.25rem;
    }}
    h1 {{ margin: 0 0 .4rem; font-size: 1.4rem; }}
    p.help {{ margin: 0 0 1rem; color: var(--muted); font-size: .95rem; }}
    form {{ display: grid; gap: .8rem; }}
    .row {{ display: grid; gap: .8rem; grid-template-columns: 1fr 1fr; }}
    label {{ display: grid; gap: .35rem; font-weight: 600; }}
    input {{
      width: 100%;
      background: #0d152c;
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 10px;
      padding: .65rem .75rem;
      font-size: 1rem;
      outline: none;
    }}
    input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(79, 140, 255, .2); }}
    .actions {{ display: flex; gap: .6rem; flex-wrap: wrap; }}
    button {{
      border: 0;
      border-radius: 10px;
      padding: .65rem 1rem;
      font-weight: 700;
      cursor: pointer;
    }}
    button[type=submit] {{ background: var(--accent); color: #fff; }}
    button[type=button] {{ background: #22335a; color: var(--text); }}
    .result, .error {{
      margin-top: .9rem;
      padding: .8rem .9rem;
      border-radius: 10px;
      font-weight: 700;
      border: 1px solid transparent;
    }}
    .result {{ background: rgba(45, 204, 146, .12); border-color: rgba(45, 204, 146, .35); color: #8df5cb; }}
    .error {{ background: rgba(255, 107, 122, .12); border-color: rgba(255, 107, 122, .35); color: #ffadba; }}
    .ghost {{ color: var(--muted); font-weight: 500; margin-top: .9rem; }}
    @media (max-width: 460px) {{ .row {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main class=\"card\">
    <h1>🧮 足し算フォーム</h1>
    <p class=\"help\">a と b を入力すると、その場で合計を表示します（サーバー計算にも対応）。</p>

    <form method=\"get\" action=\"/\" id=\"add-form\">
      <div class=\"row\">
        <label for=\"a\">a
          <input id=\"a\" type=\"number\" step=\"any\" name=\"a\" value=\"{html.escape(a_raw)}\" placeholder=\"例: 2\" />
        </label>
        <label for=\"b\">b
          <input id=\"b\" type=\"number\" step=\"any\" name=\"b\" value=\"{html.escape(b_raw)}\" placeholder=\"例: 3\" />
        </label>
      </div>
      <div class=\"actions\">
        <button type=\"submit\">サーバーで計算</button>
        <button type=\"button\" id=\"clear-btn\">クリア</button>
      </div>
    </form>

    <div id=\"live-result\" class=\"ghost\">入力待ちです。</div>
    {f'<p class="result">結果: {html.escape(total)}</p>' if has_result else ''}
    {f'<p class="error">{html.escape(error)}</p>' if error else ''}
  </main>

  <script>
    (function () {{
      const aInput = document.getElementById('a');
      const bInput = document.getElementById('b');
      const live = document.getElementById('live-result');
      const clearBtn = document.getElementById('clear-btn');

      const formatNumber = (n) => {{
        if (Number.isInteger(n)) return String(n);
        return n.toString();
      }};

      const update = () => {{
        const a = aInput.value.trim();
        const b = bInput.value.trim();

        if (!a && !b) {{
          live.className = 'ghost';
          live.textContent = '入力待ちです。';
          return;
        }}

        if (!a || !b) {{
          live.className = 'error';
          live.textContent = 'a と b の両方を入力してください。';
          return;
        }}

        const aNum = Number(a);
        const bNum = Number(b);
        if (!Number.isFinite(aNum) || !Number.isFinite(bNum)) {{
          live.className = 'error';
          live.textContent = 'a と b には数値を入力してください。';
          return;
        }}

        live.className = 'result';
        live.textContent = `ライブ結果: ${{formatNumber(aNum + bNum)}}`;
      }};

      aInput.addEventListener('input', update);
      bInput.addEventListener('input', update);
      clearBtn.addEventListener('click', () => {{
        aInput.value = '';
        bInput.value = '';
        update();
        aInput.focus();
      }});

      update();
    }})();
  </script>
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
