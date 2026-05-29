"""
core/theory.py
==============
Pure music theory: note names, intervals, scale construction,
chord building (triads, 7ths, extensions, borrowed, secondary dominants).
No GUI, no MIDI — just pitch math.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Chromatic fundamentals
# ---------------------------------------------------------------------------

CHROMATIC = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
ENHARMONIC = {
    "Db": "C#", "D#": "Eb", "E#": "F", "Fb": "E",
    "Gb": "F#", "G#": "Ab", "A#": "Bb", "B#": "C", "Cb": "B",
}

def note_to_pc(name: str) -> int:
    """Note name → pitch class 0-11."""
    name = ENHARMONIC.get(name, name)
    return CHROMATIC.index(name)

def pc_to_note(pc: int, prefer_flat: bool = False) -> str:
    """Pitch class → note name."""
    sharp_names = CHROMATIC
    flat_names  = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"]
    return flat_names[pc % 12] if prefer_flat else sharp_names[pc % 12]

def transpose(note: str, semitones: int, prefer_flat: bool = False) -> str:
    pc = (note_to_pc(note) + semitones) % 12
    return pc_to_note(pc, prefer_flat)

# ---------------------------------------------------------------------------
# Scale interval patterns (semitones from root)
# ---------------------------------------------------------------------------

SCALE_INTERVALS = {
    "Major":              [0, 2, 4, 5, 7, 9, 11],
    "Natural Minor":      [0, 2, 3, 5, 7, 8, 10],
    "Harmonic Minor":     [0, 2, 3, 5, 7, 8, 11],
    "Dorian":             [0, 2, 3, 5, 7, 9, 10],
    "Phrygian Dominant":  [0, 1, 4, 5, 7, 8, 10],
    "Hijaz":              [0, 1, 4, 5, 7, 8, 10],  # same as Phryg Dom but styled differently
}

# Chord quality interval sets (above root)
TRIAD_INTERVALS = {
    "maj": [0, 4, 7],
    "min": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
}

SEVENTH_INTERVALS = {
    "maj7":  [0, 4, 7, 11],
    "7":     [0, 4, 7, 10],
    "min7":  [0, 3, 7, 10],
    "m7b5":  [0, 3, 6, 10],
    "dim7":  [0, 3, 6, 9],
    "minmaj7": [0, 3, 7, 11],
    "aug7":  [0, 4, 8, 10],
}

EXTENDED_INTERVALS = {
    "maj9":  [0, 4, 7, 11, 14],
    "m9":    [0, 3, 7, 10, 14],
    "9":     [0, 4, 7, 10, 14],
    "add9":  [0, 4, 7, 14],
    "madd9": [0, 3, 7, 14],
    "11":    [0, 4, 7, 10, 14, 17],
    "m11":   [0, 3, 7, 10, 14, 17],
}

ALL_CHORD_INTERVALS = {**TRIAD_INTERVALS, **SEVENTH_INTERVALS, **EXTENDED_INTERVALS}

# Human-readable display symbols
QUALITY_DISPLAY = {
    "maj": "",    "min": "m",   "dim": "°",   "aug": "+",
    "sus2": "sus2", "sus4": "sus4",
    "maj7": "maj7", "7": "7",   "min7": "m7", "m7b5": "ø7",
    "dim7": "°7",  "minmaj7": "mM7", "aug7": "+7",
    "maj9": "maj9", "m9": "m9", "9": "9",     "add9": "add9",
    "madd9": "madd9", "11": "11", "m11": "m11",
}

# Harmonic function taxonomy
FUNCTION_LABELS = {
    "tonic": "T", "predominant": "PD", "dominant": "D",
    "color": "C", "passing": "P",
}

# ---------------------------------------------------------------------------
# Scale builder
# ---------------------------------------------------------------------------

def build_scale(root: str, scale_name: str) -> List[str]:
    """Return ordered list of note names in the scale."""
    intervals = SCALE_INTERVALS[scale_name]
    root_pc   = note_to_pc(root)
    prefer_flat = root in ["F", "Bb", "Eb", "Ab", "Db", "Gb"]
    return [pc_to_note((root_pc + i) % 12, prefer_flat) for i in intervals]

# ---------------------------------------------------------------------------
# Diatonic chord factory
# ---------------------------------------------------------------------------

def _diatonic_quality(scale_intervals: List[int], degree: int) -> str:
    """Determine triad quality for scale degree (0-indexed)."""
    n = len(scale_intervals)
    root = scale_intervals[degree]
    third = scale_intervals[(degree + 2) % n] - root
    fifth = scale_intervals[(degree + 4) % n] - root
    # Wrap negatives
    third = third % 12
    fifth = fifth % 12
    if third == 4 and fifth == 7:  return "maj"
    if third == 3 and fifth == 7:  return "min"
    if third == 3 and fifth == 6:  return "dim"
    if third == 4 and fifth == 8:  return "aug"
    return "maj"  # fallback

def _diatonic_seventh_quality(scale_intervals: List[int], degree: int) -> str:
    n = len(scale_intervals)
    root  = scale_intervals[degree]
    third = (scale_intervals[(degree + 2) % n] - root) % 12
    fifth = (scale_intervals[(degree + 4) % n] - root) % 12
    sev   = (scale_intervals[(degree + 6) % n] - root) % 12
    if third == 4 and fifth == 7 and sev == 11: return "maj7"
    if third == 4 and fifth == 7 and sev == 10: return "7"
    if third == 3 and fifth == 7 and sev == 10: return "min7"
    if third == 3 and fifth == 6 and sev == 10: return "m7b5"
    if third == 3 and fifth == 6 and sev == 9:  return "dim7"
    if third == 3 and fifth == 7 and sev == 11: return "minmaj7"
    return "min7"

# ---------------------------------------------------------------------------
# Chord data class
# ---------------------------------------------------------------------------

@dataclass
class Chord:
    root: str                       # e.g. "G"
    quality: str                    # e.g. "min7"
    bass: Optional[str] = None      # slash bass, e.g. "E" for Em7/E (first inv)
    degree: Optional[int] = None    # 0-indexed scale degree
    function: str = "color"         # tonic / predominant / dominant / color / passing
    notes: List[int] = field(default_factory=list)   # MIDI note numbers (C4=60)
    bass_note: int = 0              # MIDI note for bass track
    label: str = ""                 # display label e.g. "Am7"
    borrowed: bool = False
    secondary_target: Optional[str] = None  # e.g. "V" if this is V/V

    def __post_init__(self):
        if not self.notes:
            self.notes = self._build_notes()
        if not self.label:
            self.label = self._make_label()
        if not self.bass_note:
            b = self.bass if self.bass else self.root
            self.bass_note = note_to_pc(b) + 48  # Bass octave C3

    def _build_notes(self) -> List[int]:
        root_pc = note_to_pc(self.root)
        intervals = ALL_CHORD_INTERVALS.get(self.quality, TRIAD_INTERVALS["maj"])
        base_octave = 60  # C4
        notes = []
        for i in intervals:
            midi = base_octave + root_pc + i
            # Keep chord in reasonable range (60-84)
            while midi < 60: midi += 12
            while midi > 84: midi -= 12
            notes.append(midi)
        return sorted(set(notes))

    def _make_label(self) -> str:
        sym = QUALITY_DISPLAY.get(self.quality, self.quality)
        label = f"{self.root}{sym}"
        if self.bass and self.bass != self.root:
            label += f"/{self.bass}"
        return label

    def pc_set(self) -> set:
        """Return pitch class set (0-11) of chord tones."""
        return {n % 12 for n in self.notes}


# ---------------------------------------------------------------------------
# Harmonic function assignment
# ---------------------------------------------------------------------------

# Degree → function for common scales (0-indexed)
DEGREE_FUNCTION = {
    "Major":             {0:"tonic",1:"color",2:"predominant",3:"tonic",
                          4:"predominant",5:"dominant",6:"passing"},
    "Natural Minor":     {0:"tonic",1:"passing",2:"predominant",3:"tonic",
                          4:"dominant",5:"predominant",6:"dominant"},
    "Harmonic Minor":    {0:"tonic",1:"passing",2:"predominant",3:"tonic",
                          4:"dominant",5:"predominant",6:"dominant"},
    "Dorian":            {0:"tonic",1:"predominant",2:"color",3:"predominant",
                          4:"dominant",5:"color",6:"passing"},
    "Phrygian Dominant": {0:"tonic",1:"dominant",2:"color",3:"predominant",
                          4:"color",5:"predominant",6:"passing"},
    "Hijaz":             {0:"tonic",1:"dominant",2:"color",3:"predominant",
                          4:"color",5:"predominant",6:"passing"},
}

def assign_function(degree: int, scale_name: str) -> str:
    mapping = DEGREE_FUNCTION.get(scale_name, DEGREE_FUNCTION["Major"])
    return mapping.get(degree, "color")

# ---------------------------------------------------------------------------
# Full diatonic palette builder
# ---------------------------------------------------------------------------

def build_diatonic_chords(root: str, scale_name: str, complexity: str = "Medium") -> List[Chord]:
    """
    Return list of Chord objects covering triads, 7ths, and (if advanced) extensions
    for every scale degree plus borrowed chords and secondary dominants.
    """
    scale_notes = build_scale(root, scale_name)
    scale_intervals = SCALE_INTERVALS[scale_name]
    n = len(scale_notes)
    chords: List[Chord] = []

    for deg in range(n):
        note = scale_notes[deg]
        triad_q   = _diatonic_quality(scale_intervals, deg)
        seventh_q = _diatonic_seventh_quality(scale_intervals, deg)
        func      = assign_function(deg, scale_name)

        # Always include triad
        chords.append(Chord(root=note, quality=triad_q, degree=deg, function=func))

        # Medium+ adds 7ths
        if complexity in ("Medium", "Advanced"):
            chords.append(Chord(root=note, quality=seventh_q, degree=deg, function=func))

        # Advanced adds extensions + sus chords
        if complexity == "Advanced":
            if triad_q == "maj":
                chords.append(Chord(root=note, quality="maj9", degree=deg, function=func))
                chords.append(Chord(root=note, quality="add9", degree=deg, function=func))
            elif triad_q == "min":
                chords.append(Chord(root=note, quality="m9", degree=deg, function=func))
                chords.append(Chord(root=note, quality="madd9", degree=deg, function=func))
            elif seventh_q == "7":
                chords.append(Chord(root=note, quality="9", degree=deg, function=func))
            # Sus chords on degrees that work well
            if deg in (0, 3, 4):
                chords.append(Chord(root=note, quality="sus4", degree=deg, function=func))
                chords.append(Chord(root=note, quality="sus2", degree=deg, function=func))

    # Add borrowed chords (parallel minor/major)
    chords.extend(_borrowed_chords(root, scale_name, complexity))

    # Add secondary dominants
    chords.extend(_secondary_dominants(root, scale_name, complexity))

    # Add slash chords for smooth bass motion
    chords.extend(_slash_chords(chords[:n]))  # only from primary triads

    return chords


def _borrowed_chords(root: str, scale_name: str, complexity: str) -> List[Chord]:
    """Borrow from parallel mode."""
    borrowed: List[Chord] = []
    if scale_name == "Major":
        # Borrow from natural minor: bVII, bIII, bVI, iv
        parallel_scale = build_scale(root, "Natural Minor")
        borrow_degrees = {2: "min", 5: "maj", 6: "maj", 3: "min"}  # bIII, bVI, bVII, iv
        for deg, quality in borrow_degrees.items():
            note = parallel_scale[deg]
            c = Chord(root=note, quality=quality, function="color", borrowed=True)
            borrowed.append(c)
            if complexity == "Advanced":
                q7 = "min7" if quality == "min" else "maj7"
                borrowed.append(Chord(root=note, quality=q7, function="color", borrowed=True))
    elif scale_name in ("Natural Minor", "Dorian"):
        # Borrow V (major) from harmonic minor
        dom_note = transpose(root, 7)
        borrowed.append(Chord(root=dom_note, quality="maj", function="dominant", borrowed=True))
        if complexity in ("Medium", "Advanced"):
            borrowed.append(Chord(root=dom_note, quality="7", function="dominant", borrowed=True))
    return borrowed


def _secondary_dominants(root: str, scale_name: str, complexity: str) -> List[Chord]:
    """V7/x chords resolving to diatonic targets."""
    if complexity == "Simple":
        return []
    scale_notes = build_scale(root, scale_name)
    secondaries: List[Chord] = []
    # Build V7 a perfect 5th above each diatonic degree
    targets = [1, 2, 3, 4, 5] if complexity == "Advanced" else [4, 5]  # V/IV, V/V mostly
    for deg in targets:
        target_note = scale_notes[deg % len(scale_notes)]
        dom_note = transpose(target_note, 7)  # a P5 above target
        c = Chord(
            root=dom_note, quality="7", function="dominant",
            secondary_target=f"deg{deg}"
        )
        secondaries.append(c)
    return secondaries


def _slash_chords(primary_chords: List[Chord]) -> List[Chord]:
    """First and second inversions of primary triads as slash chords."""
    slash: List[Chord] = []
    for ch in primary_chords:
        if ch.quality not in ("maj", "min"):
            continue
        intervals = TRIAD_INTERVALS[ch.quality]
        # First inversion: bass = 3rd
        third_pc = (note_to_pc(ch.root) + intervals[1]) % 12
        third_note = pc_to_note(third_pc)
        slash.append(Chord(root=ch.root, quality=ch.quality, bass=third_note,
                           function=ch.function, degree=ch.degree))
        # Second inversion: bass = 5th
        fifth_pc = (note_to_pc(ch.root) + intervals[2]) % 12
        fifth_note = pc_to_note(fifth_pc)
        slash.append(Chord(root=ch.root, quality=ch.quality, bass=fifth_note,
                           function=ch.function, degree=ch.degree))
    return slash


# ---------------------------------------------------------------------------
# Voice leading helpers
# ---------------------------------------------------------------------------

def voice_leading_score(chord_a: Chord, chord_b: Chord) -> float:
    """
    0.0 (terrible) → 1.0 (excellent).
    Rewards common tones and small semitone movements.
    """
    if not chord_a.notes or not chord_b.notes:
        return 0.5
    pcs_a = chord_a.pc_set()
    pcs_b = chord_b.pc_set()
    common = len(pcs_a & pcs_b)
    total  = max(len(pcs_a), len(pcs_b))
    common_ratio = common / total

    # Smallest semitone move for each note in a to nearest in b
    moves = []
    for na in chord_a.notes:
        best = min(abs(na - nb) for nb in chord_b.notes)
        best = min(best, 12 - best)  # wrap octave
        moves.append(best)
    avg_move = sum(moves) / len(moves) if moves else 6.0
    movement_score = max(0.0, 1.0 - avg_move / 6.0)

    return 0.5 * common_ratio + 0.5 * movement_score


def bass_motion_score(chord_a: Chord, chord_b: Chord) -> float:
    """Rewards stepwise bass motion and perfect intervals; penalises tritone."""
    diff = abs(chord_a.bass_note - chord_b.bass_note) % 12
    if diff == 0:  return 0.3   # no motion
    if diff in (1, 2): return 1.0   # step
    if diff in (3, 4): return 0.8
    if diff in (5, 7): return 0.9   # 4th / 5th
    if diff == 6:      return 0.2   # tritone
    return 0.5
