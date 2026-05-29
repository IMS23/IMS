"""
generators/arpeggio_generator.py
Style-aware arpeggio generator with:
- Multiple patterns per style
- Humanization
- Rhythm variation
- Phrase-aware dynamics
- No boring repetition
"""
import random
from typing import List, Tuple, Optional
from core.theory import Chord, note_to_pc, ALL_CHORD_INTERVALS

ArpEvent = Tuple[int, int, int, int]  # start, dur, note, vel

def _arp_notes(chord: Chord, low=55, high=88) -> List[int]:
    root_pc = note_to_pc(chord.root)
    intervals = ALL_CHORD_INTERVALS.get(chord.quality, [0, 4, 7])
    notes = []
    for octave_shift in (0, 12, 24):
        for i in intervals:
            n = root_pc + i + 48 + octave_shift
            if low <= n <= high:
                notes.append(n)
    return sorted(set(notes)) or [60]

def _h(tick, amt=8):
    return max(0, tick + random.randint(-amt, amt))

def _v(base, amt=12):
    return max(30, min(120, base + random.randint(-amt, amt)))


# ---------------------------------------------------------------------------
# Style-specific arp pattern generators
# Each returns list of (offset_ticks, dur_ticks, note_index, velocity)
# note_index is index into the arp_notes list (wraps around)
# ---------------------------------------------------------------------------

def _pop_arp(notes, ppq, bars):
    """Classic pop: up pattern with rhythm emphasis on beat 1."""
    events = []
    eighth = ppq // 2
    ticks = ppq * 4 * bars
    n = len(notes)
    t = 0
    i = 0
    while t < ticks - eighth:
        note = notes[i % n]
        # Accent every 4th note
        vel = _v(85 if i % 4 == 0 else 62, 10)
        dur = eighth - 10
        events.append((_h(t, 5), dur, note, vel))
        t += eighth
        i += 1
    return events


def _rnb_arp(notes, ppq, bars):
    """R&B: 16th note feel with syncopation and ghost notes."""
    events = []
    sixteenth = ppq // 4
    ticks = ppq * 4 * bars
    n = len(notes)
    # Syncopated rhythm pattern (1=play, 0=rest, g=ghost)
    rhythm = [1,0,1,1, 0,1,1,0, 1,0,1,1, 0,1,0,1]
    vel_map = [90,0,65,75, 0,70,65,0, 85,0,60,70, 0,65,0,60]
    t = 0
    bar_idx = 0
    i = 0
    while t < ticks - sixteenth:
        pos_in_bar = bar_idx % 16
        if rhythm[pos_in_bar]:
            note = notes[i % n]
            vel = _v(vel_map[pos_in_bar], 8)
            dur = sixteenth - 8 if vel_map[pos_in_bar] > 70 else sixteenth // 2
            events.append((_h(t, 6), dur, note, vel))
            i += 1
        t += sixteenth
        bar_idx += 1
    return events


def _lofi_arp(notes, ppq, bars):
    """Lo-fi: lazy, swung, sparse. Not every beat has a note."""
    events = []
    eighth = ppq // 2
    swing  = int(ppq * 0.10)
    ticks  = ppq * 4 * bars
    n = len(notes)
    # Sparse pattern: play ~60% of 8th notes
    pattern = [1,1,0,1, 1,0,1,1, 0,1,1,0, 1,0,1,1]
    t = 0
    bar_step = 0
    i = 0
    while t < ticks - eighth:
        pos = bar_step % 16
        if pattern[pos]:
            note = notes[i % n]
            # Swing: odd 8ths delayed
            offset = swing if (bar_step % 2 == 1) else 0
            vel = _v(68 if bar_step % 4 == 0 else 52, 14)
            dur = int(eighth * 0.85)
            events.append((_h(t + offset, 10), dur, note, vel))
            i += 1
        t += eighth
        bar_step += 1
    return events


def _cinematic_arp(notes, ppq, bars):
    """Cinematic: wide intervals, long notes, swell dynamics."""
    events = []
    ticks = ppq * 4 * bars
    n = len(notes)
    # Use only root, 5th, octave for wide cinematic feel
    wide_notes = []
    if len(notes) >= 3:
        wide_notes = [notes[0], notes[len(notes)//2], notes[-1]]
        if len(notes) > 3:
            wide_notes.append(notes[0] + 12 if notes[0]+12 <= 88 else notes[0])
    else:
        wide_notes = notes

    # Quarter note pattern with swell
    quarter = ppq
    t = 0
    i = 0
    total_steps = (ticks // quarter)
    while t < ticks - quarter:
        note = wide_notes[i % len(wide_notes)]
        # Swell: louder in middle of phrase
        phrase_pos = t / ticks
        base_vel = 55 + int(40 * (1 - abs(2*phrase_pos - 1)))
        vel = _v(base_vel, 8)
        dur = int(quarter * 1.8)  # slightly overlapping
        events.append((_h(t, 4), dur, note, vel))
        t += quarter
        i += 1
    return events


def _trap_arp(notes, ppq, bars):
    """Trap: hi-hat style rapid 16ths with occasional rests, triplet feel."""
    events = []
    sixteenth = ppq // 4
    ticks = ppq * 4 * bars
    n = len(notes)
    # Trap pattern: some 16ths, some rests, some doubles
    pattern = [1,1,0,1, 1,0,1,0, 1,1,0,1, 0,1,1,0,
               1,0,1,1, 0,1,0,1, 1,1,0,0, 1,0,1,1]
    t = 0
    step = 0
    i = 0
    while t < ticks - sixteenth:
        pos = step % len(pattern)
        if pattern[pos]:
            note = notes[i % n]
            # Trap: higher notes for hi-hat effect
            if i % 3 == 0:
                note = min(note + 12, 88)
            vel = _v(80 if step % 4 == 0 else 55, 12)
            dur = sixteenth - 5
            events.append((_h(t, 4), dur, note, vel))
            i += 1
        t += sixteenth
        step += 1
    return events


def _persian_arp(notes, ppq, bars):
    """Persian: ornamental runs, triplet feel, chromatic approaches."""
    events = []
    ticks = ppq * 4 * bars
    n = len(notes)
    triplet = ppq // 3
    eighth  = ppq // 2

    # Alternating triplets and eighths for middle-eastern feel
    pattern_beats = [
        (0,       triplet, 0),
        (triplet, triplet, 1),
        (triplet*2, triplet, 2),
        (ppq,     eighth,  1),
        (ppq+eighth, eighth, 0),
        (ppq*2,   triplet, 2),
        (ppq*2+triplet, triplet, 1),
        (ppq*2+triplet*2, triplet, 0),
        (ppq*3,   eighth,  2),
        (ppq*3+eighth, eighth, 1),
    ]
    t = 0
    bar_count = 0
    while t < ticks - ppq:
        for offset, dur, idx in pattern_beats:
            tick = t + offset
            if tick >= ticks: break
            note = notes[(bar_count + idx) % n]
            vel = _v(80 if idx == 0 else 65, 12)
            events.append((_h(tick, 7), dur - 8, note, vel))
        t += ppq * 4
        bar_count += 1
    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

STYLE_FN = {
    "Pop":       _pop_arp,
    "R&B":       _rnb_arp,
    "Lo-fi":     _lofi_arp,
    "Cinematic": _cinematic_arp,
    "Trap":      _trap_arp,
    "Persian":   _persian_arp,
}


def generate_arpeggio(
    progression: List[Chord],
    style: str,
    ppq: int = 480,
    bars_per_chord: int = 2,
    seed: Optional[int] = None,
) -> List[ArpEvent]:
    if seed is not None:
        random.seed(seed)
    else:
        random.seed(13)

    fn = STYLE_FN.get(style, _pop_arp)
    ticks_per_chord = ppq * 4 * bars_per_chord
    events: List[ArpEvent] = []
    tick = 0

    for chord_idx, chord in enumerate(progression):
        notes = _arp_notes(chord)
        # Alternate direction every chord for variety
        if chord_idx % 3 == 1:
            notes = list(reversed(notes))
        elif chord_idx % 3 == 2:
            # Up-down
            notes = notes + list(reversed(notes[1:-1]))

        chord_events = fn(notes, ppq, bars_per_chord)

        # Shift to absolute ticks
        for (start, dur, note, vel) in chord_events:
            abs_tick = tick + start
            if abs_tick < tick + ticks_per_chord:
                events.append((abs_tick, dur, note, vel))

        tick += ticks_per_chord

    return events
