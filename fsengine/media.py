"""Layer 6a: images, video, audio. Stdlib-only header parsing (EXIF, MP4 atoms, ID3, FLAC, WAV)."""
from __future__ import annotations

import os
import re
import struct

from .model import Verdict

# ---------------------------------------------------------------- images
SCREEN_RES = {(1920, 1080), (2560, 1440), (3840, 2160), (1366, 768), (1536, 864), (1440, 900), (1280, 720), (1600, 900),
              (2560, 1600), (1680, 1050), (3440, 1440), (2880, 1800), (1280, 800), (1024, 768), (1280, 1024), (1920, 1200),
              (1080, 2400), (1080, 1920), (1170, 2532), (1284, 2778), (1080, 2340), (1440, 3200), (750, 1334), (828, 1792),
              (1179, 2556), (1290, 2796), (720, 1600), (1080, 2408), (1440, 2560)}
NAME_SCREENSHOT = re.compile(r"screen\s?shot|screen[ _-]?cap|snip|screenshot|^capture|^shot[ _-]|^Снимок|screengrab|^Bildschirmfoto|^Captura", re.I)
NAME_CHAT_IMG = re.compile(r"^(IMG|VID|PTT|AUD|STK)-\d{8}-WA\d+|^FB_IMG_|^received_\d+|^Snapchat-|^photo_\d+@\d{2}-\d{2}-\d{4}|^telegram-cloud|"
                           r"^signal-\d{4}-|^image_\d{10,}|^(Instagram|insta|IMG)_?\d{10,}|^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}\.(jpe?g|png|webp)$", re.I)
NAME_CAMERA = re.compile(r"^(IMG|DSC|DSCN|DSCF|P|PXL|MVI|GOPR|GX|DJI)[_-]?\d{4,}|^\d{8}[_-]\d{6}|^(PHOTO|Photo)[-_ ]\d{4}|^IMG_E?\d{4}", re.I)
NAME_WALLPAPER = re.compile(r"wallpaper|wallhaven|background|backdrop|desktop[ _-]?bg|lockscreen|4k|8k|hd[ _-]?wall", re.I)
NAME_MEME = re.compile(r"meme|funny|lol|reaction|sticker|emoji|gif[_ -]?pack|template", re.I)


def png_dims(h: bytes):
    return struct.unpack(">II", h[16:24]) if len(h) >= 24 and h[12:16] == b"IHDR" else None


def gif_dims(h: bytes):
    return struct.unpack("<HH", h[6:10]) if len(h) >= 10 else None


def bmp_dims(h: bytes):
    return (struct.unpack("<i", h[18:22])[0], abs(struct.unpack("<i", h[22:26])[0])) if len(h) >= 26 else None


def webp_info(h: bytes):
    animated, dims = False, None
    if h[12:16] == b"VP8X" and len(h) >= 30:
        animated = bool(h[20] & 0x02)
        dims = (1 + int.from_bytes(h[24:27], "little"), 1 + int.from_bytes(h[27:30], "little"))
    elif h[12:16] == b"VP8L" and len(h) >= 25:
        b = h[21:25]
        dims = (1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6)))
    elif h[12:16] == b"VP8 " and len(h) >= 30:
        dims = (struct.unpack("<H", h[26:28])[0] & 0x3FFF, struct.unpack("<H", h[28:30])[0] & 0x3FFF)
    return dims, animated


def ico_dims(h: bytes):
    return ((h[6] or 256), (h[7] or 256)) if len(h) >= 8 else None


def jpeg_info(path: str):
    """-> (dims, exif dict) by walking JPEG segments."""
    dims, exif = None, {}
    try:
        with open(path, "rb") as f:
            if f.read(2) != b"\xff\xd8":
                return None, exif
            for _ in range(60):
                b = f.read(1)
                while b and b != b"\xff":
                    b = f.read(1)
                while b == b"\xff":
                    b = f.read(1)
                if not b:
                    break
                m = b[0]
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                    continue
                if m == 0xD9 or m == 0xDA:
                    break
                ln = struct.unpack(">H", f.read(2))[0]
                if m == 0xE1 and not exif:
                    seg = f.read(min(ln - 2, 65535))
                    if seg.startswith(b"Exif\x00\x00"):
                        exif = _parse_exif(seg[6:])
                    continue
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    s = f.read(5)
                    dims = (struct.unpack(">H", s[3:5])[0], struct.unpack(">H", s[1:3])[0])
                    if exif or True:
                        break
                f.seek(ln - 2, 1)
    except (OSError, struct.error):
        pass
    return dims, exif


def _parse_exif(t: bytes) -> dict:
    out = {}
    try:
        bo = "<" if t[:2] == b"II" else ">"
        ifd0 = struct.unpack(bo + "I", t[4:8])[0]

        def read_ifd(off):
            n = struct.unpack(bo + "H", t[off:off + 2])[0]
            for i in range(min(n, 80)):
                e = t[off + 2 + i * 12: off + 14 + i * 12]
                tag, typ, cnt, val = struct.unpack(bo + "HHII", e)
                if typ == 2:
                    raw = e[8:12] if cnt <= 4 else t[val:val + cnt]
                    out[tag] = raw.split(b"\x00")[0].decode("latin-1", "replace").strip()
                elif typ in (3, 4):
                    out[tag] = val if typ == 4 else struct.unpack(bo + "H", e[8:10])[0]

        read_ifd(ifd0)
        if 0x8769 in out and isinstance(out[0x8769], int):
            read_ifd(out[0x8769])
    except (struct.error, IndexError):
        pass
    return {"make": out.get(0x010F, ""), "model": out.get(0x0110, ""), "software": out.get(0x0131, ""),
            "taken": out.get(0x9003, "")}


def classify_image(path: str, name: str, sn, size: int, ext: str) -> Verdict:
    h, kind = sn.head, sn.kind
    ev = [f"file signature: {kind}"]
    dims, exif, animated = None, {}, False
    if kind == "png":
        dims = png_dims(h)
    elif kind == "jpeg":
        dims, exif = jpeg_info(path)
    elif kind == "gif":
        dims, animated = gif_dims(h), True
    elif kind == "webp":
        dims, animated = webp_info(h)
    elif kind == "bmp":
        dims = bmp_dims(h)
    elif kind == "ico":
        dims = ico_dims(h)
    if dims:
        ev.append(f"{dims[0]}x{dims[1]} px")
    base = ("Images",)
    # Minecraft skin
    if dims in ((64, 64), (64, 32), (128, 128)) and re.search(r"skin|steve|alex|minecraft", name, re.I) and kind == "png":
        return Verdict(("Games", "Minecraft", "Skins & Textures"), "Minecraft skin", 0.85, ev + ["64x64 PNG named like a skin"])
    if kind == "ico":
        return Verdict(("Images", "Icons"), "Icon", 0.93, ev)
    if exif.get("make") or exif.get("model") or exif.get("taken"):
        cam = " ".join(x for x in (exif.get("make"), exif.get("model")) if x)
        ev.append("EXIF camera data" + (f": {cam}" if cam else ""))
        return Verdict(("Images", "Photos"), f"Camera photo ({cam})" if cam else "Camera photo", 0.95, ev)
    if NAME_SCREENSHOT.search(name):
        return Verdict(("Images", "Screenshots"), "Screenshot", 0.92, ev + ["name looks like a screenshot"])
    if NAME_CHAT_IMG.search(name):
        return Verdict(("Images", "Social & Chat"), "Chat/social-media image", 0.88, ev + ["name matches WhatsApp/Telegram/Facebook pattern"])
    if kind == "webp" and dims and max(dims) <= 512 and (animated or re.search(r"stick", name, re.I)):
        return Verdict(("Images", "Stickers & GIFs"), "Sticker", 0.8, ev)
    if animated and kind in ("gif", "webp"):
        return Verdict(("Images", "Stickers & GIFs"), "Animated image", 0.85 if kind == "gif" else 0.75, ev + ["animated"])
    if NAME_MEME.search(name):
        return Verdict(("Images", "Stickers & GIFs"), "Meme / sticker", 0.65, ev + ["name looks like meme/sticker"])
    if dims and dims in SCREEN_RES and kind == "png" and not NAME_WALLPAPER.search(name):
        return Verdict(("Images", "Screenshots"), "Screenshot (screen-sized PNG)", 0.72, ev + ["exact screen resolution, PNG, no camera data"])
    if NAME_WALLPAPER.search(name) or (dims and min(dims) >= 1080 and max(dims) >= 1920 and kind in ("jpeg", "png", "webp")
                                       and not NAME_CAMERA.search(name)):
        conf = 0.8 if NAME_WALLPAPER.search(name) else 0.6
        return Verdict(("Images", "Wallpapers & Art"), "Wallpaper / artwork", conf,
                       ev + (["name says wallpaper"] if conf > 0.7 else ["large, no camera data"]))
    if dims and max(dims) <= 256 and kind in ("png", "webp", "bmp"):
        return Verdict(("Images", "Icons"), "Small graphic / icon", 0.7, ev + ["tiny image"])
    if NAME_CAMERA.search(name):
        return Verdict(("Images", "Photos"), "Camera-style photo (by file name)", 0.75, ev + ["camera naming pattern"])
    return Verdict(base, "Image", 0.88, ev)


# ---------------------------------------------------------------- video
NAME_SCREENREC = re.compile(r"screen\s?(recording|record|capture|cast)|screenrecord|screen[_-]recorder|^obs\b|^replay|bandicam|shadowplay|"
                            r"^Desktop \d{4}\.\d{2}\.\d{2}|^\d{4}-\d{2}-\d{2}[ _]\d{2}-\d{2}-\d{2}|gamebar|^Recording[ _]\d|loom|^Capture[ _]\d|xbox", re.I)
NAME_CHAT_VID = re.compile(r"^VID-\d{8}-WA|^video-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}|^Snapchat-|^FB_VID|^received_|^(ss)?tik[ _-]?tok|snaptik|ssstik|^Instagram|^insta|^reel", re.I)
NAME_CAMERA_VID = re.compile(r"^(VID|MOV|PXL|MVI|GOPR|GX\d|DJI|GH\d|MAH|C\d{4})[_-]?\d{3,}|^\d{8}_\d{6}|^IMG_\d{4}\.|^DSC_?\d{4}", re.I)
NAME_SHOW = re.compile(r"\bS\d{1,2}[ ._-]?E\d{1,3}\b|\bseason[ ._]?\d+|\b\d{1,2}x\d{2}\b|^\[[^\]]{2,30}\][^\[]*[ ._-]+\d{2,3}\b(?!\d)", re.I)
NAME_RELEASE = re.compile(r"\b(480p|576p|720p|1080p|2160p|4k|bluray|blu-ray|brrip|bdrip|web-?dl|web-?rip|hdrip|dvdrip|hdtv|x26[45]|hevc|xvid|h\.?26[45]|"
                          r"yify|yts|rarbg|ettv|amzn|nf|hdcam|remux)\b", re.I)
NAME_COURSE = re.compile(r"lecture|tutorial|course|lesson|class[ _-]?\d|module[ _-]?\d|udemy|coursera|masterclass|bootcamp|walkthrough|how[ _-]to|chapter[ _-]?\d", re.I)


def _boxes(buf: bytes, start=0, end=None):
    end = len(buf) if end is None else end
    p = start
    while p + 8 <= end:
        size, typ = struct.unpack(">I4s", buf[p:p + 8])
        hdr = 8
        if size == 1 and p + 16 <= end:
            size = struct.unpack(">Q", buf[p + 8:p + 16])[0]; hdr = 16
        elif size == 0:
            size = end - p
        if size < hdr:
            break
        yield typ, p + hdr, min(p + size, end)
        p += size


def mp4_info(path: str) -> dict:
    """duration (s), width, height from moov, without reading mdat."""
    info = {}
    try:
        with open(path, "rb") as f:
            fsize = os.fstat(f.fileno()).st_size
            pos = 0
            while pos + 8 <= fsize:
                f.seek(pos)
                hdr = f.read(16)
                size, typ = struct.unpack(">I4s", hdr[:8])
                hl = 8
                if size == 1:
                    size = struct.unpack(">Q", hdr[8:16])[0]; hl = 16
                elif size == 0:
                    size = fsize - pos
                if size < hl:
                    break
                if typ == b"moov" and size < 64 * 1024 * 1024:
                    f.seek(pos + hl)
                    moov = f.read(size - hl)
                    _parse_moov(moov, info)
                    break
                pos += size
    except (OSError, struct.error):
        pass
    return info


def _parse_moov(moov: bytes, info: dict):
    for typ, s, e in _boxes(moov):
        if typ == b"mvhd":
            v = moov[s]
            if v == 1:
                ts, dur = struct.unpack(">IQ", moov[s + 20:s + 32])
            else:
                ts, dur = struct.unpack(">II", moov[s + 12:s + 20])
            if ts:
                info["duration"] = dur / ts
        elif typ == b"trak":
            for t2, s2, e2 in _boxes(moov, s, e):
                if t2 == b"tkhd":
                    v = moov[s2]
                    off = s2 + (88 if v == 1 else 76)
                    mo = s2 + (52 if v == 1 else 40)
                    try:
                        w, h = struct.unpack(">II", moov[off:off + 8])
                        a, b_ = struct.unpack(">ii", moov[mo:mo + 8])
                    except struct.error:
                        continue
                    w, h = w >> 16, h >> 16
                    if w and h and "width" not in info:
                        if a == 0 and abs(b_) == 0x10000:   # rotated 90/270
                            w, h = h, w
                        info["width"], info["height"] = w, h


def avi_info(h: bytes) -> dict:
    try:
        us, frames = struct.unpack("<I", h[32:36])[0], struct.unpack("<I", h[48:52])[0]
        w, hh = struct.unpack("<II", h[64:72])
        return {"width": w, "height": hh, "duration": us * frames / 1e6 if us else 0}
    except struct.error:
        return {}


def classify_video(path: str, name: str, sn, size: int, ext: str) -> Verdict:
    ev = [f"file signature: {sn.kind}"]
    info = mp4_info(path) if sn.kind in ("mp4", "mov", "3gp") else avi_info(sn.head) if sn.kind == "avi" else {}
    dur, w, h = info.get("duration"), info.get("width"), info.get("height")
    if w and h:
        ev.append(f"{w}x{h}")
    if dur:
        ev.append(f"{int(dur // 60)}m{int(dur % 60):02d}s long")
    if NAME_SHOW.search(name):
        return Verdict(("Videos", "TV Shows & Anime"), "TV episode", 0.9, ev + ["episode pattern in name (S01E02 / fansub style)"])
    if NAME_RELEASE.search(name):
        sub = "Movies"
        return Verdict(("Videos", sub), "Movie", 0.85, ev + ["release tags in name (1080p/WEB-DL/x264...)"])
    if NAME_CHAT_VID.search(name):
        return Verdict(("Videos", "Social & Chat"), "Chat/social-media video", 0.88, ev + ["WhatsApp/Telegram/TikTok/Instagram naming"])
    if NAME_SCREENREC.search(name):
        return Verdict(("Videos", "Screen Recordings"), "Screen recording", 0.85, ev + ["recorder naming pattern"])
    if NAME_CAMERA_VID.search(name):
        return Verdict(("Videos", "Camera Clips"), "Camera clip", 0.85, ev + ["camera naming pattern"])
    if NAME_COURSE.search(name):
        return Verdict(("Videos", "Courses & Lectures"), "Course / tutorial video", 0.75, ev + ["lecture/tutorial words in name"])
    if w and h and h > w * 1.2 and dur and dur <= 180:
        return Verdict(("Videos", "Shorts & Vertical"), "Vertical short video", 0.72, ev + ["portrait orientation, under 3 min"])
    if w and h and (w, h) in SCREEN_RES and dur and dur < 3 * 3600 and sn.kind in ("mkv", "mp4") and not NAME_RELEASE.search(name) \
            and re.search(r"\d{4}-\d{2}-\d{2}|\d{8}", name):
        return Verdict(("Videos", "Screen Recordings"), "Screen recording (screen-sized, dated name)", 0.62, ev)
    if dur and dur >= 40 * 60 and size > 400 * 1024 * 1024:
        return Verdict(("Videos", "Movies"), "Long feature-length video", 0.62, ev + ["over 40 min and large"])
    return Verdict(("Videos",), "Video", 0.88, ev)


# ---------------------------------------------------------------- audio
NAME_VOICE = re.compile(r"^(PTT|AUD)-\d{8}-WA|voice[ _-]?(note|memo|message|\d)|new recording|^recording[ _-]?\d|call[ _-]?recording|^record[ _-]?\d|"
                        r"^\d{8}[_-]\d{6}\.(m4a|amr|3ga|aac|opus|wav)$|whatsapp audio|^sound[ _-]?recording|^\d{4}-\d{2}-\d{2}[ _]\d{2}[.-]\d{2}[.-]\d{2}\.(m4a|wav)", re.I)
NAME_PODCAST = re.compile(r"podcast|audiobook|audio[ _-]?book|\bepisode\b|\bep\.?\s?\d+|unabridged|narrated|\bchapter[ _-]?\d+", re.I)
NAME_SFX = re.compile(r"sfx|sound[ _-]?effect|\bsample|\bloop\b|\bkick\b|snare|hi-?hat|\b808\b|riser|foley|\bstem\b|\bone[ _-]?shot|whoosh|impact|ambience|ambient[ _-]?loop", re.I)
NAME_ARTIST_TITLE = re.compile(r"^(\d{1,3}[ ._-]+)?[^-–—_]{2,45}\s[-–—]\s[^-–—]{2,70}\.\w{2,4}$")
_MP3_BR1 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
_MP3_BR2 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]


def _synchsafe(b: bytes) -> int:
    return (b[0] << 21) | (b[1] << 14) | (b[2] << 7) | b[3]


def _id3_text(d: bytes) -> str:
    if not d:
        return ""
    enc, body = d[0], d[1:]
    try:
        s = body.decode({0: "latin-1", 1: "utf-16", 2: "utf-16-be", 3: "utf-8"}.get(enc, "latin-1"), "replace")
    except Exception:
        s = body.decode("latin-1", "replace")
    return s.strip("\x00 \ufeff\r\n")


def id3_tags(path: str, size: int) -> tuple[dict, int]:
    tags: dict = {}
    id3len = 0
    try:
        with open(path, "rb") as f:
            hdr = f.read(10)
            if len(hdr) == 10 and hdr[:3] == b"ID3":
                ver = hdr[3]
                id3len = _synchsafe(hdr[6:10]) + 10
                data = f.read(min(id3len - 10, 262144))
                p = 0
                idsz, hsz = (3, 6) if ver == 2 else (4, 10)
                names = {"TIT2": "title", "TPE1": "artist", "TALB": "album", "TCON": "genre", "TT2": "title", "TP1": "artist",
                         "TAL": "album", "TCO": "genre", "TRCK": "track", "TRK": "track"}
                while p + hsz <= len(data):
                    fid = data[p:p + idsz].decode("latin-1")
                    if not fid.strip("\x00"):
                        break
                    if ver == 2:
                        fsz = int.from_bytes(data[p + 3:p + 6], "big")
                    elif ver == 4:
                        fsz = _synchsafe(data[p + 4:p + 8])
                    else:
                        fsz = struct.unpack(">I", data[p + 4:p + 8])[0]
                    if fsz <= 0 or p + hsz + fsz > len(data):
                        break
                    if fid in names:
                        tags[names[fid]] = _id3_text(data[p + hsz:p + hsz + fsz])
                    p += hsz + fsz
            if size > 128:
                f.seek(-128, 2)
                t = f.read(128)
                if t[:3] == b"TAG":
                    def g(a, b):
                        return t[a:b].split(b"\x00")[0].decode("latin-1", "replace").strip()
                    tags.setdefault("title", g(3, 33)); tags.setdefault("artist", g(33, 63)); tags.setdefault("album", g(63, 93))
    except OSError:
        pass
    return {k: v for k, v in tags.items() if v}, id3len


def mp3_duration(path: str, size: int, id3len: int) -> float | None:
    try:
        with open(path, "rb") as f:
            f.seek(id3len)
            b = f.read(4096)
        for i in range(len(b) - 4):
            if b[i] == 0xFF and (b[i + 1] & 0xE0) == 0xE0:
                ver = (b[i + 1] >> 3) & 3
                layer = (b[i + 1] >> 1) & 3
                bi = b[i + 2] >> 4
                if ver == 1 or layer != 1 or bi in (0, 15):
                    continue
                kbps = (_MP3_BR1 if ver == 3 else _MP3_BR2)[bi]
                return (size - id3len) * 8 / (kbps * 1000)
    except OSError:
        pass
    return None


def flac_info(path: str) -> tuple[dict, float | None]:
    tags, dur = {}, None
    try:
        with open(path, "rb") as f:
            if f.read(4) != b"fLaC":
                return tags, dur
            while True:
                h = f.read(4)
                if len(h) < 4:
                    break
                last, typ, ln = h[0] & 0x80, h[0] & 0x7F, int.from_bytes(h[1:4], "big")
                data = f.read(ln) if ln < 2_000_000 else b""
                if typ == 0 and len(data) >= 18:
                    v = int.from_bytes(data[10:18], "big")
                    rate, total = (v >> 44) & 0xFFFFF, v & 0xFFFFFFFFF
                    if rate:
                        dur = total / rate
                elif typ == 4 and data:
                    p = 4 + struct.unpack("<I", data[:4])[0]
                    n = struct.unpack("<I", data[p:p + 4])[0]; p += 4
                    for _ in range(min(n, 200)):
                        l = struct.unpack("<I", data[p:p + 4])[0]; p += 4
                        k, _, val = data[p:p + l].decode("utf-8", "replace").partition("=")
                        tags[k.lower()] = val; p += l
                if last:
                    break
    except (OSError, struct.error):
        pass
    return {k: v for k, v in tags.items() if k in ("title", "artist", "album", "genre")}, dur


def m4a_tags(path: str) -> dict:
    tags = {}
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            blob = f.read(1_500_000)
            if size > 3_000_000:
                f.seek(-1_500_000, 2); blob += f.read()
        for key, nm in ((b"\xa9nam", "title"), (b"\xa9ART", "artist"), (b"\xa9alb", "album"), (b"\xa9gen", "genre")):
            i = blob.find(key + b"\x00")  # not used; atoms have size before tag
            i = blob.find(key)
            if i > 3:
                j = blob.find(b"data", i, i + 24)
                if j > 0:
                    dsz = struct.unpack(">I", blob[j - 4:j])[0]
                    tags[nm] = blob[j + 12:j - 4 + dsz].decode("utf-8", "replace").strip()
    except (OSError, struct.error):
        pass
    return {k: v for k, v in tags.items() if v}


def wav_duration(h: bytes, size: int) -> float | None:
    try:
        p, br = 12, 0
        while p + 8 <= len(h):
            cid, cl = h[p:p + 4], struct.unpack("<I", h[p + 4:p + 8])[0]
            if cid == b"fmt ":
                br = struct.unpack("<I", h[p + 16:p + 20])[0]
            elif cid == b"data":
                return (cl if cl < size else size - p) / br if br else None
            p += 8 + cl + (cl & 1)
    except struct.error:
        pass
    return None


def classify_audio(path: str, name: str, sn, size: int, ext: str) -> Verdict:
    kind = sn.kind
    ev = [f"file signature: {kind}"]
    tags, dur = {}, None
    if kind == "mp3":
        tags, idl = id3_tags(path, size); dur = mp3_duration(path, size, idl)
    elif kind == "flac":
        tags, dur = flac_info(path)
    elif kind in ("m4a", "m4b"):
        tags = m4a_tags(path); dur = mp4_info(path).get("duration")
    elif kind == "wav":
        dur = wav_duration(sn.head, size)
    if tags:
        ev.append("tags: " + ", ".join(f"{k}={v[:30]}" for k, v in list(tags.items())[:3]))
    if dur:
        ev.append(f"{int(dur // 60)}m{int(dur % 60):02d}s")
    genre = tags.get("genre", "").lower()
    if kind == "midi":
        return Verdict(("Audio", "MIDI & Music Projects"), "MIDI file", 0.93, ev)
    if kind == "m4b" or re.search(r"audiobook|podcast|speech|spoken", genre) or NAME_PODCAST.search(name):
        return Verdict(("Audio", "Podcasts & Audiobooks"), "Podcast / audiobook", 0.88 if kind == "m4b" or genre else 0.75,
                       ev + (["M4B audiobook container"] if kind == "m4b" else ["genre/name says podcast or audiobook"]))
    if NAME_VOICE.search(name) or kind == "amr":
        return Verdict(("Audio", "Voice Notes & Recordings"), "Voice note / recording", 0.85, ev + ["recorder/WhatsApp naming or AMR voice codec"])
    if tags.get("artist") and tags.get("title"):
        return Verdict(("Audio", "Music"), f"Song: {tags['artist']} - {tags['title']}", 0.96, ev)
    if tags.get("title") or tags.get("album") or tags.get("artist"):
        return Verdict(("Audio", "Music"), "Music (partial tags)", 0.88, ev)
    if NAME_SFX.search(name) or (kind in ("wav", "aiff", "ogg") and dur is not None and dur < 12 and not NAME_ARTIST_TITLE.search(name)):
        return Verdict(("Audio", "Samples & Sound Effects"), "Sample / sound effect", 0.72, ev + ["short clip or sample-style name"])
    if NAME_ARTIST_TITLE.search(name) and ext in (".mp3", ".flac", ".m4a", ".ogg", ".wav", ".opus", ".wma", ".aac"):
        return Verdict(("Audio", "Music"), "Song (by 'Artist - Title' file name)", 0.76, ev + ["name looks like 'Artist - Title'"])
    if dur and dur > 25 * 60:
        return Verdict(("Audio", "Podcasts & Audiobooks"), "Long recording (mix / podcast / audiobook)", 0.6, ev + ["over 25 minutes, no tags"])
    return Verdict(("Audio",), "Audio", 0.88, ev)
