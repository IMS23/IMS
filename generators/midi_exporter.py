"""
generators/midi_exporter.py
Multi-track MIDI export with strumming, humanization, dynamics.
BPM is properly written to tempo track.
"""
import random
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from typing import List, Tuple
from core.project import Project
from generators.bass_generator import generate_bass
from generators.melody_generator import generate_melody
from generators.arpeggio_generator import generate_arpeggio
from generators.drum_generator import generate_drums
from generators.drum_generator import generate_drums

NoteEvent = Tuple[int, int, int, int]  # start, dur, note, vel


def _humanize(tick, amount=6):
    return max(0, tick + random.randint(-amount, amount))

def _humanize_vel(vel, amount=10):
    return max(30, min(120, vel + random.randint(-amount, amount)))


def _chord_to_events(chord, start_tick, dur_ticks, style):
    """
    Convert a chord to note events with strumming and voice dynamics.
    Top note louder, strum direction depends on style.
    """
    events = []
    notes = sorted(chord.notes)
    if not notes:
        return events

    # Strum settings per style
    strum_settings = {
        "Pop":       (12, "up"),
        "R&B":       (20, "up"),
        "Lo-fi":     (25, "up"),
        "Cinematic": (8,  "up"),
        "Trap":      (0,  "up"),   # no strum
        "Persian":   (15, "up"),
    }
    strum_gap, direction = strum_settings.get(style, (10, "up"))

    if direction == "down":
        notes = list(reversed(notes))

    for i, note in enumerate(notes):
        strum_offset = i * strum_gap
        tick = _humanize(start_tick + strum_offset, 5)

        # Top note louder (melody note in chord)
        if i == len(notes) - 1:
            vel = _humanize_vel(82, 8)
        elif i == 0:
            vel = _humanize_vel(65, 8)
        else:
            vel = _humanize_vel(72, 10)

        # Slightly shorter notes for articulation
        note_dur = dur_ticks - strum_gap * len(notes) - random.randint(20, 60)
        note_dur = max(ppq_global // 4, note_dur)

        events.append((tick, note_dur, note, vel))

    return events

ppq_global = 480  # module-level for chord events


def _chord_track(progression, ppq, bars_per_chord, style):
    global ppq_global
    ppq_global = ppq
    ticks_per_chord = ppq * 4 * bars_per_chord
    events: List[NoteEvent] = []
    tick = 0
    for chord in progression:
        dur = ticks_per_chord - ppq // 8
        chord_events = _chord_to_events(chord, tick, dur, style)
        events.extend(chord_events)
        tick += ticks_per_chord
    return _events_to_track(events, channel=0, ppq=ppq)


def _events_to_track(events, channel, ppq):
    track = MidiTrack()
    msgs = []
    for start, dur, note, vel in events:
        if not (0 <= note <= 127): continue
        vel = max(1, min(127, vel))
        msgs.append((start,          Message("note_on",  channel=channel, note=note, velocity=vel,   time=0)))
        msgs.append((start + dur,    Message("note_off", channel=channel, note=note, velocity=0,     time=0)))
    msgs.sort(key=lambda x: (x[0], 0 if x[1].type == "note_off" else 1))
    prev = 0
    for abs_tick, msg in msgs:
        msg.time = max(0, abs_tick - prev)
        prev = abs_tick
        track.append(msg)
    return track


def export_midi(project: Project, output_path: str, include_arpeggio: bool = True, include_drums: bool = True):
    random.seed(42)
    ppq  = 480
    prog = project.progression
    s    = project.settings

    if not prog:
        raise ValueError("No chords in progression.")

    mid = MidiFile(type=1, ticks_per_beat=ppq)

    # Track 0: Tempo — BPM properly applied
    tempo_track = MidiTrack()
    tempo_us = mido.bpm2tempo(s.bpm)
    tempo_track.append(MetaMessage("set_tempo",      tempo=tempo_us, time=0))
    tempo_track.append(MetaMessage("time_signature", numerator=4, denominator=4,
                                   clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))
    tempo_track.append(MetaMessage("track_name", name=f"Tempo {s.bpm}BPM", time=0))
    mid.tracks.append(tempo_track)

    # Track 1: Chords (with strumming + humanization)
    chord_trk = _chord_track(prog, ppq, s.bars_per_chord, s.style)
    chord_trk.insert(0, MetaMessage("track_name", name="Chords", time=0))
    mid.tracks.append(chord_trk)

    # Track 2: Bass (style-aware)
    bass_events = generate_bass(prog, s.style, s.bpm, ppq, s.bars_per_chord)
    bass_trk = _events_to_track(bass_events, channel=1, ppq=ppq)
    bass_trk.insert(0, MetaMessage("track_name", name="Bass", time=0))
    mid.tracks.append(bass_trk)

    # Track 3: Melody (phrase-aware, swing, humanized)
    melody_events = generate_melody(prog, s.root, s.scale, s.style,
                                    ppq=ppq, bars_per_chord=s.bars_per_chord)
    melody_trk = _events_to_track(melody_events, channel=2, ppq=ppq)
    melody_trk.insert(0, MetaMessage("track_name", name="Melody", time=0))
    mid.tracks.append(melody_trk)

    # Track 4: Arpeggio
    if include_arpeggio:
        arp_events = generate_arpeggio(prog, s.style, ppq=ppq, bars_per_chord=s.bars_per_chord)
        arp_trk = _events_to_track(arp_events, channel=3, ppq=ppq)
        arp_trk.insert(0, MetaMessage("track_name", name="Arpeggio", time=0))
        mid.tracks.append(arp_trk)

    # Tracks 5-8: Drums — each element on its own track (all channel 9)
    if include_drums:
        # Map drum pattern selection to style override
        drum_style = s.style
        if hasattr(s, 'drum_pattern') and s.drum_pattern and s.drum_pattern != "Auto (match style)":
            pat = s.drum_pattern
            if pat.startswith("Pop"): drum_style = "Pop"
            elif pat.startswith("R&B"): drum_style = "R&B"
            elif pat.startswith("Lo-fi"): drum_style = "Lo-fi"
            elif pat.startswith("Cinematic"): drum_style = "Cinematic"
            elif pat.startswith("Trap"): drum_style = "Trap"
            elif pat.startswith("Persian"): drum_style = "Persian"
        drum_groups = generate_drums(prog, drum_style, ppq=ppq, bars_per_chord=s.bars_per_chord)
        track_order = ["Kick", "Snare", "HiHat", "Percussion"]
        for group_name in track_order:
            events = drum_groups.get(group_name, [])
            if events:
                trk = _events_to_track(events, channel=9, ppq=ppq)
                trk.insert(0, MetaMessage("track_name", name=f"Drums - {group_name}", time=0))
                mid.tracks.append(trk)

    # Tracks 5-8: Drums — each element on its own track (all channel 9)
    if include_drums:
        # Map drum pattern selection to style override
        drum_style = s.style
        if hasattr(s, 'drum_pattern') and s.drum_pattern and s.drum_pattern != "Auto (match style)":
            pat = s.drum_pattern
            if pat.startswith("Pop"): drum_style = "Pop"
            elif pat.startswith("R&B"): drum_style = "R&B"
            elif pat.startswith("Lo-fi"): drum_style = "Lo-fi"
            elif pat.startswith("Cinematic"): drum_style = "Cinematic"
            elif pat.startswith("Trap"): drum_style = "Trap"
            elif pat.startswith("Persian"): drum_style = "Persian"
        drum_groups = generate_drums(prog, drum_style, ppq=ppq, bars_per_chord=s.bars_per_chord)
        track_order = ["Kick", "Snare", "HiHat", "Percussion"]
        for group_name in track_order:
            events = drum_groups.get(group_name, [])
            if events:
                trk = _events_to_track(events, channel=9, ppq=ppq)
                trk.insert(0, MetaMessage("track_name", name=f"Drums - {group_name}", time=0))
                mid.tracks.append(trk)

    mid.save(output_path)
    print(f"[MIDI] Exported {len(mid.tracks)} tracks → {output_path}  BPM={s.bpm}")
