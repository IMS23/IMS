"""
generators/bass_generator.py
Style-aware bass generator with humanization, passing notes, syncopation.
"""
import random
from typing import List, Tuple
from core.theory import Chord, note_to_pc, ALL_CHORD_INTERVALS

BassEvent = Tuple[int, int, int, int]  # start, dur, note, vel

def _pc(chord: Chord) -> int:
    b = chord.bass if chord.bass else chord.root
    return note_to_pc(b)

def _root_midi(chord: Chord, octave: int = 2) -> int:
    midi = _pc(chord) + 12 * (octave + 1)
    while midi < 28: midi += 12
    while midi > 50: midi -= 12
    return midi

def _humanize(tick: int, amount: int = 8) -> int:
    return tick + random.randint(-amount, amount)

def _humanize_vel(base: int, amount: int = 12) -> int:
    return max(40, min(120, base + random.randint(-amount, amount)))

def generate_bass(progression, style, bpm=90, ppq=480, bars_per_chord=2) -> List[BassEvent]:
    random.seed(42)
    dispatch = {
        "Pop":       _pop_bass,
        "R&B":       _rnb_bass,
        "Lo-fi":     _lofi_bass,
        "Cinematic": _cinematic_bass,
        "Trap":      _trap_bass,
        "Persian":   _persian_bass,
    }
    fn = dispatch.get(style, _pop_bass)
    ticks_per_bar = ppq * 4
    ticks_per_chord = ticks_per_bar * bars_per_chord
    events: List[BassEvent] = []
    tick = 0
    for i, chord in enumerate(progression):
        next_chord = progression[i + 1] if i + 1 < len(progression) else progression[0]
        events.extend(fn(chord, next_chord, tick, ticks_per_chord, ppq))
        tick += ticks_per_chord
    return events


def _pop_bass(chord, next_chord, start, dur, ppq):
    """Root on 1, 5th on 3, passing note before next chord."""
    events = []
    root = _root_midi(chord)
    intervals = ALL_CHORD_INTERVALS.get(chord.quality, [0,4,7])
    fifth = _pc(chord) + (intervals[2] if len(intervals)>2 else 7)
    fifth_midi = (fifth % 12) + (root // 12) * 12
    if fifth_midi < root: fifth_midi += 12

    beat = ppq
    # Beat 1 - root strong
    events.append((_humanize(start,4), int(beat*1.8), root, _humanize_vel(95,8)))
    # Beat 2 - ghost note
    events.append((_humanize(start+beat,6), beat//2, root, _humanize_vel(55,10)))
    # Beat 3 - fifth
    events.append((_humanize(start+beat*2,4), int(beat*1.8), fifth_midi, _humanize_vel(85,8)))
    # Beat 4 - approach to next chord (chromatic)
    next_root = _root_midi(next_chord)
    approach = next_root - 1 if next_root > root else next_root + 1
    events.append((_humanize(start+beat*3,5), beat-20, approach, _humanize_vel(70,10)))
    return events


def _rnb_bass(chord, next_chord, start, dur, ppq):
    """Syncopated R&B bass with 16th note feel."""
    events = []
    root = _root_midi(chord)
    beat = ppq
    sixteenth = ppq // 4

    # Syncopated pattern: hit just before beats
    pattern = [
        (0,           int(beat*1.5), 95),
        (beat+sixteenth*3, beat//2, 65),  # syncopation
        (beat*2,      int(beat*1.5), 85),
        (beat*3+sixteenth, beat-30, 70),
    ]
    for offset, length, vel in pattern:
        events.append((_humanize(start+offset,6), length, root, _humanize_vel(vel,12)))
    return events


def _lofi_bass(chord, next_chord, start, dur, ppq):
    """Lo-fi: lazy, behind the beat, simple with swing feel."""
    events = []
    root = _root_midi(chord)
    beat = ppq
    swing = int(ppq * 0.08)  # slight swing delay

    # Laid-back: slightly behind beat
    lazy = int(ppq * 0.05)
    events.append((_humanize(start+lazy, 8), int(beat*2.5), root, _humanize_vel(80,15)))
    events.append((_humanize(start+beat*2+lazy+swing, 8), int(beat*1.8), root, _humanize_vel(70,15)))
    return events


def _cinematic_bass(chord, next_chord, start, dur, ppq):
    """Long sustained notes with swell, octave movement."""
    events = []
    root_low  = _root_midi(chord, octave=1)  # very low
    root_high = root_low + 12
    half = dur // 2

    events.append((_humanize(start,3), half-10, root_low,  _humanize_vel(90,6)))
    events.append((_humanize(start+half,3), half-10, root_high, _humanize_vel(75,6)))
    return events


def _trap_bass(chord, next_chord, start, dur, ppq):
    """808-style: long root on 1, slide effect via velocity, ghost on 3."""
    events = []
    root = _root_midi(chord, octave=1)
    beat = ppq
    sixteenth = ppq // 4

    events.append((_humanize(start,3), int(beat*2.5), root, _humanize_vel(110,5)))
    # Ghost 808 hits
    events.append((_humanize(start+beat*2+sixteenth,4), beat//2, root, _humanize_vel(60,8)))
    events.append((_humanize(start+beat*3,4), beat, root, _humanize_vel(75,8)))
    return events


def _persian_bass(chord, next_chord, start, dur, ppq):
    """Persian: drone on root with ornamental approach."""
    events = []
    root = _root_midi(chord)
    beat = ppq
    next_root = _root_midi(next_chord)
    # Semitone above target (Hijaz characteristic approach)
    approach = next_root + 1

    events.append((_humanize(start,5), int(beat*2), root, _humanize_vel(90,8)))
    events.append((_humanize(start+beat*2,5), int(beat*1.5), root, _humanize_vel(80,8)))
    events.append((_humanize(start+int(beat*3.5),5), beat//2, approach, _humanize_vel(70,10)))
    return events
