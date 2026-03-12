"""
Gallery: A lightweight HTTP image/video gallery server.

Serves a directory of captures as a browseable HTML gallery.
Can be run standalone or embedded in scripts via context manager
or background thread.

Example::

    from camera.gallery import GalleryServer

    # Blocking (standalone)
    GalleryServer("captures/").serve()

    # Non-blocking background server
    with GalleryServer("captures/", port=8080) as srv:
        print(f"Gallery at {srv.url}")
        ...  # do other work

    # One-liner helper
    GalleryServer.open("captures/")
"""

from __future__ import annotations

import html
import mimetypes
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote


# ── MIME helpers ──────────────────────────────────────────────────────────────

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS


# ── HTML templates ────────────────────────────────────────────────────────────

_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Pi-Printer Gallery · {title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: system-ui, sans-serif;
      background: #111;
      color: #eee;
      padding: 1.5rem;
    }}
    h1 {{ font-size: 1.2rem; margin-bottom: 1rem; color: #aaa; }}
    h1 span {{ color: #fff; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1rem;
    }}
    .card {{
      background: #1e1e1e;
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .card a {{
      display: block;
      aspect-ratio: 16/9;
      overflow: hidden;
      background: #000;
    }}
    .card img, .card video {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: opacity .2s;
    }}
    .card img:hover {{ opacity: .85; }}
    .card .label {{
      font-size: .75rem;
      color: #888;
      padding: .4rem .6rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .empty {{
      color: #555;
      margin-top: 3rem;
      text-align: center;
      font-size: 1rem;
    }}
    .subdirs {{
      display: flex;
      flex-wrap: wrap;
      gap: .5rem;
      margin-bottom: 1.5rem;
    }}
    .subdirs a {{
      background: #2a2a2a;
      color: #ccc;
      text-decoration: none;
      padding: .35rem .8rem;
      border-radius: 6px;
      font-size: .85rem;
    }}
    .subdirs a:hover {{ background: #333; color: #fff; }}
    .breadcrumb {{ font-size: .85rem; color: #666; margin-bottom: 1.2rem; }}
    .breadcrumb a {{ color: #888; text-decoration: none; }}
    .breadcrumb a:hover {{ color: #fff; }}
    .breadcrumb span {{ color: #aaa; margin: 0 .3rem; }}
  </style>
</head>
<body>
  <h1>Pi-Printer Gallery · <span>{title}</span></h1>
  {breadcrumb}
  {subdirs}
  {content}
</body>
</html>
"""

_CRUMB_ITEM  = '<a href="{href}">{label}</a><span>›</span>'
_SUBDIR_ITEM = '<a href="{href}">📁 {label}/</a>'
_IMG_CARD    = """\
<div class="card">
  <a href="{file_url}" target="_blank">
    <img src="{file_url}" alt="{name}" loading="lazy"/>
  </a>
  <div class="label">{name}</div>
</div>"""
_VID_CARD    = """\
<div class="card">
  <a href="{file_url}" target="_blank">
    <video src="{file_url}" muted playsinline
           onmouseenter="this.play()" onmouseleave="this.pause();this.currentTime=0">
    </video>
  </a>
  <div class="label">{name}</div>
</div>"""


# ── LAN IP helper ─────────────────────────────────────────────────────────────

def _lan_ip() -> str:
    """Return the machine's LAN IP, falling back to localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


# ── Request handler ───────────────────────────────────────────────────────────

class _GalleryHandler(BaseHTTPRequestHandler):
    """Serves gallery HTML for directories; raw files for media."""

    root: Path  # set by GalleryServer before binding

    def log_message(self, fmt, *args):  # silence default stdio logging
        pass

    def do_GET(self):
        rel = unquote(self.path.lstrip("/")) or ""
        target = (self.root / rel).resolve()

        # Security: must stay inside root
        try:
            target.relative_to(self.root.resolve())
        except ValueError:
            self._send(403, "text/plain", b"Forbidden")
            return

        if target.is_dir():
            self._serve_gallery(target, rel)
        elif target.is_file():
            self._serve_file(target)
        else:
            self._send(404, "text/plain", b"Not found")

    # ── directory → HTML ──────────────────────────────────────────────────────

    def _serve_gallery(self, directory: Path, rel: str):
        entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name))

        subdirs = [e for e in entries if e.is_dir()]
        media   = [e for e in entries if e.is_file() and e.suffix.lower() in MEDIA_EXTS]

        # breadcrumb
        parts  = [p for p in rel.split("/") if p]
        crumbs = ['<a href="/">captures</a>']
        for i, part in enumerate(parts):
            href = "/" + "/".join(parts[: i + 1])
            crumbs.append(_CRUMB_ITEM.format(href=href, label=html.escape(part)))
        breadcrumb = (
            '<div class="breadcrumb">' + " ".join(crumbs) + "</div>" if parts else ""
        )

        # sub-directory pills
        sd_html = ""
        if subdirs:
            items = [
                _SUBDIR_ITEM.format(
                    href=("/" + rel + "/" + d.name).replace("//", "/"),
                    label=html.escape(d.name),
                )
                for d in subdirs
            ]
            sd_html = '<div class="subdirs">' + "".join(items) + "</div>"

        # media grid
        if media:
            cards = []
            for f in media:
                file_url = ("/" + rel + "/" + f.name).replace("//", "/")
                name     = html.escape(f.name)
                if f.suffix.lower() in VIDEO_EXTS:
                    cards.append(_VID_CARD.format(file_url=file_url, name=name))
                else:
                    cards.append(_IMG_CARD.format(file_url=file_url, name=name))
            content = '<div class="grid">' + "".join(cards) + "</div>"
        else:
            content = '<p class="empty">No images or videos here yet.</p>'

        title = parts[-1] if parts else "/"
        body  = _PAGE.format(
            title=html.escape(title),
            breadcrumb=breadcrumb,
            subdirs=sd_html,
            content=content,
        )
        self._send(200, "text/html; charset=utf-8", body.encode())

    # ── file → streamed bytes with Range support ──────────────────────────────

    _CHUNK = 512 * 1024  # 512 KB read chunks

    def _serve_file(self, path: Path):
        mime, _ = mimetypes.guess_type(str(path))
        mime = mime or "application/octet-stream"
        size = path.stat().st_size

        range_header = self.headers.get("Range")

        if range_header:
            # Parse "bytes=start-end"
            try:
                byte_range = range_header.strip().replace("bytes=", "")
                start_str, _, end_str = byte_range.partition("-")
                start = int(start_str) if start_str else 0
                end   = int(end_str)   if end_str   else size - 1
            except ValueError:
                self._send_error(416, "Requested Range Not Satisfiable")
                return

            start = max(0, start)
            end   = min(end, size - 1)
            length = end - start + 1

            self.send_response(206)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(length))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            self._stream_file(path, start, length)
        else:
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            self._stream_file(path, 0, size)

    def _stream_file(self, path: Path, offset: int, length: int):
        """Stream *length* bytes from *path* starting at *offset*."""
        try:
            with open(path, "rb") as f:
                f.seek(offset)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(self._CHUNK, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client disconnected mid-stream – not an error

    # ── low-level send ────────────────────────────────────────────────────────

    def _send(self, code: int, content_type: str, body: bytes):
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_error(self, code: int, message: str):
        body = message.encode()
        self._send(code, "text/plain", body)


# ── Public API ────────────────────────────────────────────────────────────────

class GalleryServer:
    """
    Lightweight HTTP gallery server for a captures directory.

    Parameters
    ----------
    root:
        Directory to serve. Defaults to ``captures/`` relative to cwd.
    port:
        TCP port to listen on. Defaults to 8080.
    """

    def __init__(self, root: str | Path = "captures", port: int = 8080):
        self.root = Path(root).resolve()
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    # ── convenience ───────────────────────────────────────────────────────────

    @property
    def url(self) -> str:
        """Best-guess URL using the machine's LAN IP."""
        return f"http://{_lan_ip()}:{self.port}"

    # ── blocking ──────────────────────────────────────────────────────────────

    def serve(self):
        """Start a blocking server (Ctrl-C to stop)."""
        self._make_server()
        print(f"  Gallery → {self.url}  (Ctrl-C to stop)")
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            print("\n  Gallery server stopped.")
        finally:
            self._server.server_close()

    # ── non-blocking ──────────────────────────────────────────────────────────

    def start(self):
        """Start the server in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._make_server()
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="GalleryServer",
        )
        self._thread.start()
        time.sleep(0.1)  # let the port bind before returning
        print(f"  Gallery → {self.url}")

    def stop(self):
        """Shut down the background server."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    # ── context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "GalleryServer":
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    # ── internal ──────────────────────────────────────────────────────────────

    def _make_server(self):
        self.root.mkdir(parents=True, exist_ok=True)
        handler = type("_H", (_GalleryHandler,), {"root": self.root})
        self._server = HTTPServer(("", self.port), handler)

    # ── static helper ─────────────────────────────────────────────────────────

    @staticmethod
    def open(root: str | Path = "captures", port: int = 8080):
        """Blocking one-liner: ``GalleryServer.open('captures/')``."""
        GalleryServer(root, port).serve()
