import io, json, os, struct, zipfile, zlib
from pathlib import Path

def zipbytes(files: dict) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for k, v in files.items():
            z.writestr(k, v if isinstance(v, (bytes, str)) else json.dumps(v))
    return b.getvalue()

def png(w, h):
    def chunk(t, d): 
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(min(h, 4)))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")

def jpeg_exif(w, h, make="Canon", model="EOS 80D"):
    mk, md = make.encode() + b"\x00", model.encode() + b"\x00"
    ifd_off = 8; n = 2
    data_off = ifd_off + 2 + n * 12 + 4
    tiff = b"II*\x00" + struct.pack("<I", 8) + struct.pack("<H", n)
    tiff += struct.pack("<HHII", 0x010F, 2, len(mk), data_off) + struct.pack("<HHII", 0x0110, 2, len(md), data_off + len(mk))
    tiff += struct.pack("<I", 0) + mk + md
    app1 = b"Exif\x00\x00" + tiff
    sof = b"\x08" + struct.pack(">HH", h, w) + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    return (b"\xff\xd8" + b"\xff\xe1" + struct.pack(">H", len(app1) + 2) + app1 +
            b"\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof + b"\xff\xda\x00\x02" + b"\x00" * 50 + b"\xff\xd9")

def jpeg_plain(w, h):
    sof = b"\x08" + struct.pack(">HH", h, w) + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    return b"\xff\xd8\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof + b"\xff\xda\x00\x02" + b"\x00" * 50 + b"\xff\xd9"

def mp4(w, h, dur_s, ts=1000):
    def box(t, d): return struct.pack(">I4s", len(d) + 8, t) + d
    mvhd = box(b"mvhd", b"\x00\x00\x00\x00" + b"\x00" * 8 + struct.pack(">II", ts, dur_s * ts) + b"\x00" * 80)
    matrix = struct.pack(">9i", 0x10000, 0, 0, 0, 0x10000, 0, 0, 0, 0x40000000)
    tk = b"\x00\x00\x00\x00" + b"\x00" * 8 + struct.pack(">I", 1) + b"\x00" * 4 + struct.pack(">I", dur_s * ts) + b"\x00" * 8 + b"\x00" * 8 + matrix + struct.pack(">II", w << 16, h << 16)
    trak = box(b"trak", box(b"tkhd", tk))
    ftyp = box(b"ftyp", b"isom\x00\x00\x02\x00isomiso2mp41")
    return ftyp + box(b"moov", mvhd + trak) + box(b"mdat", b"\x00" * 2000)

def mp3_tagged(title, artist):
    def fr(i, t): 
        body = b"\x03" + t.encode(); return i + struct.pack(">I", len(body)) + b"\x00\x00" + body
    frames = fr(b"TIT2", title) + fr(b"TPE1", artist)
    sz = len(frames); ss = bytes([(sz >> 21) & 127, (sz >> 14) & 127, (sz >> 7) & 127, sz & 127])
    return b"ID3\x03\x00\x00" + ss + frames + b"\xff\xfb\x90\x00" + b"\x00" * 4000

def pdf_text(text, pages=1):
    stream = ("BT /F1 12 Tf 72 720 Td (" + text.replace("(", "").replace(")", "") + ") Tj ET").encode()
    comp = zlib.compress(stream)
    return (b"%PDF-1.4\n1 0 obj<</Type/Pages/Count " + str(pages).encode() + b">>endobj\n2 0 obj<</Length " + str(len(comp)).encode() + b">>stream\n" + comp + b"\nendstream\nendobj\n%%EOF")

def lib_jar(group, art, ver):
    return zipbytes({"META-INF/MANIFEST.MF": f"Manifest-Version: 1.0\nAutomatic-Module-Name: {art}\n",
                     f"META-INF/maven/{group}/{art}/pom.properties": f"groupId={group}\nartifactId={art}\nversion={ver}\n",
                     "a/B.class": b"\xca\xfe\xba\xbe" + b"\x00" * 20})

def build(root: Path):
    def w(rel, data):
        p = root / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
    # the screenshot problem: library jars
    for g, a, v in [("org.apache.ant", "ant", "1.10.15"), ("org.ow2.asm", "asm", "9.8"), ("commons-io", "commons-io", "2.15.1"),
                    ("org.bouncycastle", "bcprov-jdk18on", "1.81"), ("com.google.errorprone", "error_prone_annotations", "2.36.0"),
                    ("org.apache.commons", "commons-lang3", "3.17.0")]:
        w(f"Minecraft & Mods/{a}-{v}.jar", lib_jar(g, a, v))
    w("Minecraft & Mods/sodium-fabric-0.5.3.jar", zipbytes({"fabric.mod.json": {"id": "sodium", "name": "Sodium", "version": "0.5.3"}, "x.class": b"\xca\xfe\xba\xbe"}))
    w("Minecraft & Mods/jei-forge.jar", zipbytes({"META-INF/mods.toml": 'modLoader="javafml"\n[[mods]]\nmodId="jei"\nversion="1.0"\ndisplayName="JEI"\n'}))
    w("Minecraft & Mods/EssentialsX.jar", zipbytes({"plugin.yml": "name: EssentialsX\nmain: com.earth2me.essentials.Essentials\nversion: 2.20\n"}))
    w("Minecraft & Mods/ViaVersion.jar", zipbytes({"paper-plugin.yml": "name: ViaVersion\nmain: x.Y\n"}))
    w("Minecraft & Mods/server.jar", zipbytes({"META-INF/MANIFEST.MF": "Main-Class: io.papermc.paperclip.Main\n", "io/papermc/paperclip/Main.class": b"x"}))
    w("Minecraft & Mods/mystery.jar", zipbytes({"readme.txt": "hi"}))
    w("Packs/FaithfulRP.zip", zipbytes({"pack.mcmeta": {"pack": {"pack_format": 15, "description": "x"}}, "assets/minecraft/textures/a.png": b"1"}))
    w("Packs/VanillaTweaks-dp.zip", zipbytes({"Wrap/pack.mcmeta": {"pack": {"pack_format": 26}}, "Wrap/data/minecraft/functions/a.mcfunction": "say hi"}))
    w("Packs/BSL_Shaders.zip", zipbytes({"shaders/final.fsh": "void main(){}", "shaders/shaders.properties": "x=1"}))
    w("Packs/bedrock.mcpack", zipbytes({"manifest.json": {"format_version": 2, "header": {"uuid": "1", "name": "BR"}, "modules": [{"type": "resources", "uuid": "2"}]}}))
    w("Packs/fabulous.mrpack", zipbytes({"modrinth.index.json": {"name": "Fabulously Optimized", "files": []}}))
    w("Packs/World.zip", zipbytes({"MyWorld/level.dat": b"x", "MyWorld/region/r.0.0.mca": b"x"}))
    w("Discord/bot.zip", zipbytes({"package.json": {"name": "b", "dependencies": {"discord.js": "^14"}}, "index.js": "const { Client } = require('discord.js');"}))
    w("Discord/music-bot.py", "import discord\nfrom discord.ext import commands\nbot = commands.Bot(command_prefix='!')\n")
    # unzipped folders (units)
    w("Loose/MyBot/package.json", json.dumps({"dependencies": {"discord.js": "14"}})); w("Loose/MyBot/index.js", "x"); w("Loose/MyBot/config.json", '{"token": "x"}')
    w("Loose/MyBot/commands/ping.js", "module.exports={}")
    w("Loose/SomeDatapack/pack.mcmeta", '{"pack":{"pack_format":10}}'); w("Loose/SomeDatapack/data/ns/functions/a.mcfunction", "say")
    w("Loose/MyServer/server.properties", "x=1"); w("Loose/MyServer/eula.txt", "eula=true"); w("Loose/MyServer/paper.jar", b"PK")
    w("Loose/webapp/package.json", json.dumps({"dependencies": {"react": "18"}})); w("Loose/webapp/src/App.jsx", "x")
    w("Loose/pysite/requirements.txt", "flask\n"); w("Loose/pysite/app.py", "x")
    w("Loose/RandomStuff/readme.txt", "hello")
    # media
    w("Media/IMG_2041.jpg", jpeg_exif(4000, 3000)); w("Media/Screenshot 2026-10-01 120000.png", png(1920, 1080))
    w("Media/IMG-20260101-WA0001.jpg", jpeg_plain(1280, 960)); w("Media/pic.png", png(300, 300)); w("Media/bg.jpg", jpeg_plain(3840, 2160))
    w("Media/Steve_skin.png", png(64, 64))
    w("Media/Breaking.Bad.S01E02.720p.mp4", mp4(1280, 720, 2700)); w("Media/VID_20260101_101010.mp4", mp4(1920, 1080, 20))
    w("Media/tiktok_clip.mp4", mp4(1080, 1920, 15)); w("Media/2026-10-01 10-10-10.mkv", b"\x1aE\xdf\xa3" + b"\x00" * 500)
    w("Media/Coldplay - Yellow.mp3", mp3_tagged("Yellow", "Coldplay")); w("Media/PTT-20260101-WA0002.opus", b"OggS" + b"\x00" * 100)
    w("Media/snare_01.wav", b"RIFF\x00\x00\x00\x00WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 44100, 88200, 2, 16) + b"data" + struct.pack("<I", 8820) + b"\x00" * 8820)
    # docs
    w("Docs/inv1.pdf", pdf_text("INVOICE No 1234 Bill To Acme Ltd Subtotal 100 Total due 118 VAT 18 Amount due"))
    w("Docs/cv.pdf", pdf_text("Curriculum Vitae John Work Experience Education Skills LinkedIn"))
    w("Docs/notes.txt", "shopping list: milk eggs"); w("Docs/server.log", "[12:00:00] [Server thread/INFO]: Starting minecraft server")
    w("Docs/crash-2026.txt", "---- Minecraft Crash Report ----\n// Oops")
    w("Docs/movie.srt", "1\n00:00:01,000 --> 00:00:03,000\nHello\n")
    w("Docs/assignment.docx", zipbytes({"[Content_Types].xml": "<x/>", "word/document.xml": "<w:t>Assignment 3 for the semester exam. Lecture notes chapter 4 university</w:t>"}))
    w("Docs/data.sqlite", b"SQLite format 3\x00" + b"\x00" * 100); w("Docs/font.ttf", b"\x00\x01\x00\x00\x00" + b"\x00" * 200)
    w("Docs/setup_app.exe", b"MZ" + b"\x00" * 500); w("Docs/lib.dll", b"MZ" + b"\x00" * 500)
    w("Docs/app.apk", zipbytes({"AndroidManifest.xml": "x", "classes.dex": "x"})); w("Docs/book.epub", zipbytes({"mimetype": "application/epub+zip", "a.xhtml": "x"}))
    w("Docs/video.ts", b"\x47" + b"\x00" * 187 + b"\x47" + b"\x00" * 187 + b"\x47" + b"\x00" * 300); w("Docs/code.ts", "export const a: number = 1;\n")
    w("Docs/weird.bin", bytes(range(256)) * 4); w("Docs/photos.zip", zipbytes({f"p{i}.jpg": b"x" for i in range(6)}))
    w("Docs/key.pem", "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n")
    w("Docs/archive.rar", b"Rar!\x1a\x07\x00" + b"\x00" * 50); w("Docs/liar.jpg", png(10, 10))
