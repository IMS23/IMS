"""
generators/melody_generator.py
Phrase-aware melody with humanization, swing, dynamics, rests, contour.
"""
import random
from typing import List, Tuple, Optional
from core.theory import Chord, note_to_pc, SCALE_INTERVALS

MelodyEvent = Tuple[int, int, int, int]

def _scale_notes(root, scale, low=60, high=79):
    root_pc = note_to_pc(root)
    intervals = SCALE_INTERVALS[scale]
    notes = []
    for oct in range(3, 8):
        for i in intervals:
            n = root_pc + i + oct * 12
            if low <= n <= high:
                notes.append(n)
    return sorted(set(notes))

def _chord_tones(chord, low=60, high=79):
    return [n for n in chord.notes if low <= n <= high] or chord.notes[:3]

def _humanize(tick, amount=10):
    return max(0, tick + random.randint(-amount, amount))

def _humanize_vel(base, amount=15):
    return max(35, min(118, base + random.randint(-amount, amount)))

def _nearest(note, candidates):
    return min(candidates, key=lambda c: abs(c - note))

def _step_toward(current, target, scale_notes):
    """Move stepwise toward target note."""
    candidates = [n for n in scale_notes if abs(n - current) <= 4]
    if not candidates:
        return current
    return min(candidates, key=lambda n: abs(n - target))


# ---------------------------------------------------------------------------
# Style-specific melody patterns
# ---------------------------------------------------------------------------

# Each pattern: list of (beat_offset_in_quarters, duration_quarters, is_strong, is_rest)
MELODY_PATTERNS = {
    "Pop": [
        # Bar 1
        (0, 1, True, False), (1, 0.5, False, False), (1.5, 0.5, False, False),
        (2, 1, True, False), (3, 1, False, False),
        # Bar 2
        (4, 1.5, True, False), (5.5, 0.5, False, False),
        (6, 1, True, False), (7, 1, False, True),  # rest at end
    ],
    "R&B": [
        (0, 0.75, True, False), (0.75, 0.25, False, False),
        (1, 0.5, False, True),  # rest
        (1.5, 0.5, False, False), (2, 1, True, False),
        (3, 0.25, False, False), (3.25, 0.25, False, False), (3.5, 0.5, False, False),
        (4, 1, True, False), (5, 0.5, False, False), (5.5, 0.5, False, True),
        (6, 1.5, True, False), (7.5, 0.5, False, False),
    ],
    "Lo-fi": [
        (0, 2, True, False), (2, 1, False, False),
        (3, 1, False, True),  # rest
        (4, 1.5, True, False), (5.5, 0.5, False, False),
        (6, 2, True, False),
    ],
    "Cinematic": [
        (0, 3, True, False), (3, 1, False, False),
        (4, 2, True, False), (6, 2, False, False),
    ],
    "Trap": [
        (0, 0.5, True, False), (0.5, 0.5, False, True),
        (1, 0.25, False, False), (1.25, 0.25, False, False), (1.5, 0.5, False, False),
        (2, 1, True, False), (3, 0.5, False, True),
        (3.5, 0.5, False, False),
        (4, 0.5, True, False), (4.5, 0.5, False, True),
        (5, 1, False, False), (6, 1, True, False), (7, 1, False, True),
    ],
    "Persian": [
        (0, 0.5, True, False), (0.5, 0.25, False, False), (0.75, 0.25, False, False),
        (1, 1, False, False), (2, 0.5, True, False), (2.5, 0.25, False, False),
        (2.75, 0.25, False, False), (3, 1, False, False),
        (4, 1.5, True, False), (5.5, 0.5, False, False),
        (6, 0.5, True, False), (6.5, 0.25, False, False), (6.75, 0.25, False, False),
        (7, 1, False, False),
    ],
}

SWING_AMOUNT = {
    "Lo-fi": 0.12,
    "R&B":   0.08,
    "Pop":   0.0,
    "Cinematic": 0.0,
    "Trap":  0.0,
    "Persian": 0.05,
}


def generate_melody(progression, root, scale, style, ppq=480,
                    bars_per_chord=2, low_midi=60, high_midi=76,
                    seed=None) -> List[MelodyEvent]:
    if seed is not None:
        random.seed(seed)
    else:
        random.seed(7)

    scale_tones  = _scale_notes(root, scale, low_midi, high_midi)
    if not scale_tones:
        scale_tones = _scale_notes(root, scale, 55, 82)

    ticks_per_bar   = ppq * 4
    ticks_per_chord = ticks_per_bar * bars_per_chord
    swing = SWING_AMOUNT.get(style, 0.0)
    pattern = MELODY_PATTERNS.get(style, MELODY_PATTERNS["Pop"])

    events: List[MelodyEvent] = []
    # Start at 5th scale degree for interest
    prev_note = scale_tones[len(scale_tones) * 2 // 3]

    # Phrase contour: rise in first half, peak at 2/3, fall at end
    total_chords = len(progression)

    for chord_idx, chord in enumerate(progression):
        chord_tones = _chord_tones(chord, low_midi, high_midi)
        chord_start = chord_idx * ticks_per_chord

        # Phrase position 0.0-1.0
        phrase_pos = chord_idx / max(total_chords - 1, 1)

        # Target note based on contour
        if phrase_pos < 0.5:
            # Rising: aim higher
            target = scale_tones[min(len(scale_tones)-1, int(len(scale_tones)*0.75))]
        elif phrase_pos < 0.75:
            # Peak
            target = scale_tones[min(len(scale_tones)-1, int(len(scale_tones)*0.85))]
        else:
            # Falling: aim for root area
            target = scale_tones[min(2, len(scale_tones)-1)]

        # How many bars does this chord span?
        bars_to_fill = bars_per_chord
        bar = 0
        while bar < bars_to_fill:
            bar_start = chord_start + bar * ticks_per_bar

            # Use motif in bar 0, variation in bar 1+
            use_pattern = pattern if bar == 0 else _vary_pattern(pattern, style)

            for beat_off, dur_beats, is_strong, is_rest in use_pattern:
                # Only fill current bar
                if beat_off >= 4 * (bar + 1) or beat_off < 4 * bar:
                    continue
                local_off = beat_off - 4 * bar

                tick = bar_start + int(local_off * ppq)

                # Apply swing to off-beats
                if swing > 0 and (local_off * 2) % 2 == 1:
                    tick += int(ppq * swing)

                dur_ticks = max(ppq // 4, int(dur_beats * ppq) - 20)

                if is_rest:
                    prev_note = prev_note  # hold position
                    continue

                # Choose note
                if is_strong:
                    # Strong beat: chord tone near target
                    candidates = chord_tones if chord_tones else scale_tones
                else:
                    candidates = scale_tones

                # Pick note close to prev but moving toward target
                close = [n for n in candidates if abs(n - prev_note) <= 5]
                toward = [n for n in (close or candidates) if
                          (target > prev_note and n >= prev_note) or
                          (target < prev_note and n <= prev_note) or
                          abs(n - prev_note) <= 2]
                pool = toward if toward else (close if close else candidates)
                note = random.choice(pool)

                # Velocity: strong beats louder, phrase peak louder
                base_vel = 88 if is_strong else 68
                if 0.4 < phrase_pos < 0.75:
                    base_vel += 8  # louder at peak
                if phrase_pos > 0.85:
                    base_vel -= 10  # quieter at end

                vel = _humanize_vel(base_vel, 12)
                tick_h = _humanize(tick, 8 if not is_strong else 4)

                events.append((tick_h, dur_ticks, note, vel))
                prev_note = note

            bar += 1

    return events


def _vary_pattern(pattern, style):
    """Create variation of pattern — different note lengths, occasional rests."""
    varied = []
    for beat_off, dur, strong, is_rest in pattern:
        # 20% chance to turn a weak note into a rest
        if not strong and not is_rest and random.random() < 0.2:
            varied.append((beat_off, dur, strong, True))
        # 15% chance to double a short note (two 8ths instead of one quarter)
        elif not strong and dur >= 0.5 and random.random() < 0.15:
            varied.append((beat_off, dur/2, strong, False))
            varied.append((beat_off + dur/2, dur/2, False, False))
        else:
            varied.append((beat_off, dur, strong, is_rest))
    return varied
