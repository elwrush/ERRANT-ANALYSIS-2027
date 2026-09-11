import base64
import io
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def _decode(data_uri):
    assert data_uri.startswith("data:image/png;base64,")
    raw = base64.b64decode(data_uri.split(",", 1)[1])
    return Image.open(io.BytesIO(raw))


class TestOpaquePngBytes:
    def test_rgba_composited_over_white(self, tmp_path):
        from image_utils import opaque_png_bytes

        img = Image.new("RGBA", (2, 2), (255, 0, 0, 0))
        img.putpixel((0, 0), (0, 0, 255, 255))
        p = tmp_path / "rgba.png"
        img.save(p)

        out = Image.open(io.BytesIO(opaque_png_bytes(p)))
        assert out.mode == "RGB"
        assert out.getpixel((0, 0)) == (0, 0, 255)
        assert out.getpixel((1, 1)) == (255, 255, 255)

    def test_la_composited_over_white(self, tmp_path):
        from image_utils import opaque_png_bytes

        img = Image.new("LA", (2, 1), (0, 0))
        img.putpixel((0, 0), (128, 255))
        p = tmp_path / "la.png"
        img.save(p)

        out = Image.open(io.BytesIO(opaque_png_bytes(p)))
        assert out.mode == "RGB"
        assert out.getpixel((0, 0)) == (128, 128, 128)
        assert out.getpixel((1, 0)) == (255, 255, 255)

    def test_palette_with_transparency(self, tmp_path):
        from image_utils import opaque_png_bytes

        img = Image.new("P", (2, 1))
        img.putpalette([0, 0, 0, 255, 255, 255] + [0] * (768 - 6))
        img.putpixel((0, 0), 0)
        img.putpixel((1, 0), 1)
        p = tmp_path / "pal.png"
        img.save(p, transparency=0)

        out = Image.open(io.BytesIO(opaque_png_bytes(p)))
        assert out.mode == "RGB"
        assert out.getpixel((0, 0)) == (255, 255, 255)

    def test_rgb_passthrough(self, tmp_path):
        from image_utils import opaque_png_bytes

        img = Image.new("RGB", (2, 2), (10, 20, 30))
        p = tmp_path / "rgb.png"
        img.save(p)

        out = Image.open(io.BytesIO(opaque_png_bytes(p)))
        assert out.mode == "RGB"
        assert out.getpixel((0, 0)) == (10, 20, 30)

    def test_missing_file_raises(self, tmp_path):
        from image_utils import opaque_png_bytes

        with pytest.raises(FileNotFoundError):
            opaque_png_bytes(tmp_path / "nope.png")


class TestOpaqueDataUri:
    def test_data_uri_is_opaque_rgb(self, tmp_path):
        from image_utils import opaque_data_uri

        img = Image.new("RGBA", (2, 2), (255, 0, 0, 0))
        p = tmp_path / "rgba.png"
        img.save(p)

        out = _decode(opaque_data_uri(p))
        assert out.mode == "RGB"
        assert out.getpixel((0, 0)) == (255, 255, 255)

    def test_svg_passthrough(self, tmp_path):
        from image_utils import opaque_data_uri

        svg = tmp_path / "chart.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")

        uri = opaque_data_uri(svg)
        assert uri.startswith("data:image/svg+xml;base64,")
        decoded = base64.b64decode(uri.split(",", 1)[1]).decode("utf-8")
        assert decoded.startswith("<svg")
