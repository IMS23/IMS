"""
generators/audio_preview.py
============================
Plays chord/note preview sounds directly inside the app using
Python's built-in ctypes to call Windows WinMM MIDI API.
No external libraries needed — works on any Windows system.
Falls back to a simple beep on non-Windows.
"""

import sys
import threading
import time
from typing import List


# ---------------------------------------------------------------------------
# Windows MIDI via ctypes (winmm.dll) — no dependencies
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    import ctypes
    _winmm = ctypes.windll.winmm

    def _midi_out_open():
        handle = ctypes.c_ulong(0)
        # MIDI_MAPPER = -1 (0xFFFFFFFF as uint)
        _winmm.midiOutOpen(ctypes.byref(handle), ctypes.c_uint(-1), 0, 0, 0)
        return handle.value

    def _midi_out_close(handle):
        _winmm.midiOutClose(handle)

    def _midi_out_short_msg(handle, msg):
        _winmm.midiOutShortMsg(handle, ctypes.c_ulong(msg))

    def _build_msg(status, data1, data2):
        return status | (data1 << 8) | (data2 << 16)

    def _play_notes_windows(notes: List[int], velocity: int, duration_ms: int,
                             program: int = 0):
        """Play a chord using Windows MIDI out."""
        try:
            handle = _midi_out_open()
            # Set instrument (program change on channel 0)
            _midi_out_short_msg(handle, _build_msg(0xC0, program, 0))
            # Note ON
            for note in notes:
                _midi_out_short_msg(handle, _build_msg(0x90, note, velocity))
            time.sleep(duration_ms / 1000.0)
            # Note OFF
            for note in notes:
                _midi_out_short_msg(handle, _build_msg(0x80, note, 0))
            _midi_out_close(handle)
        except Exception as e:
            print(f"[Audio] MIDI error: {e}")


# ---------------------------------------------------------------------------
# Style → GM program number
# ---------------------------------------------------------------------------

STYLE_PROGRAMS = {
    "Pop":       0,    # Acoustic Grand Piano
    "R&B":       4,    # Electric Piano
    "Lo-fi":     4,    # Electric Piano
    "Cinematic": 48,   # String Ensemble
    "Trap":      0,    # Piano
    "Persian":   105,  # Sitar / Banjo area
}

STYLE_BASS_PROGRAMS = {
    "Pop":       32,   # Acoustic Bass
    "R&B":       33,   # Electric Bass
    "Lo-fi":     33,   # Electric Bass
    "Cinematic": 42,   # Cello
    "Trap":      38,   # Synth Bass
    "Persian":   32,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preview_chord(chord, style: str = "Pop", duration_ms: int = 1200):
    """
    Play a chord preview in a background thread.
    chord: core.theory.Chord object
    """
    if not chord.notes:
        return

    def _play():
        program = STYLE_PROGRAMS.get(style, 0)
        velocity = 85
        notes = chord.notes[:]

        if sys.platform == "win32":
            _play_notes_windows(notes, velocity, duration_ms, program)
        else:
            # Fallback: system beep (Linux/Mac)
            try:
                import os
                os.system("echo -e '\\a'")
            except:
                pass

    t = threading.Thread(target=_play, daemon=True)
    t.start()


def preview_single_note(midi_note: int, style: str = "Pop", duration_ms: int = 600):
    """Play a single MIDI note preview."""
    def _play():
        program = STYLE_PROGRAMS.get(style, 0)
        if sys.platform == "win32":
            _play_notes_windows([midi_note], 90, duration_ms, program)
    threading.Thread(target=_play, daemon=True).start()
