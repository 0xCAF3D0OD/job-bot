"""Images génériques refusées comme logo (docs/14 §4) : une règle par test, sans base."""

import io
import re

import pytest
from PIL import Image, ImageDraw

from jobbot.logos import generic


def png(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


def logo(size: int = 64) -> bytes:
    """Un vrai logo : un disque bleu et un trait rouge sur fond blanc."""
    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, size - 8, size - 8), fill=(30, 80, 200))
    draw.line((0, size // 2, size, size // 2), fill=(200, 30, 30), width=4)
    return png(image)


def test_a_real_logo_is_accepted() -> None:
    assert generic.refusal(logo(), "image/png", others=0) is None


def test_banned_fingerprint_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    data = logo()
    monkeypatch.setattr(generic, "BANNED", frozenset({generic.sha256(data)}))
    assert generic.refusal(data, "image/png", others=0) == "image générique connue"


def test_banned_list_holds_sha256_fingerprints() -> None:
    for fingerprint in generic.BANNED:
        assert re.fullmatch(r"[0-9a-f]{64}", fingerprint), fingerprint


def test_image_shared_by_two_other_companies_is_refused() -> None:
    assert generic.refusal(logo(), "image/png", others=1) is None
    assert generic.refusal(logo(), "image/png", others=2) == "image commune à plusieurs entreprises"


def test_image_smaller_than_24_px_is_refused() -> None:
    assert generic.blank_reason(logo(23), "image/png") == "image trop petite"
    assert generic.blank_reason(logo(24), "image/png") is None
    wide = png(Image.new("RGB", (200, 20), "navy"))
    assert generic.blank_reason(wide, "image/png") == "image trop petite"


def test_almost_transparent_image_is_refused() -> None:
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((0, 0, 9, 9), fill=(0, 0, 0, 255))  # 1 % visible
    assert generic.blank_reason(png(image), "image/png") == "image presque transparente"
    empty = png(Image.new("RGBA", (64, 64), (255, 255, 255, 0)))
    assert generic.blank_reason(empty, "image/png") == "image presque transparente"


def test_flat_single_color_is_refused() -> None:
    flat = png(Image.new("RGB", (64, 64), (240, 240, 240)))
    assert generic.blank_reason(flat, "image/png") == "une seule couleur"
    # Bruit de compression : toujours une seule couleur.
    out = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 200, 200)).save(out, "JPEG", quality=60)
    assert generic.blank_reason(out.getvalue(), "image/jpeg") == "une seule couleur"
    # Un aplat entouré d'une marge transparente aussi.
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((2, 2, 97, 97), fill=(255, 255, 255, 255))
    assert generic.blank_reason(png(image), "image/png") == "une seule couleur"


def test_single_color_logo_on_transparent_background_is_kept() -> None:
    """Un sigle noir sur fond transparent est un vrai logo : sa forme fait le dessin."""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(image).text((4, 20), "ACME", fill=(0, 0, 0, 255), font_size=20)
    assert generic.blank_reason(png(image), "image/png") is None


def test_other_raster_formats_are_checked() -> None:
    out = io.BytesIO()
    Image.new("RGB", (16, 16), "red").save(out, "ICO", sizes=[(16, 16)])
    assert generic.blank_reason(out.getvalue(), "image/x-icon") == "image trop petite"
    out = io.BytesIO()
    Image.open(io.BytesIO(logo())).save(out, "GIF")
    assert generic.blank_reason(out.getvalue(), "image/gif") is None


def test_unreadable_image_is_refused() -> None:
    assert generic.blank_reason(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50, "image/png") == (
        "image illisible"
    )


def test_svg_only_checks_its_declared_size() -> None:
    def svg(attributes: str) -> bytes:
        return f'<svg xmlns="http://www.w3.org/2000/svg" {attributes}><rect/></svg>'.encode()

    assert generic.blank_reason(svg('width="16" height="16"'), "image/svg+xml") == (
        "image trop petite"
    )
    assert generic.blank_reason(svg('width="20px" height="120"'), "image/svg+xml") == (
        "image trop petite"
    )
    assert generic.blank_reason(svg('width="120" height="40"'), "image/svg+xml") is None
    assert generic.blank_reason(svg('viewBox="0 0 16 16"'), "image/svg+xml") is None
    assert generic.blank_reason(svg('width="100%" height="100%"'), "image/svg+xml") is None


def test_logos_command_needs_an_action(capsys: pytest.CaptureFixture[str]) -> None:
    from jobbot.__main__ import main

    assert main(["logos"]) == 1
    assert "--clean-generic" in capsys.readouterr().err
