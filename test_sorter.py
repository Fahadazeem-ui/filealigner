import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures_builder as fx
import sorter_core as core
from fsengine import Engine


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        core.UNDO_DIR = t / "undo"
        core.CACHE_PATH = t / "cache.json"
        self.root = t / "Downloads"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, data=b"x"):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
        return p

    def cats(self, **kw):
        res = core.scan(str(self.root), **kw)
        return {Path(os.path.relpath(i.source, self.root)).as_posix(): i.category for i in res.items}, res


class TestTheOriginalProblem(Base):
    def test_library_jars_are_not_minecraft_mods(self):
        """Screenshot case: 300 dependency jars were all dumped into 'Minecraft & Mods'."""
        libs = [("org.apache.ant", "ant", "1.10.15"), ("org.ow2.asm", "asm", "9.8"), ("commons-io", "commons-io", "2.15.1")]
        for g, a, v in libs:
            self.put(f"{a}-{v}.jar", fx.lib_jar(g, a, v))
        c, _ = self.cats()
        for g, a, v in libs:
            self.assertEqual(c[f"{a}-{v}.jar"], "Development/Libraries/Java")

    def test_real_mods_plugins_and_servers_still_found(self):
        self.put("sodium.jar", fx.zipbytes({"fabric.mod.json": {"id": "sodium", "version": "1"}}))
        self.put("jei.jar", fx.zipbytes({"META-INF/mods.toml": 'modId="jei"\n'}))
        self.put("neo.jar", fx.zipbytes({"META-INF/neoforge.mods.toml": 'modId="x"\n'}))
        self.put("ess.jar", fx.zipbytes({"plugin.yml": "name: Ess\nmain: a.B\n"}))
        self.put("paper.jar", fx.zipbytes({"META-INF/MANIFEST.MF": "Main-Class: io.papermc.paperclip.Main\n", "x.class": b"x"}))
        c, _ = self.cats()
        self.assertEqual(c["sodium.jar"], "Games/Minecraft/Mods/Fabric")
        self.assertEqual(c["jei.jar"], "Games/Minecraft/Mods/Forge")
        self.assertEqual(c["neo.jar"], "Games/Minecraft/Mods/NeoForge")
        self.assertEqual(c["ess.jar"], "Games/Minecraft/Plugins/Bukkit-Spigot-Paper")
        self.assertEqual(c["paper.jar"], "Games/Minecraft/Servers/Server Jars")

    def test_packs_shaders_worlds_bedrock_modpacks(self):
        self.put("rp.zip", fx.zipbytes({"pack.mcmeta": {"pack": {"pack_format": 15}}, "assets/a.png": b"1"}))
        self.put("dp.zip", fx.zipbytes({"W/pack.mcmeta": {"pack": {"pack_format": 15}}, "W/data/ns/functions/a.mcfunction": "x"}))
        self.put("sh.zip", fx.zipbytes({"shaders/final.fsh": "x", "shaders/shaders.properties": "a=1"}))
        self.put("br.mcpack", fx.zipbytes({"manifest.json": {"header": {"uuid": "1"}, "modules": [{"type": "data"}]}}))
        self.put("mp.mrpack", fx.zipbytes({"modrinth.index.json": {"name": "p"}}))
        self.put("w.zip", fx.zipbytes({"World/level.dat": b"x", "World/region/r.mca": b"x"}))
        c, _ = self.cats()
        self.assertEqual(c["rp.zip"], "Games/Minecraft/Resourcepacks")
        self.assertEqual(c["dp.zip"], "Games/Minecraft/Datapacks")
        self.assertEqual(c["sh.zip"], "Games/Minecraft/Shaders")
        self.assertEqual(c["br.mcpack"], "Games/Minecraft/Bedrock/Behavior Packs")
        self.assertEqual(c["mp.mrpack"], "Games/Minecraft/Modpacks")
        self.assertEqual(c["w.zip"], "Games/Minecraft/Worlds & Schematics/Worlds")

    def test_discord_bot_zip_folder_and_single_file(self):
        self.put("bot.zip", fx.zipbytes({"package.json": {"dependencies": {"discord.js": "14"}}, "index.js": "x"}))
        self.put("Bot2/requirements.txt", "py-cord==2.4\n")
        self.put("Bot2/main.py", "import discord\n")
        self.put("solo.py", "import discord\nbot = discord.Client()\n")
        c, _ = self.cats()
        self.assertEqual(c["bot.zip"], "Development/Discord Bots")
        self.assertEqual(c["Bot2"], "Development/Discord Bots")
        self.assertEqual(c["solo.py"], "Development/Discord Bots")


class TestUnitsAreNeverSplit(Base):
    def test_project_folder_moves_whole_and_inner_files_stay_inside(self):
        self.put("MyPack/pack.mcmeta", '{"pack":{"pack_format":9}}')
        self.put("MyPack/data/ns/functions/f.mcfunction", "say hi")
        self.put("MyPack/readme.txt", "hello")
        self.put("webapp/package.json", json.dumps({"dependencies": {"react": "18"}}))
        self.put("webapp/src/App.jsx", "x")
        self.put("webapp/config.json", "{}")
        c, res = self.cats()
        self.assertEqual(set(c), {"MyPack", "webapp"})            # nothing inside is listed separately
        core.execute(res)
        base = self.root / "Games/Minecraft/Datapacks/MyPack"
        self.assertTrue((base / "data/ns/functions/f.mcfunction").is_file())
        self.assertTrue((base / "readme.txt").is_file())
        self.assertTrue((self.root / "Development/Projects/Web Apps/webapp/src/App.jsx").is_file())

    def test_server_folder_is_one_unit(self):
        self.put("srv/server.properties", "a=1")
        self.put("srv/plugins/Ess.jar", fx.zipbytes({"plugin.yml": "name: E\nmain: a.B\n"}))
        self.put("srv/world/level.dat", b"x")
        self.put("srv/world/region/r.mca", b"x")
        c, _ = self.cats()
        self.assertEqual(c, {"srv": "Games/Minecraft/Servers"})

    def test_python_venv_is_left_alone(self):
        self.put("proj/.venv/pyvenv.cfg", "home=/x")
        self.put("venvdir/pyvenv.cfg", "home=/x")
        self.put("venvdir/lib/a.py", "x=1")
        c, res = self.cats()
        self.assertNotIn("venvdir/lib/a.py", c)
        self.assertTrue(any("virtual environment" in r for _, r in res.skipped))


class TestNoExtraction(Base):
    def test_zip_stays_a_zip_and_nothing_new_appears(self):
        self.put("mod.zip", fx.zipbytes({"fabric.mod.json": {"id": "m"}, "a/b.class": b"x"}))
        before = {p.name for p in self.root.rglob("*")}
        _, res = self.cats()
        core.execute(res)
        files = [p for p in self.root.rglob("*") if p.is_file()]
        self.assertEqual([p.name for p in files], ["mod.zip"])
        self.assertTrue(zipfile_ok(files[0]))
        self.assertNotIn("fabric.mod.json", {p.name for p in self.root.rglob("*")} - before)


def zipfile_ok(p):
    import zipfile
    return zipfile.is_zipfile(p)


class TestExistingFoldersAreInspected(Base):
    def test_misplaced_file_in_category_folder_moves_but_users_subfolders_are_respected(self):
        self.put("Images/holiday.jpg", fx.jpeg_exif(100, 100))
        self.put("Images/Trip 2024/pic.jpg", fx.jpeg_exif(100, 100))        # user's own sub-folder: leave
        self.put("Images/Trip 2024/clip.mp4", fx.mp4(1280, 720, 30))         # video hiding in Images: move
        self.put("Images/song.mp3", fx.mp3_tagged("Y", "C"))                 # audio hiding in Images: move
        c, res = self.cats(mode="audit")
        self.assertEqual(c["Images/Trip 2024/clip.mp4"], "Videos")
        self.assertEqual(c["Images/song.mp3"], "Audio/Music")
        self.assertNotIn("Images/Trip 2024/pic.jpg", c)
        self.assertEqual(len(c), 2)

    def test_legacy_minecraft_and_mods_folder_gets_repaired(self):
        for g, a, v in [("org.a", "a", "1.0"), ("org.b", "b", "2.0")]:
            self.put(f"Minecraft & Mods/{a}-{v}.jar", fx.lib_jar(g, a, v))
        self.put("Minecraft & Mods/real.jar", fx.zipbytes({"fabric.mod.json": {"id": "r"}}))
        self.put("unrelated/file.txt", "keep me here")
        c, res = self.cats(mode="audit")
        self.assertEqual(c["Minecraft & Mods/a-1.0.jar"], "Development/Libraries/Java")
        self.assertEqual(c["Minecraft & Mods/real.jar"], "Games/Minecraft/Mods/Fabric")
        self.assertNotIn("unrelated/file.txt", c)                             # audit never touches random folders

    def test_files_inside_ordinary_folders_are_sorted_in_full_mode(self):
        self.put("New folder (3)/a.mp3", fx.mp3_tagged("t", "a"))
        self.put("New folder (3)/b.jpg", fx.jpeg_exif(10, 10))
        c, _ = self.cats()
        self.assertEqual(c["New folder (3)/a.mp3"], "Audio/Music")
        self.assertEqual(c["New folder (3)/b.jpg"], "Images/Photos")


class TestSafetyAndIdempotence(Base):
    def test_rescan_after_sort_finds_nothing_to_do(self):
        fx.build(self.root)
        core.execute(core.scan(str(self.root)))
        again = core.scan(str(self.root))
        self.assertEqual(again.items, [])
        self.assertGreater(again.in_place, 30)

    def test_undo_restores_everything_including_removed_empty_folders(self):
        fx.build(self.root)
        snap = sorted(os.path.relpath(p, self.root) for p in self.root.rglob("*"))
        out = core.execute(core.scan(str(self.root)))
        self.assertFalse(out.failed)
        n, failed = core.undo()
        self.assertEqual(failed, [])
        self.assertEqual(n, len(out.moved))
        self.assertEqual(snap, sorted(os.path.relpath(p, self.root) for p in self.root.rglob("*")))

    def test_name_collisions_never_overwrite(self):
        self.put("a/x.png", fx.png(500, 500))
        self.put("b/x.png", fx.png(600, 600))
        _, res = self.cats()
        out = core.execute(res)
        self.assertEqual(len(out.moved), 2)
        self.assertEqual(len(list((self.root / "Images").glob("x*.png"))), 2)

    def test_refuses_drive_roots_and_home(self):
        for bad in (os.path.abspath(os.sep), os.path.expanduser("~")):
            with self.assertRaises(ValueError):
                core.scan(bad)

    def test_unselected_items_are_not_moved(self):
        self.put("a.png", fx.png(500, 500))
        _, res = self.cats()
        res.items[0].selected = False
        core.execute(res)
        self.assertTrue((self.root / "a.png").exists())


class TestEngineDetails(Base):
    def setUp(self):
        super().setUp()
        self.e = Engine()

    def v(self, name, data):
        return self.e.classify_file(str(self.put(name, data)))

    def test_content_beats_extension(self):
        self.assertEqual(self.v("photo.jpg", fx.png(300, 300)).dest[0], "Images")
        self.assertEqual(self.v("renamed.dat", fx.mp3_tagged("t", "a")).path, "Audio/Music")
        self.assertEqual(self.v("movie.bin", fx.mp4(1280, 720, 30)).dest[0], "Videos")

    def test_dot_ts_is_video_or_typescript_by_content(self):
        ts = b"\x47" + b"\x00" * 187 + b"\x47" + b"\x00" * 187 + b"\x47" + b"\x00" * 300
        self.assertEqual(self.v("a.ts", ts).dest[0], "Videos")
        self.assertEqual(self.v("b.ts", "export const a: number = 1;\n").path, "Development/Scripts/JavaScript & TypeScript")

    def test_unknown_goes_to_review_with_reason_not_a_junk_folder(self):
        v = self.v("mystery.xyz", bytes(range(256)) * 4)
        self.assertEqual(v.dest[0], "Review")
        self.assertTrue(v.evidence)

    def test_every_verdict_explains_itself(self):
        for name, data in (("a.jar", fx.lib_jar("g", "a", "1")), ("s.png", fx.png(1920, 1080)), ("p.pdf", fx.pdf_text("invoice total due bill to"))):
            self.assertTrue(self.v(name, data).evidence, name)

    def test_documents_by_content(self):
        self.assertEqual(self.v("x.pdf", fx.pdf_text("Curriculum Vitae Work Experience Education Skills")).path, "Documents/Resumes & CVs")
        self.assertEqual(self.v("y.pdf", fx.pdf_text("INVOICE Bill To Subtotal Total due VAT")).path, "Documents/Invoices & Receipts")

    def test_media_subtypes(self):
        self.assertEqual(self.v("IMG_2041.jpg", fx.jpeg_exif(4000, 3000)).path, "Images/Photos")
        self.assertEqual(self.v("Screenshot 2026-10-01.png", fx.png(1920, 1080)).path, "Images/Screenshots")
        self.assertEqual(self.v("Show.S01E02.720p.mp4", fx.mp4(1280, 720, 2700)).path, "Videos/TV Shows & Anime")
        self.assertEqual(self.v("clip.mp4", fx.mp4(1080, 1920, 15)).path, "Videos/Shorts & Vertical")

    def test_user_rules_override(self):
        rules = Path(self.tmp.name) / "rules.json"
        rules.write_text(json.dumps({"extensions": {".foo": ["Games", "Foo"]}}))
        from fsengine.rules import UserRules
        e = Engine(UserRules(str(rules)))
        self.assertEqual(e.classify_file(str(self.put("a.foo", b"zzz"))).path, "Games/Foo")


class TestRobustness(Base):
    def test_corrupt_and_truncated_files_never_crash_the_engine(self):
        import random
        random.seed(3)
        fx.build(self.root)
        e = Engine()
        for p in [p for p in self.root.rglob("*") if p.is_file()]:
            data = p.read_bytes()
            for i, d in enumerate((data[: len(data) // 2], data[:7], b"", bytes(random.randrange(256) for _ in range(len(data))))):
                q = self.root / "fuzz" / f"{i}_{p.name}"
                q.parent.mkdir(exist_ok=True)
                q.write_bytes(d)
                v = e.classify_file(str(q))
                self.assertNotIn("Could not analyse", v.label, f"{q.name}: {v.evidence}")


class TestScale(Base):
    def test_thousands_of_files_scan_quickly_and_cache_helps(self):
        for i in range(3000):
            self.put(f"bulk/f{i}.jpg", fx.jpeg_plain(100, 100))
        t = time.time()
        r1 = core.scan(str(self.root))
        first = time.time() - t
        t = time.time()
        core.scan(str(self.root))
        second = time.time() - t
        self.assertEqual(len(r1.items), 3000)
        self.assertLess(first, 20)
        self.assertLessEqual(second, first)


class TestRealWorldCases(Base):
    """The zips that went to the wrong folder: a repo, an exe zip, shaders, resource packs, mods."""

    def setUp(self):
        super().setUp()
        self.e = Engine()

    def test_repo_zip_is_a_project_not_an_archive(self):
        """FileSorter.zip: README + package-less python sources + .github -> Development/Projects/Python."""
        import bench.corpus as corpus
        p = self.put("FileSorter.zip", corpus.zbytes({
            "FileSorter/README.md": "# FileSorter", "FileSorter/sorter.py": "import os",
            "FileSorter/fsengine/classify.py": "x=1", "FileSorter/fsengine/rules.py": "x=2",
            "FileSorter/test_sorter.py": "def t(): pass", "FileSorter/run.bat": "python file_sorter.py",
            "FileSorter/.github/workflows/build.yml": "name: build"}))
        self.assertEqual(self.e.classify_file(str(p)).path, "Development/Projects/Python")

    def test_exe_only_zip_is_software_not_archives(self):
        import bench.corpus as corpus
        p = self.put("FileSorter-exe.zip", corpus.zbytes({"FileSorter.exe": corpus.exe(product="FileSorter")}))
        v = self.e.classify_file(str(p))
        self.assertEqual(v.path, "Software/Programs")
        self.assertTrue(any("single" in e or "wraps" in e for e in v.evidence), v.evidence)

    def test_shader_pack_with_pack_mcmeta_is_a_shader_pack(self):
        import bench.corpus as corpus
        files = {"pack.mcmeta": '{"pack":{"pack_format":8}}'}
        files.update({f"shaders/{n}.fsh": "void main(){}" for n in
                      ("final", "composite", "composite1", "gbuffers_basic", "gbuffers_terrain", "shadow")})
        files["shaders/shaders.properties"] = "shadowMapResolution=2048\n"
        p = self.put("BSL_Shaders_v8.zip", corpus.zbytes(files))
        self.assertEqual(self.e.classify_file(str(p)).path, "Games/Minecraft/Shaders")

    def test_resource_pack_with_core_shaders_is_a_resource_pack(self):
        """assets/*/shaders/ is a resource pack (core shaders) - not a shader pack."""
        import bench.corpus as corpus
        p = self.put("FaithfulCore.zip", corpus.zbytes({
            "pack.mcmeta": '{"pack":{"pack_format":22}}',
            "assets/minecraft/shaders/core/rendertype_solid.fsh": "void main(){}",
            "assets/minecraft/shaders/include/fog.glsl": "float f(){}",
            "assets/minecraft/textures/block/stone.png": fx.png(16, 16)}))
        v = self.e.classify_file(str(p))
        self.assertEqual(v.path, "Games/Minecraft/Resourcepacks")
        self.assertTrue(any("resource pack" in e for e in v.evidence), v.evidence)

    def test_obfuscated_mod_without_descriptor_is_found_by_bytecode(self):
        import bench.corpus as corpus
        p = self.put("mystery.jar", corpus.zbytes({"a/b/c.class": corpus.cls("net/minecraftforge/fml/common/Mod")}))
        v = self.e.classify_file(str(p))
        self.assertEqual(v.path, "Games/Minecraft/Mods/Forge")
        self.assertTrue(any("bytecode" in e for e in v.evidence), v.evidence)

    def test_multi_loader_jar_is_not_filed_as_one_loader(self):
        import bench.corpus as corpus
        p = self.put("multi.jar", corpus.zbytes({"fabric.mod.json": '{"id":"m"}', "META-INF/mods.toml": 'modId="m"\n'}))
        self.assertEqual(self.e.classify_file(str(p)).path, "Games/Minecraft/Mods/Multi-loader")

    def test_disabled_and_renamed_jars_are_still_read(self):
        import bench.corpus as corpus
        for name in ("sodium.jar.disabled", "sodium.jar.old", "sodium.jar.bak"):
            p = self.put(name, corpus.zbytes({"fabric.mod.json": '{"id":"sodium"}'}))
            v = self.e.classify_file(str(p))
            self.assertEqual(v.path, "Games/Minecraft/Mods/Fabric", name)
            self.assertTrue(any(".disabled" in e or ".old" in e or ".bak" in e for e in v.evidence), v.evidence)

    def test_zip_of_photos_is_not_an_archive(self):
        import bench.corpus as corpus
        p = self.put("holiday.zip", corpus.zbytes({f"p{i}.jpg": fx.jpeg_plain(640, 480) for i in range(6)}))
        self.assertEqual(self.e.classify_file(str(p)).path, "Images/Zipped Collections")

    def test_zip_of_mixed_things_stays_an_archive(self):
        import bench.corpus as corpus
        p = self.put("mixed.zip", corpus.zbytes({"a.pdf": fx.pdf_text("hello"), "b.png": fx.png(4, 4),
                                                 "c.mp3": fx.mp3_tagged("t", "a"), "d.exe": corpus.exe(product="X")}))
        self.assertEqual(self.e.classify_file(str(p)).path, "Archives/Mixed Contents")

    def test_bot_zip_with_src_layout_is_a_bot(self):
        import bench.corpus as corpus
        p = self.put("repo-main.zip", corpus.zbytes({
            "repo-main/package.json": '{"dependencies":{"discord.js":"14"}}',
            "repo-main/src/bot/index.js": "const {Client}=require('discord.js');\nclient.login(process.env.TOKEN);",
            "repo-main/src/bot/commands/ping.js": "module.exports={}", "repo-main/.env": "DISCORD_TOKEN=x"}))
        self.assertEqual(self.e.classify_file(str(p)).path, "Development/Discord Bots")

    def test_leaked_bot_token_is_warned_about(self):
        import bench.corpus as corpus
        token = "M" + "z" * 23 + ".abcdef.ghiJKLmnopQRStuvWX1234567890"
        p = self.put("bot.zip", corpus.zbytes({"bot.py": "import discord\nbot.run(TOKEN)",
                                              ".env": f"DISCORD_TOKEN={token}"}))
        v = self.e.classify_file(str(p))
        self.assertTrue(any("token" in e.lower() for e in v.evidence), v.evidence)

    def test_installer_and_portable_app_zips(self):
        import bench.corpus as corpus
        inst = self.put("Setup.zip", corpus.zbytes({"CoolSetup.exe": corpus.exe(product="Cool", markers=("Nullsoft",))}))
        self.assertEqual(self.e.classify_file(str(inst)).path, "Software/Installers")
        port = self.put("Portable.zip", corpus.zbytes({"t.exe": corpus.exe(product="T"),
                                                       **{f"l{i}.dll": b"MZ" + b"\x00" * 40 for i in range(4)}}))
        self.assertEqual(self.e.classify_file(str(port)).path, "Software/Portable Apps & Installed Programs")

    def test_nested_mod_in_a_zip_keeps_its_loader(self):
        import bench.corpus as corpus
        p = self.put("nested.zip", corpus.zbytes({"inner.jar": corpus.zbytes({"fabric.mod.json": '{"id":"x"}'})}))
        self.assertEqual(self.e.classify_file(str(p)).path, "Games/Minecraft/Mods/Fabric")

    def test_engine_never_reads_more_than_it_has_to(self):
        """Tiering: a settled item must not trigger the expensive probes."""
        import bench.corpus as corpus
        from fsengine import probes
        calls = {"n": 0}
        real = probes.bytecode_markers
        probes.bytecode_markers = lambda *a, **k: (calls.__setitem__("n", calls["n"] + 1), real(*a, **k))[1]
        try:
            e = Engine()
            p = self.put("sodium.jar", corpus.zbytes({"fabric.mod.json": '{"id":"sodium"}'}))
            e.classify_file(str(p))
            self.assertEqual(calls["n"], 0, "bytecode probe ran even though the descriptor settled it")
            q = self.put("mystery2.jar", corpus.zbytes({"a.class": corpus.cls("net/fabricmc/api/ModInitializer")}))
            e.classify_file(str(q))
            self.assertGreaterEqual(calls["n"], 1)
        finally:
            probes.bytecode_markers = real


class TestLearningAndLookup(Base):
    def setUp(self):
        super().setUp()
        self.e = Engine()

    def test_correction_is_remembered_and_applied(self):
        import bench.corpus as corpus
        from fsengine import Corrections
        corr = Corrections(path=str(Path(self.tmp.name) / "corr.json"))
        e = Engine(corrections=corr)
        files = {"bot.py": "import discord\nbot.run(TOKEN)", "cogs/a.py": "import discord",
                 ".env": "TOKEN=abc", "requirements.txt": "discord.py"}
        p = self.put("mybot.zip", corpus.zbytes(files))
        learned = corr.record_path(str(p), ("Development", "My Bots"), "test")
        self.assertTrue(learned)
        again = self.put("another-bot.zip", corpus.zbytes(files))
        v = e.classify_file(str(again))
        self.assertEqual(v.path, "Development/My Bots")
        self.assertTrue(any("filed" in x for x in v.evidence), v.evidence)

    def test_correction_does_not_leak_to_unrelated_files(self):
        import bench.corpus as corpus
        from fsengine import Corrections
        corr = Corrections(path=str(Path(self.tmp.name) / "corr.json"))
        e = Engine(corrections=corr)
        corr.record_path(str(self.put("bot.zip", corpus.zbytes({"bot.py": "import discord", "cogs/a.py": "x",
                                                                ".env": "t=1", "requirements.txt": "discord.py"}))),
                         ("Development", "My Bots"))
        v = e.classify_file(str(self.put("pack.zip", corpus.zbytes({"pack.mcmeta": "{}", "assets/minecraft/lang/en_us.json": "{}"}))))
        self.assertEqual(v.path, "Games/Minecraft/Resourcepacks")

    def test_online_lookup_is_off_by_default_and_only_sends_hashes(self):
        import bench.corpus as corpus
        from fsengine import Lookup
        sent = []

        def fake_fetch(url, data=None):
            sent.append((url, data))
            if "version_files" in url:
                return {"abc": {"project_id": "P1", "name": "BSL", "loaders": ["iris"]}}
            return {"project_type": "shader", "title": "BSL Shaders"}

        files = {f"shaders/x{i}.fsh": "void main(){}" for i in range(3)}
        files["shaders/readme.txt"] = "notes " * 400
        p = self.put("mystery_shader.zip", corpus.zbytes(files))
        off = Lookup(enabled=False, fetch=fake_fetch, cache_path=str(Path(self.tmp.name) / "hc.json"))
        Engine(online=off).classify_file(str(p))
        self.assertEqual(sent, [], "lookup ran while disabled")

        on = Lookup(enabled=True, fetch=fake_fetch, cache_path=str(Path(self.tmp.name) / "hc.json"))
        v = Engine(online=on).classify_file(str(p))
        self.assertTrue(sent, "lookup did not run")
        for url, data in sent:
            body = (data or b"").decode() if isinstance(data, (bytes, bytearray)) else ""
            self.assertNotIn("shaders", body, "the file name/listing must never be sent")
        self.assertEqual(v.path, "Games/Minecraft/Shaders")
        self.assertTrue(any("hash" in e for e in v.evidence), v.evidence)

    def test_review_verdicts_explain_themselves(self):
        p = self.put("mystery.xyz", bytes(range(256)) * 4)
        v = self.e.classify_file(str(p))
        self.assertEqual(v.dest[0], "Review")
        self.assertTrue(v.evidence)


class TestCorpusRoundTrip(Base):
    """The whole pipeline on 120+ labelled items at once: sort, then re-scan must find nothing to do."""

    def test_sort_120_items_then_rescan_is_idle(self):
        import bench.corpus as corpus
        for case in corpus.CASES:
            corpus.build_case(case, str(self.root))
        # extra junk that must not break anything
        self.put("empty-file.txt", b"")
        self.put("half-download.crdownload", b"PK\x03\x04")
        self.put("desktop.ini", b"[.ShellClassInfo]")
        self.put("~$draft.docx", b"PK\x03\x04")
        self.put("New folder/with/deep/stuff.txt", b"hello")
        t0 = time.time()
        res = core.scan(str(self.root))
        scan_seconds = time.time() - t0
        self.assertGreaterEqual(len(res.items), 110)
        self.assertLess(scan_seconds, 60, "scan got slow")
        out = core.execute(res)
        self.assertFalse(out.failed, out.failed[:5])
        again = core.scan(str(self.root))
        stray = [i.name for i in again.items]
        self.assertEqual(stray, [], f"second scan still wants to move {stray[:10]}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
