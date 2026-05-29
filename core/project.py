"""
core/project.py
===============
Holds all project state and handles JSON serialization / deserialization.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from .theory import Chord


@dataclass
class ProjectSettings:
    root: str       = "C"
    scale: str      = "Major"
    style: str      = "Pop"
    mood: str       = "Happy"
    complexity: str = "Medium"
    bpm: int        = 90
    bars_per_chord: int = 2
    time_signature: str = "4/4"
    drum_variant:   int = 0
    fill_frequency: int = 4
    drum_pattern: str = 'Auto (match style)'


def chord_to_dict(c: Chord) -> dict:
    return {
        "root": c.root,
        "quality": c.quality,
        "bass": c.bass,
        "degree": c.degree,
        "function": c.function,
        "label": c.label,
        "borrowed": c.borrowed,
        "secondary_target": c.secondary_target,
    }


def chord_from_dict(d: dict) -> Chord:
    return Chord(
        root=d["root"],
        quality=d["quality"],
        bass=d.get("bass"),
        degree=d.get("degree"),
        function=d.get("function", "color"),
        label=d.get("label", ""),
        borrowed=d.get("borrowed", False),
        secondary_target=d.get("secondary_target"),
    )


@dataclass
class Project:
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    progression: List[Chord]  = field(default_factory=list)
    filename: Optional[str]   = None

    # ---- serialization ----

    def to_dict(self) -> dict:
        return {
            "settings": asdict(self.settings),
            "progression": [chord_to_dict(c) for c in self.progression],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        settings = ProjectSettings(**data.get("settings", {}))
        progression = [chord_from_dict(d) for d in data.get("progression", [])]
        return cls(settings=settings, progression=progression)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        self.filename = path

    @classmethod
    def load(cls, path: str) -> "Project":
        with open(path) as f:
            data = json.load(f)
        proj = cls.from_dict(data)
        proj.filename = path
        return proj

    # ---- helpers ----

    def add_chord(self, chord: Chord) -> None:
        self.progression.append(chord)

    def remove_chord(self, index: int) -> None:
        if 0 <= index < len(self.progression):
            self.progression.pop(index)

    def move_chord(self, from_idx: int, to_idx: int) -> None:
        if from_idx == to_idx:
            return
        chord = self.progression.pop(from_idx)
        self.progression.insert(to_idx, chord)

    def clear(self) -> None:
        self.progression.clear()
