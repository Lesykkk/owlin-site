"""Recognises an image by its first bytes, so a file's real type does not depend on what the client claims."""

# Content type and file extension for each kind of image we accept.
IMAGE_KINDS = {
    "png": ("image/png", "png"),
    "jpeg": ("image/jpeg", "jpg"),
    "webp": ("image/webp", "webp"),
}


def detect_image(data: bytes) -> tuple[str, str] | None:
    """(content type, extension) of a PNG, JPEG or WebP file, or None for anything else."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return IMAGE_KINDS["png"]
    if data.startswith(b"\xff\xd8\xff"):
        return IMAGE_KINDS["jpeg"]
    # WebP is a RIFF container: "RIFF", a 4-byte size, then "WEBP".
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return IMAGE_KINDS["webp"]
    return None
