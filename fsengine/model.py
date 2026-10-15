"""Verdict = where something should go, how sure we are, and WHY."""
from __future__ import annotations

from dataclasses import dataclass, field

SURE, PROBABLY, UNSURE = "Sure", "Probably", "Unsure"
REVIEW_THRESHOLD = 0.5


def confidence_label(c: float) -> str:
    return SURE if c >= 0.85 else PROBABLY if c >= 0.6 else UNSURE


@dataclass
class Verdict:
    dest: tuple[str, ...]            # e.g. ("Games", "Minecraft", "Mods", "Fabric")
    label: str                       # human description, e.g. "Fabric mod 'sodium' 0.5.3"
    confidence: float = 0.8
    evidence: list[str] = field(default_factory=list)
    unit: bool = False               # True = a whole folder that must move as ONE thing

    @property
    def level(self) -> str:
        return confidence_label(self.confidence)

    @property
    def path(self) -> str:
        return "/".join(self.dest)

    def to_json(self) -> dict:
        return {"dest": list(self.dest), "label": self.label, "confidence": self.confidence,
                "evidence": self.evidence, "unit": self.unit}

    @staticmethod
    def from_json(d: dict) -> "Verdict":
        return Verdict(tuple(d["dest"]), d["label"], d["confidence"], list(d.get("evidence", [])), d.get("unit", False))


def review(reason: str, evidence: list[str] | None = None, bucket: str = "Unidentified") -> Verdict:
    """Not sure -> never dumped into a junk folder; goes to Review with the reason attached."""
    return Verdict(("Review", bucket), reason, 0.3, evidence or [])
