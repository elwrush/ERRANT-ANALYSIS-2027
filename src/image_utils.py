"""Image helpers: strip transparency and encode opaque PNG data URIs."""
import base64
import io
from pathlib import Path

from PIL import Image


def _is_transparent(im: Image.Image) -> bool:
    if im.mode in ("RGBA", "LA"):
        return True
    return im.mode == "P" and "transparency" in im.info


def opaque_png_bytes(path: Path) -> bytes:
    """Return PNG bytes with all transparency composited onto an opaque white background.

    Any RGBA/LA/palette-with-transparency image is alpha-composited over white and
    converted to RGB; an already-opaque image is converted to RGB. The result always
    has no alpha channel.
    """
    path = Path(path)
    with Image.open(path) as im:
        if _is_transparent(im):
            rgba = im.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            opaque = Image.alpha_composite(background, rgba).convert("RGB")
        else:
            opaque = im.convert("RGB")
        buf = io.BytesIO()
        opaque.save(buf, format="PNG")
        return buf.getvalue()


def opaque_data_uri(path: Path) -> str:
    """Return a base64 data URI with all transparency removed.

    Raster images are composited onto white and re-encoded as opaque PNG. SVG is
    passed through unchanged (its alpha is removed at generation time by the chart
    code, not by raster compositing).
    """
    path = Path(path)
    if path.suffix.lower() == ".svg":
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/svg+xml;base64,{b64}"
    b64 = base64.b64encode(opaque_png_bytes(path)).decode("ascii")
    return f"data:image/png;base64,{b64}"
