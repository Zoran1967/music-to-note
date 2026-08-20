# -*- coding: utf-8 -*-
"""
transcription/simple_pdf.py

Minimal pure-Python PDF writer -- ZERO third-party dependencies.

WHY THIS EXISTS: reportlab was tried first, but its optional C
accelerator module (_rl_accel) fails to compile against Python 3.11 on
the Android NDK toolchain ("incomplete definition of type 'struct
_frame'" -- the same class of problem this project already hit with
aubio/numpy, see transcription/pitch_detection.py). Rather than fight
a C extension we don't actually need, this module implements just the
handful of raw PDF primitives the app requires (lines, circles/
ellipses, text with the standard Helvetica fonts, multiple pages) by
writing PDF syntax directly. Standard, well-documented PDF structure --
nothing exotic.

Supports a small canvas-like API on purpose, so calling code
(transcription/notation_pdf.py) barely had to change when switching
away from reportlab.
"""

PAGE_A4 = (595.2755905511812, 841.8897637795277)  # points, 210x297mm


def _esc_text(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class Path:
    """Small helper mirroring reportlab's beginPath()/curveTo() API,
    used only for the hand-drawn treble clef's little tail curve."""

    def __init__(self):
        self.ops = []

    def moveTo(self, x, y):
        self.ops.append("{:.3f} {:.3f} m".format(x, y))

    def curveTo(self, x1, y1, x2, y2, x3, y3):
        self.ops.append(
            "{:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} c".format(
                x1, y1, x2, y2, x3, y3
            )
        )


class SimplePDFCanvas:
    """Subset of reportlab.pdfgen.canvas.Canvas's API, pure Python."""

    def __init__(self, path, pagesize=PAGE_A4):
        self._path = path
        self.page_w, self.page_h = pagesize
        self._pages = []       # finished page content strings
        self._ops = []         # current page's operators
        self._font_size = 12
        self._font_bold = False

    # -- state (kept simple: PDF q/Q around any style change) --------
    def saveState(self):
        self._ops.append("q")

    def restoreState(self):
        self._ops.append("Q")

    def setLineWidth(self, w):
        self._ops.append("{:.3f} w".format(w))

    def setFillColorRGB(self, r, g, b):
        self._ops.append("{:.3f} {:.3f} {:.3f} rg".format(r, g, b))

    def setFont(self, name, size):
        self._font_bold = "Bold" in name
        self._font_size = size

    # -- shapes --------------------------------------------------
    def line(self, x1, y1, x2, y2):
        self._ops.append(
            "{:.3f} {:.3f} m {:.3f} {:.3f} l S".format(x1, y1, x2, y2)
        )

    def circle(self, cx, cy, r, stroke=1, fill=0):
        self._ellipse_ops(cx - r, cy - r, cx + r, cy + r, stroke, fill)

    def ellipse(self, x1, y1, x2, y2, fill=0, stroke=1):
        self._ellipse_ops(x1, y1, x2, y2, stroke, fill)

    def _ellipse_ops(self, x1, y1, x2, y2, stroke, fill):
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        rx = abs(x2 - x1) / 2.0
        ry = abs(y2 - y1) / 2.0
        kx = 0.5522847498 * rx
        ky = 0.5522847498 * ry
        ops = [
            "{:.3f} {:.3f} m".format(cx + rx, cy),
            "{:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} c".format(
                cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry
            ),
            "{:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} c".format(
                cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy
            ),
            "{:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} c".format(
                cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry
            ),
            "{:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} c".format(
                cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy
            ),
        ]
        self._ops.append(" ".join(ops) + " " + self._paint_op(stroke, fill))

    def _paint_op(self, stroke, fill):
        if fill and stroke:
            return "B"
        if fill:
            return "f"
        return "S"

    def beginPath(self):
        return Path()

    def drawPath(self, path, stroke=1, fill=0):
        self._ops.append(" ".join(path.ops) + " " + self._paint_op(stroke, fill))

    # -- text --------------------------------------------------
    def drawString(self, x, y, text):
        font_ref = "F2" if self._font_bold else "F1"
        self._ops.append(
            "BT /{} {:.3f} Tf {:.3f} {:.3f} Td ({}) Tj ET".format(
                font_ref, self._font_size, x, y, _esc_text(text)
            )
        )

    def drawCentredString(self, x, y, text):
        # Rough width estimate (no font metrics available without a
        # library) -- good enough for the small debug labels this is
        # used for; not used for anything load-bearing.
        approx_width = 0.5 * self._font_size * len(text)
        self.drawString(x - approx_width / 2.0, y, text)

    # -- pages / output --------------------------------------------------
    def showPage(self):
        self._pages.append("\n".join(self._ops))
        self._ops = []

    def save(self):
        if self._ops:
            self.showPage()
        _write_pdf(self._path, self._pages, self.page_w, self.page_h)


def _write_pdf(path, pages, page_w, page_h):
    n_pages = max(1, len(pages))
    if not pages:
        pages = [""]

    catalog_num = 1
    pages_num = 2
    page_nums = [3 + i for i in range(n_pages)]
    content_nums = [3 + n_pages + i for i in range(n_pages)]
    font_regular_num = 3 + 2 * n_pages
    font_bold_num = font_regular_num + 1
    total_objs = font_bold_num

    buf = bytearray()
    offsets = {}

    def write_obj(num, body_bytes):
        offsets[num] = len(buf)
        buf.extend("{} 0 obj\n".format(num).encode("latin-1"))
        buf.extend(body_bytes)
        buf.extend(b"\nendobj\n")

    buf.extend(b"%PDF-1.4\n")

    write_obj(
        catalog_num,
        "<< /Type /Catalog /Pages {} 0 R >>".format(pages_num).encode("latin-1"),
    )

    kids = " ".join("{} 0 R".format(n) for n in page_nums)
    write_obj(
        pages_num,
        "<< /Type /Pages /Kids [{}] /Count {} >>".format(kids, n_pages).encode(
            "latin-1"
        ),
    )

    for i, pnum in enumerate(page_nums):
        cnum = content_nums[i]
        body = (
            "<< /Type /Page /Parent {pages} 0 R "
            "/MediaBox [0 0 {w:.3f} {h:.3f}] "
            "/Resources << /Font << /F1 {freg} 0 R /F2 {fbold} 0 R >> >> "
            "/Contents {cnum} 0 R >>"
        ).format(
            pages=pages_num, w=page_w, h=page_h,
            freg=font_regular_num, fbold=font_bold_num, cnum=cnum,
        ).encode("latin-1")
        write_obj(pnum, body)

    for i, cnum in enumerate(content_nums):
        stream_data = pages[i].encode("latin-1")
        body = (
            "<< /Length {} >>\nstream\n".format(len(stream_data)).encode("latin-1")
            + stream_data
            + b"\nendstream"
        )
        write_obj(cnum, body)

    write_obj(
        font_regular_num,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    )
    write_obj(
        font_bold_num,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    )

    xref_start = len(buf)
    buf.extend("xref\n0 {}\n".format(total_objs + 1).encode("latin-1"))
    buf.extend(b"0000000000 65535 f \n")
    for n in range(1, total_objs + 1):
        buf.extend("{:010d} 00000 n \n".format(offsets[n]).encode("latin-1"))

    buf.extend(
        (
            "trailer\n<< /Size {} /Root {} 0 R >>\nstartxref\n{}\n%%EOF"
        ).format(total_objs + 1, catalog_num, xref_start).encode("latin-1")
    )

    with open(path, "wb") as f:
        f.write(buf)
