"""Local AMOE page. Loopback only. GET never colors a page.

Wheel paint and engine membership stay separate requests.
In-band densitometry is returned as its own header, not as the plate color.

Author: Aziel Eliab.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from amoe import AmoeError, __version__
from amoe.doctor import doctor_card
from amoe.gallery import save_gallery
from amoe.wheel import GRID, reject_name
from amoe.wrap import invention_card, load_page, process

LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})
WEB = files("amoe") / "web"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}
MAX_UPLOAD = 12 * 1024 * 1024
DEFAULT_PORT = 8871


def _web_bytes(name: str) -> bytes:
    return (WEB / name).read_bytes()


def _wants_json(header: str | None) -> bool:
    return "application/json" in str(header or "").lower()


class Handler(BaseHTTPRequestHandler):
    server_version = f"AMOE/{__version__}"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra:
            for key, value in extra.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, obj: object) -> None:
        body = json.dumps(obj, indent=2).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            if _wants_json(self.headers.get("Accept")):
                self._json(
                    200,
                    {
                        "product": "amoe",
                        "version": __version__,
                        "author": "Aziel Eliab",
                        "amoe_is_wiring": True,
                        "amoe_is_field": False,
                        "pigment_recovery": False,
                        "loopback": True,
                        "ui": f"http://127.0.0.1:{DEFAULT_PORT}/",
                    },
                )
                return
            self._send(200, _web_bytes("index.html"), MIME[".html"])
            return
        if path == "/style.css":
            self._send(200, _web_bytes("style.css"), MIME[".css"])
            return
        if path == "/app.js":
            self._send(200, _web_bytes("app.js"), MIME[".js"])
            return
        if path == "/api/doctor":
            self._json(200, doctor_card())
            return
        if path == "/api/sample":
            from spectrallock.engine import png_bytes, synthetic_page

            png = png_bytes(synthetic_page(192, 192))
            self._send(
                200,
                png,
                "image/png",
                {"Content-Disposition": 'inline; filename="sample-page.png"'},
            )
            return
        self._json(404, {"message": "That page is not on this local server."})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/color":
            self._post_color()
            return
        if path == "/api/gallery":
            self._post_gallery()
            return
        self._json(404, {"message": "That page is not on this local server."})

    def _read_body(self) -> bytes | None:
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            self._json(400, {"message": "Choose a PNG or JPEG page.", "refuse": "AMOE-NO-PAGE"})
            return None
        if length <= 0:
            self._json(400, {"message": "Choose a PNG or JPEG page.", "refuse": "AMOE-NO-PAGE"})
            return None
        if length > MAX_UPLOAD:
            self._json(400, {"message": "That picture is too big (max 12 MB).", "refuse": "AMOE-TOO-BIG"})
            return None
        return self.rfile.read(length)

    def _post_color(self) -> None:
        raw = self._read_body()
        if raw is None:
            return
        fields = _parse_fields(raw, self.headers.get("Content-Type") or "")
        mode = str(fields.get("mode") or "tazel").strip().lower()
        paint = str(fields.get("paint") or "wheel").strip().lower()
        lift = str(fields.get("lift") or "").lower() in {"1", "true", "on", "yes"}
        geom_off = str(fields.get("geom") or "1").lower() in {"0", "false", "off", "no"}
        image = fields.get("file")
        if not isinstance(image, (bytes, bytearray)) or not image:
            self._json(400, {"message": "Choose a PNG or JPEG page.", "refuse": "AMOE-NO-PAGE"})
            return
        code = reject_name(mode)
        if code:
            card = invention_card(code)
            card["mode"] = mode
            self._json(400, {"message": 'A lens named "amoe" is refused. Choose tazel, zero, or rosetta.', "refuse": code, "card": card})
            return
        if mode not in GRID:
            self._json(
                400,
                {
                    "message": "Unknown lens. Try tazel, zero, rosetta, or zen.",
                    "refuse": "AMOE-BAD-LENS",
                },
            )
            return
        if paint not in {"wheel", "engine"}:
            self._json(400, {"message": "Paint is wheel or engine.", "refuse": "AMOE-BAD-PAINT"})
            return
        try:
            with TemporaryDirectory(prefix="amoe-ui-") as tmp:
                src = Path(tmp) / "page.png"
                src.write_bytes(bytes(image))
                try:
                    rgb, digest = load_page(src)
                except ValueError:
                    self._json(400, {"message": "That file is not a PNG or JPEG.", "refuse": "AMOE-NOT-PICTURE"})
                    return
                out = Path(tmp) / "out"
                try:
                    card = process(
                        rgb,
                        src="page.png",
                        out_dir=out,
                        modes=[mode],
                        paint=paint,
                        lift=lift,
                        sha256_in=digest,
                        geom=not geom_off,
                        weight=True,
                    )
                except AmoeError as exc:
                    refused = invention_card(exc.code)
                    self._json(400, {"message": str(exc.code), "refuse": exc.code, "card": refused})
                    return
                cell = card["cells"][mode]
                png = (out / str(cell["path"])).read_bytes()
                self._finish_image(card, png, filename=str(cell["path"]))
        except ValueError as exc:
            self._json(400, {"message": str(exc), "refuse": "AMOE-NOT-PICTURE"})

    def _post_gallery(self) -> None:
        raw = self._read_body()
        if raw is None:
            return
        fields = _parse_fields(raw, self.headers.get("Content-Type") or "")
        image = fields.get("file")
        if not isinstance(image, (bytes, bytearray)) or not image:
            self._json(400, {"message": "Choose a PNG or JPEG page.", "refuse": "AMOE-NO-PAGE"})
            return
        with TemporaryDirectory(prefix="amoe-ui-") as tmp:
            src = Path(tmp) / "page.png"
            src.write_bytes(bytes(image))
            try:
                rgb, _digest = load_page(src)
            except ValueError:
                self._json(400, {"message": "That file is not a PNG or JPEG.", "refuse": "AMOE-NOT-PICTURE"})
                return
            out = Path(tmp) / "gallery.png"
            card = save_gallery(rgb, out)
            png = out.read_bytes()
            self._finish_image(card, png, filename="gallery.png")

    def _finish_image(self, card: dict, png: bytes, *, filename: str) -> None:
        if _wants_json(self.headers.get("Accept")):
            self._json(200, card)
            return
        inband = card.get("inband") if isinstance(card.get("inband"), dict) else {}
        refuse = card.get("refuse")
        if isinstance(refuse, list):
            refuse_text = ",".join(str(item) for item in refuse if item)
        else:
            refuse_text = str(refuse or "")
        self._send(
            200,
            png,
            "image/png",
            {
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Amoe-Mode": str(card.get("paint") or card.get("pass") or ""),
                "X-Amoe-Paint": str(card.get("paint") or card.get("pass") or ""),
                "X-Amoe-File": filename,
                "X-Amoe-Refuse": refuse_text,
                "X-Amoe-Tazel-Inband": str((inband or {}).get("tazel_inband_pct", "")),
                "X-Amoe-Vyrn-Inband": str((inband or {}).get("vyrn_inband_pct", "")),
            },
        )


def _parse_fields(raw: bytes, content_type: str) -> dict[str, object]:
    fields: dict[str, object] = {}
    bound = b""
    for part in content_type.split(";"):
        piece = part.strip()
        if piece.lower().startswith("boundary="):
            bound = piece.split("=", 1)[1].strip().strip('"').encode("utf-8")
    if not bound:
        return {"file": raw}
    marker = b"--" + bound
    for chunk in raw.split(marker):
        chunk = chunk.strip(b"\r\n")
        if not chunk or chunk == b"--":
            continue
        if b"\r\n\r\n" not in chunk:
            continue
        head, body = chunk.split(b"\r\n\r\n", 1)
        if body.endswith(b"\r\n"):
            body = body[:-2]
        header = head.decode("utf-8", "replace")
        lower = header.lower()
        name = ""
        if 'name="' in lower:
            start = lower.find('name="') + 6
            end = lower.find('"', start)
            name = lower[start:end]
        if "filename=" in lower or name == "file":
            fields["file"] = body
            continue
        fields[name] = body.decode("utf-8", "replace").strip()
    return fields


def make_server(host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    if host not in LOOPBACK:
        raise ValueError("AMOE UI binds loopback only (127.0.0.1).")
    return ThreadingHTTPServer((host, port), Handler)


def serve(host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
    httpd = make_server(host, port)
    bound_host, bound_port = httpd.server_address[:2]
    shown = f"[{bound_host}]" if ":" in str(bound_host) else bound_host
    print(f"Open http://{shown}:{bound_port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
