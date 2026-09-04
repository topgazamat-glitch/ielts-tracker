"""Multipart form parsing and image sniffing - standard library only.

`cgi.FieldStorage` is deprecated and gone in newer Pythons, so the small amount
of parsing this app needs is done here instead.
"""
import os
import re
import struct

MAX_BYTES = 50 * 1024 * 1024   # whole request; Telegram will not send more
MAX_FILES = 12


def parse_multipart(body, content_type):
    """Returns (fields, files) where files is a list of (filename, bytes)."""
    m = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type or "")
    if not m:
        return {}, []
    boundary = (m.group(1) or m.group(2)).strip().encode()
    fields, files = {}, []
    for part in body.split(b"--" + boundary):
        if not part or part in (b"--\r\n", b"--"):
            continue
        head, sep, data = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        data = data[:-2] if data.endswith(b"\r\n") else data
        disp = ""
        for line in head.split(b"\r\n"):
            if line.lower().startswith(b"content-disposition:"):
                disp = line.decode("utf-8", "replace")
        name = re.search(r'name="([^"]*)"', disp)
        filename = re.search(r'filename="([^"]*)"', disp)
        if filename:
            if filename.group(1) and data:
                files.append((filename.group(1), data))
        elif name:
            fields.setdefault(name.group(1), []).append(data.decode("utf-8", "replace"))
    return fields, files


def image_size(data):
    """(width, height, kind) for JPEG and PNG; (None, None, None) otherwise."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return w, h, "png"
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            # SOF0..SOF15, excluding the DHT/DAC/DRI markers in that range
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h, "jpeg"
            i += 2 + length
    return None, None, None


EXT_TYPES = {
    ".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
    ".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".ogg": "audio/ogg",
    ".oga": "audio/ogg", ".wav": "audio/wav", ".mp4": "video/mp4",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain", ".zip": "application/zip",
}


def content_type(name):
    ext = os.path.splitext(name or "")[1].lower()
    return EXT_TYPES.get(ext, "application/octet-stream")


def safe_ext(name):
    """Keep the extension so the file opens correctly; discard everything else."""
    ext = os.path.splitext(name or "")[1].lower()
    return ext if ext in EXT_TYPES else ""
