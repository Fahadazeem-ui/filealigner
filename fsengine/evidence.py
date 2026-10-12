"""Evidence + scoring. Detectors do not decide, they *testify*; this layer weighs the testimony.

Old design was "first rule that matches wins". One wrong-looking zip (a bot repo, a shader pack
with a pack.mcmeta, an obfuscated mod jar) was enough to lose the item to a wrong folder.

New design:
    detector -> Signal(destination, weight, reason)
    fusion   -> score per destination, pick the best, keep the runner-up as a caveat,
                turn the score into a confidence, and always keep the reasons.

Weight vocabulary (every detector speaks the same language, so scores are comparable):

    W.DECISIVE  3.0   a marker that cannot reasonably mean anything else (fabric.mod.json,
                      plugin.yml with main:, package.json depending on discord.js, PE version info)
    W.STRONG    2.0   strong but not unique (shaders/*.fsh, assets/minecraft/textures, cogs/+events/)
    W.MEDIUM    1.2   suggestive (old asset layouts, folder shape, source imports)
    W.WEAK      0.6   a hint (file name, ecosystem naming, batch of relatives)
    W.TINY      0.35  whisper (a generic directory name)
    W.ANTI     -1.5   counter-evidence ("has .class files, so it is not a pure resource pack")

Scores add up, so several medium hints can outvote one wrong strong hint - and a single decisive
marker still wins on its own. Negative weights push a destination down instead of blocking it,
which is how hybrid packs (datapack + resources, resource pack + core shaders) stay explainable.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .model import Verdict, review


class W:
    DECISIVE = 3.0
    STRONG = 2.0
    MEDIUM = 1.2
    WEAK = 0.6
    TINY = 0.35
    ANTI = -1.5

    @staticmethod
    def from_confidence(conf: float) -> float:
        """Bridge for the legacy content detectors (media.py / documents.py): their confidence
        becomes a comparable weight.  0.95 -> ~3.0 | 0.8 -> ~2.0 | 0.6 -> ~0.7."""
        return max(0.45, (float(conf) - 0.5) * 6.6)


@dataclass(frozen=True)
class Signal:
    dest: tuple[str, ...]
    weight: float
    detail: str
    probe: str = ""
    label: str = ""

    @staticmethod
    def of(dest, weight: float, detail: str, probe: str = "", label: str = "") -> "Signal":
        return Signal(tuple(dest), float(weight), detail, probe, label)


@dataclass
class Board:
    signals: list[Signal] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)   # e.g. a leaked bot token in the config
    fallback_label: str = ""
    fallback_dest: tuple[str, ...] | None = None        # used when voters only cancel each other
    unit: bool = False
    labels: dict[tuple[str, ...], tuple[float, str]] = field(default_factory=dict)   # dest -> (weight, label)

    # ------------------------------------------------------------------ adding
    def add(self, dest, weight: float, detail: str, probe: str = "", label: str = "") -> None:
        self.signals.append(Signal.of(_flat(dest), weight, detail, probe, label))

    def add_verdict(self, v: Verdict, probe: str = "", weight: float | None = None) -> None:
        if v is None:
            return
        self.add(v.dest, W.from_confidence(v.confidence) if weight is None else weight, v.label, probe, v.label)
        for e in v.evidence:
            self.notes.append(f"{probe or 'content'}: {e}")

    def label(self, dest, text: str, weight: float = 1.0) -> None:
        """Give a destination a human name (used for the GUI/CLI line). Heaviest claim wins."""
        dest = _flat(dest)
        cur = self.labels.get(dest)
        if text and (cur is None or weight >= cur[0]):
            self.labels[dest] = (weight, text)

    def note(self, text: str) -> None:
        self.notes.append(text)

    def warn(self, text: str) -> None:
        self.warnings.append(text)

    # ------------------------------------------------------------------ scoring
    # weak probe classes overlap ("extension .mp4" and "content signature mp4" are the same fact),
    # so within one destination they count once (max), not twice (sum).
    WEAK_PROBES = {"name", "magic", "census"}

    def _raw(self) -> dict[tuple[str, ...], float]:
        raw: dict[tuple[str, ...], float] = {}
        weak: dict[tuple[str, ...], float] = {}
        for s in self.signals:
            if s.probe in self.WEAK_PROBES:
                weak[s.dest] = max(weak.get(s.dest, -9.9), s.weight) if s.weight >= 0 \
                    else min(weak.get(s.dest, 0.0), s.weight)
            else:
                raw[s.dest] = raw.get(s.dest, 0.0) + s.weight
        for dest, w in weak.items():
            raw[dest] = raw.get(dest, 0.0) + w
        return raw

    def scores(self) -> dict[tuple[str, ...], float]:
        """Weight with hierarchy credit: a claim about a parent partly supports its children and
        the other way round, but the direct claim always dominates."""
        raw = self._raw()
        out: dict[tuple[str, ...], float] = {}
        for d in raw:
            s = raw[d]
            for o, w in raw.items():
                if o == d or w <= 0:
                    continue
                if _is_prefix(o, d):
                    s += 0.30 * w
                elif _is_prefix(d, o):
                    s += 0.20 * w
            out[d] = s
        return out

    def best(self) -> tuple[tuple[str, ...] | None, float, float, tuple[str, ...] | None]:
        sc = self.scores()
        if not sc:
            return None, 0.0, 0.0, None
        order = sorted(sc.items(), key=lambda kv: (-kv[1], -len(kv[0])))
        best, bs = order[0]
        # a deeper destination wins a photo finish against its own ancestor (be specific)
        for d, s in order[1:]:
            if _is_prefix(best, d) and s >= bs - 0.6:
                best, bs = d, s
                break
        margin, runner = 9.9, None
        for d, s in order:
            if d == best or _is_prefix(d, best) or _is_prefix(best, d):
                continue
            margin, runner = bs - s, d
            break
        return best, bs, margin, runner

    def best_score(self) -> float:
        return self.best()[1]

    def strong_scores(self) -> dict[tuple[str, ...], float]:
        """Scores from the evidence that needed real reading (no name/extension hints)."""
        strong = Board()
        strong.signals = [s for s in self.signals if s.probe not in self.WEAK_PROBES]
        return strong.scores()

    def decisive(self, need: float = 2.8, margin: float = 1.1) -> bool:
        """Enough to stop deepening? Only *read* evidence counts - a name hint is never enough."""
        sc = self.strong_scores()
        if not sc:
            return False
        order = sorted(sc.items(), key=lambda kv: (-kv[1], -len(kv[0])))
        best, bs = order[0]
        margin2 = 9.9
        for d, s in order[1:]:
            if _is_prefix(d, best) or _is_prefix(best, d):
                continue
            margin2 = bs - s
            break
        return bs >= need and margin2 >= margin

    # ------------------------------------------------------------------ output
    def _probes_for(self, dest: tuple[str, ...]) -> set[str]:
        return {s.probe for s in self.signals if s.dest == dest and s.weight > 0 and s.probe}

    def label_for(self, dest: tuple[str, ...]) -> str:
        explicit = self.labels.get(tuple(dest))
        if explicit and explicit[1]:
            return explicit[1]
        return self.fallback_label or "/".join(dest)

    def explain(self, dest: tuple[str, ...]) -> list[str]:
        strong = [s for s in self.signals if s.dest == dest and s.weight > 0]
        weak = [s for s in self.signals if s.dest != dest and s.weight > 0]
        out = [f"+ {s.detail}" + (f"  [{s.probe}]" if s.probe else "") for s in
               sorted(strong, key=lambda s: -s.weight)]
        anti = [s for s in self.signals if s.dest == dest and s.weight < 0]
        out += [f"- {s.detail}" for s in anti]
        if not strong:
            out += [f"~ {s.detail}" for s in sorted(weak, key=lambda s: -s.weight)[:3]]
        out += self.notes
        out += self.warnings
        return out

    def confidence(self) -> tuple[float, tuple[str, ...] | None, float, tuple[str, ...] | None]:
        best, score, margin, runner = self.best()
        if best is None:
            return 0.0, None, margin, runner
        conf = 1.0 / (1.0 + math.exp(-(score - 0.85) / 1.0))
        if len(self._probes_for(best)) >= 2:      # two independent probes agreeing
            conf = min(0.99, conf + 0.03)
        conf = min(0.99, conf)
        if margin < 1.0:                          # real conflict -> say so instead of pretending
            conf *= 0.72 + 0.28 * max(0.0, margin)
        return conf, best, margin, runner

    def verdict(self, floor: float = 0.8) -> Verdict:
        conf, best, margin, runner = self.confidence()
        if best is None or self.best_score() < floor:
            reason = self.fallback_label or "No recognisable content"
            return review(reason, self.notes[:6] + self.warnings, self._review_bucket())
        label = self.label_for(best)
        alt = [(runner, round(self.scores().get(runner, 0.0), 2))] if runner else []
        ev = self.explain(best)
        if margin < 1.0 and runner:
            ev.append(f"other candidate on the table: {'/'.join(str(x) for x in runner)} (its content disagrees)")
        collision = ""
        if self.fallback_dest and margin < 1.0 and any(s.dest == self.fallback_dest for s in self.signals):
            collision = "/".join(self.fallback_dest)
        return Verdict(best, label, conf, ev, self.unit, alt, collision)

    def _review_bucket(self) -> str:
        for s in self.signals:
            if s.dest and s.dest[0] == "Review":
                return s.dest[-1]
        return "Unidentified"


def _flat(dest) -> tuple[str, ...]:
    """Accept ("A", ("B", "C")) as ("A", "B", "C") - a nested tuple is always a bug upstream."""
    out: list[str] = []
    for part in dest:
        if isinstance(part, str):
            out.append(part)
        else:
            out.extend(_flat(part))
    return tuple(out)


def _is_prefix(a: tuple[str, ...], b: tuple[str, ...]) -> bool:
    return len(a) < len(b) and b[: len(a)] == a


def is_prefix(a: tuple[str, ...], b: tuple[str, ...]) -> bool:
    return _is_prefix(a, b)
