#!/usr/env python3
# -*- coding: utf-8 -*-
"""
Лендинг-редактор: локальный сервер для редактирования текста в HTML лендингах.

Запуск:
    python landing-editor.py                    # порт 8095
    python landing-editor.py --port 9000        # свой порт
    python landing-editor.py --dir D:\\Landing  # своя папка

Использование:
    1. Открой http://localhost:8095 в браузере
    2. Кликни на любой лендинг в списке
    3. Кликни на текст — появится поле редактирования
    4. Нажми Ctrl+S или кнопку Save — файл перезаписан
    5. Ctrl+Z — отмена
"""

import http.server
import urllib.parse
import json
import os
import re
import argparse
from pathlib import Path

HOST = "localhost"
DEFAULT_PORT = 8095


EDITOR_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Лендинг-редактор</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e1e4e8; }
.layout { display: flex; height: 100vh; }
.sidebar { width: 280px; background: #161b22; border-right: 1px solid #30363d; overflow-y: auto; padding: 20px; }
.sidebar h1 { font-size: 16px; margin-bottom: 16px; color: #58a6ff; }
.file-list { list-style: none; }
.file-list li { padding: 10px 12px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; font-size: 13px; transition: background 0.15s; word-break: break-all; }
.file-list li:hover { background: #21262d; }
.file-list li.active { background: #1f6feb; color: white; }
.file-list li .size { color: #8b949e; font-size: 11px; }
.preview { flex: 1; display: flex; flex-direction: column; }
.toolbar { padding: 12px 20px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 12px; }
.toolbar button { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-save { background: #238636; color: white; }
.btn-save:hover { background: #2ea043; }
.btn-revert { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
.btn-revert:hover { background: #30363d; }
.status { font-size: 12px; color: #8b949e; margin-left: auto; }
iframe { flex: 1; border: none; background: white; width: 100%; }
[contenteditable] { outline: 2px solid #58a6ff; outline-offset: 2px; background: rgba(88,166,255,0.1); border-radius: 2px; }
[contenteditable]:hover { outline-color: #f0883e; }
.toast { position: fixed; bottom: 20px; right: 20px; padding: 12px 20px; border-radius: 8px; background: #238636; color: white; font-size: 14px; opacity: 0; transition: opacity 0.3s; z-index: 9999; }
.toast.show { opacity: 1; }
.toast.error { background: #da3633; }
</style>
</head>
<body>
<div class="layout">
  <div class="sidebar">
    <h1>📁 Лендинги</h1>
    <ul class="file-list" id="files"></ul>
  </div>
  <div class="preview">
    <div class="toolbar">
      <button class="btn-save" id="saveBtn" disabled>💾 Save (Ctrl+S)</button>
      <button class="btn-revert" id="revertBtn" disabled>↺ Отменить</button>
      <span class="status" id="status">Выберите файл</span>
    </div>
    <iframe id="frame" src="about:blank"></iframe>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
let currentFile = null;
let changes = {};

const frame = document.getElementById('frame');
const saveBtn = document.getElementById('saveBtn');
const revertBtn = document.getElementById('revertBtn');
const status = document.getElementById('status');
const toast = document.getElementById('toast');

fetch('/api/files')
  .then(r => r.json())
  .then(files => {
    const ul = document.getElementById('files');
    files.forEach(f => {
      const li = document.createElement('li');
      li.innerHTML = f.name + '<br><span class="size">' + f.size + '</span>';
      li.onclick = () => loadFile(f.name, li);
      ul.appendChild(li);
    });
  })
  .catch(err => {
    document.getElementById('files').innerHTML = '<li style="color:#da3633">Ошибка: ' + err + '</li>';
  });

function loadFile(name, li) {
  document.querySelectorAll('.file-list li').forEach(e => e.classList.remove('active'));
  li.classList.add('active');
  currentFile = name;
  changes = {};
  saveBtn.disabled = true;
  revertBtn.disabled = true;
  status.textContent = 'Редактирую: ' + name;
  frame.src = '/preview/' + encodeURIComponent(name);
}

frame.onload = () => {
  const doc = frame.contentDocument;
  if (!doc) return;

  // Универсально: все элементы с текстом делаем редактируемыми
  // Включая элементы с дочерними тегами (span внутри p, br, и т.д.)
  const walker = doc.createTreeWalker(
    doc.body,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );

  const textParents = new Set();
  let node;
  while ((node = walker.nextNode())) {
    const text = node.textContent.trim();
    if (!text) continue;
    // Находим ближайший элемент-родитель для этого текстового узла
    let parent = node.parentElement;
    if (!parent) continue;
    // Поднимаемся до элемента который имеет visible text
    // но не выше body и не выше редактируемого родителя
    if (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE') continue;
    textParents.add(parent);
  }

  textParents.forEach(el => {
    // Пропускаем скрипты и стили
    if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
    // Пропускаем если нет видимого текста
    if (!el.textContent.trim()) return;

    el.setAttribute('contenteditable', 'true');
    el.dataset.original = el.textContent;

    el.addEventListener('input', () => {
      if (el.textContent !== el.dataset.original) {
        changes[el.dataset.original] = el.textContent;
        saveBtn.disabled = false;
        revertBtn.disabled = false;
        status.textContent = '✏️ Изменений: ' + Object.keys(changes).length + ' — ' + currentFile;
      } else {
        delete changes[el.dataset.original];
        if (Object.keys(changes).length === 0) {
          saveBtn.disabled = true;
          revertBtn.disabled = true;
          status.textContent = 'Редактирую: ' + currentFile;
        }
      }
    });
  });
};

function showToast(msg, isError) {
  toast.textContent = msg;
  toast.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => toast.className = 'toast', 2000);
}

function saveChanges() {
  if (!currentFile || Object.keys(changes).length === 0) return;
  fetch('/api/save', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({file: currentFile, changes: changes})
  })
  .then(r => r.json())
  .then(res => {
    if (res.success) {
      showToast('✅ Сохранено: ' + Object.keys(changes).length + ' правок');
      changes = {};
      saveBtn.disabled = true;
      revertBtn.disabled = true;
      status.textContent = 'Редактирую: ' + currentFile;
    } else {
      showToast('❌ ' + res.error, true);
    }
  });
}

function revertChanges() {
  const doc = frame.contentDocument;
  if (!doc) return;
  doc.querySelectorAll('[contenteditable]').forEach(el => {
    if (el.dataset.original) el.textContent = el.dataset.original;
  });
  changes = {};
  saveBtn.disabled = true;
  revertBtn.disabled = true;
  status.textContent = 'Редактирую: ' + currentFile;
  showToast('↺ Изменения отменены');
}

saveBtn.onclick = saveChanges;
revertBtn.onclick = revertChanges;

document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveChanges();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
    e.preventDefault();
    revertChanges();
  }
});
</script>
</body>
</html>
"""


class EditorHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        self.landing_dir = directory or Path.cwd()
        super().__init__(*args, directory=str(self.landing_dir), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(EDITOR_HTML.encode("utf-8"))
            return

        if parsed.path == "/api/files":
            files = []
            for f in sorted(self.landing_dir.glob("*.html")):
                size = f.stat().st_size
                if size > 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                files.append({"name": f.name, "size": size_str})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(files).encode("utf-8"))
            return

        if parsed.path.startswith("/preview/"):
            filename = urllib.parse.unquote(parsed.path[9:])
            filepath = self.landing_dir / filename
            if filepath.exists() and filepath.suffix == ".html":
                content = filepath.read_text(encoding="utf-8", errors="replace")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            else:
                self.send_error(404)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/save":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            filename = data.get("file", "")
            changes = data.get("changes", {})

            filepath = self.landing_dir / filename
            if not filepath.exists() or filepath.suffix != ".html":
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Файл не найден"}).encode("utf-8"))
                return

            backup = filepath.with_suffix(".html.bak")
            backup.write_text(filepath.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")

            content = filepath.read_text(encoding="utf-8", errors="replace")

            for old_text, new_text in changes.items():
                if old_text == new_text:
                    continue
                escaped = re.escape(old_text)
                content = re.sub(escaped, lambda m: new_text, content, count=1)

            filepath.write_text(content, encoding="utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "saved": len(changes)}).encode("utf-8"))
            return

        self.send_error(404)

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Лендинг-редактор")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Порт (по умолчанию 8095)")
    parser.add_argument("--dir", type=str, default=None, help="Папка с лендингами")
    args = parser.parse_args()

    landing_dir = Path(args.dir) if args.dir else Path("D:/Hermes_Projects/Landing-Pages")
    if not landing_dir.exists():
        print(f"Папка не найдена: {landing_dir}")
        print("   Укажи --dir /путь/к/лендингам")
        return

    server = http.server.HTTPServer(
        (HOST, args.port),
        lambda *a, **kw: EditorHandler(*a, directory=landing_dir, **kw)
    )

    count = len(list(landing_dir.glob("*.html")))
    print("=" * 50)
    print("  Лендинг-редактор запущен")
    print(f"  Адрес:  http://{HOST}:{args.port}")
    print(f"  Папка:  {landing_dir}")
    print(f"  Лендингов: {count}")
    print("  Ctrl+C - остановить")
    print("=" * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановлен")
        server.shutdown()


if __name__ == "__main__":
    main()
