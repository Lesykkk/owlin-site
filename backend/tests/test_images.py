import pytest

from owlin.modules.orders.images import detect_image

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 20
WEBP = b"RIFF" + b"\x10\x00\x00\x00" + b"WEBP" + b"VP8 " + b"\x00" * 8


@pytest.mark.parametrize(
    "data, expected",
    [
        (PNG, ("image/png", "png")),
        (JPEG, ("image/jpeg", "jpg")),
        (WEBP, ("image/webp", "webp")),
    ],
)
def test_images_are_recognised_by_their_first_bytes(data: bytes, expected: tuple[str, str]) -> None:
    assert detect_image(data) == expected


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\x89PNG",
        b"GIF89a" + b"\x00" * 20,
        b"<html><script>alert(1)</script></html>",
        b"%PDF-1.7",
        b"RIFF" + b"\x10\x00\x00\x00" + b"WAVE" + b"\x00" * 8,
        b"MZ" + b"\x00" * 30,
    ],
)
def test_everything_else_is_not_an_image(data: bytes) -> None:
    assert detect_image(data) is None
