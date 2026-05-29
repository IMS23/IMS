"""
generators/drum_generator.py  — Professional Drum Engine v2
══════════════════════════════════════════════════════════
Features:
  • 6 styles × 3 pattern variants each
  • 4 time signatures: 4/4, 3/4, 6/8, 5/4
  • Ghost notes on snare
  • Accents on strong beats
  • 6 fill types (triggered every N chords)
  • Humanization: timing ±8 ticks, velocity ±12
  • Swing for Lo-fi / R&B
  • Each element → separate MIDI track
    Kick / Snare / HiHat / Percussion
"""

import random
from typing import List, Tuple, Dict, Optional
from core.theory import Chord

DrumEvent = Tuple[int, int, int, int]   # (start, dur, note, vel)

# ─── GM Drum Map ──────────────────────────────────────────────
KICK   = 36;  RIM    = 37;  SNARE  = 38;  CLAP   = 39
SNARE2 = 40;  LF_TOM = 41;  HH_CL  = 42;  LO_TOM = 43
HH_HALF= 44;  MID_TOM= 45;  HH_OP  = 46;  HF_TOM = 47
HI_TOM = 48;  CRASH  = 49;  RIDE   = 51;  RIDE_B = 53
TAMB   = 54;  COWBELL= 56;  SHAKER = 82

DRUM_GROUPS = {
    "Kick":       {KICK},
    "Snare":      {SNARE, CLAP, SNARE2, RIM},
    "HiHat":      {HH_CL, HH_HALF, HH_OP},
    "Percussion": {LO_TOM, MID_TOM, HI_TOM, LF_TOM, HF_TOM,
                   CRASH, RIDE, RIDE_B, TAMB, COWBELL, SHAKER},
}
def _grp(n):
    for g,s in DRUM_GROUPS.items():
        if n in s: return g
    return "Percussion"

def _h(t, a=8):   return max(0, t + random.randint(-a, a))
def _v(b, a=12):  return max(20, min(127, b + random.randint(-a, a)))

# ─── Step sequencer ───────────────────────────────────────────
def _seq(pat: Dict[int, List[int]], ppq, bars,
         steps_per_bar=16, swing=0.0, offset=0):
    events = []
    step_t = (ppq * 4) // steps_per_bar
    for bar in range(bars):
        for step in range(steps_per_bar):
            t = offset + bar * ppq * 4 + step * step_t
            if swing > 0 and step % 2 == 1:
                t += int(ppq * swing)
            for note, vels in pat.items():
                vel = vels[step % len(vels)]
                if vel > 0:
                    events.append((_h(t,6), max(10, step_t-8), note, _v(vel,10)))
    return events

# ═══════════════════════════════════════════════════════════════
#  PATTERN LIBRARY
#  Each function returns {"Kick":[], "Snare":[], "HiHat":[], "Percussion":[]}
# ═══════════════════════════════════════════════════════════════

# ── POP ────────────────────────────────────────────────────────
_POP_KICK = [
    [100,0,0,0, 0,0,0,0, 100,0,0,0, 0,0,0,0],   # A: basic 4-on-floor
    [100,0,0,0, 0,0,0,80, 100,0,0,0, 0,0,80,0],  # B: +anticipation
    [100,0,0,75,0,0,0,0,  100,0,0,0, 75,0,0,80], # C: busier
]
_POP_SNARE = [
    [0,0,0,0, 90,0,0,0,  0,0,0,0,  90,0,0,0],                  # A
    [0,0,0,0, 90,0,0,30, 0,0,0,0,  90,0,30,0],                  # B +ghost
    [0,0,30,0,90,0,30,0, 0,30,0,0, 90,0,0,30],                  # C more ghost
]
_POP_HH = [
    ({HH_CL:[70,0,70,0]*4,   HH_OP:[0,0,0,0,0,0,65,0]*2}),     # A 8ths
    ({HH_CL:[70,55,70,55]*4, HH_OP:[0,0,65,0]*4}),              # B 16ths
    ({HH_CL:[65,55,70,55,65,0,70,55]*2, HH_OP:[0,0,0,60]*4}),  # C open+skip
]

def _pop(ppq, bars, v=0):
    k = _seq({KICK: _POP_KICK[v%3]}, ppq, bars)
    s = _seq({SNARE:_POP_SNARE[v%3]}, ppq, bars)
    h = _seq(_POP_HH[v%3], ppq, bars)
    p = []
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":p}

# ── R&B ────────────────────────────────────────────────────────
_RNB_KICK = [
    [100,0,0,0, 0,0,75,0,  0,0,100,0, 0,75,0,0],
    [100,0,0,75,0,0,0,0,   0,100,0,0, 75,0,0,0],
    [100,0,75,0,0,0,0,75,  100,0,0,0, 0,0,75,0],
]
_RNB_SNARE = [
    [0,0,0,0, 85,0,0,30, 0,0,0,0,  85,0,30,0],
    [0,0,0,0, 85,0,30,0, 0,30,0,0, 85,0,0,30],
    [0,30,0,0,85,0,0,30, 30,0,0,0, 85,30,0,0],
]

def _rnb(ppq, bars, v=0):
    k = _seq({KICK:_RNB_KICK[v%3]}, ppq, bars)
    s = _seq({SNARE:_RNB_SNARE[v%3], RIM:[0,25,0,0]*4}, ppq, bars)
    h = _seq({HH_CL:[65,55,65,55]*4, HH_OP:[0,0,0,0,0,0,60,0]*2}, ppq, bars)
    p = _seq({SHAKER:[40,0,40,0]*4}, ppq, bars)
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":p}

# ── LO-FI ──────────────────────────────────────────────────────
_LOFI_KICK = [
    [95,0,0,0, 0,0,0,0, 0,0,85,0, 0,0,0,0],
    [95,0,0,0, 0,0,85,0, 0,0,0,0, 80,0,0,0],
    [95,0,0,0, 0,85,0,0, 0,0,95,0, 0,0,80,0],
]
_LOFI_SNARE = [
    [0,0,0,0, 80,0,0,0,  0,0,0,0,  75,0,0,25],
    [0,0,0,0, 80,0,0,25, 0,0,0,0,  75,0,25,0],
    [0,0,25,0,80,0,0,0,  25,0,0,0, 75,0,0,25],
]

def _lofi(ppq, bars, v=0, sw=0.13):
    k = _seq({KICK:_LOFI_KICK[v%3]}, ppq, bars, swing=sw)
    s = _seq({SNARE:_LOFI_SNARE[v%3], RIM:[0,0,0,28,0,0,0,0]*2}, ppq, bars, swing=sw)
    h = _seq({HH_CL:[58,0,52,0,0,0,52,0]*2, HH_OP:[0,0,0,0,0,52,0,0]*2}, ppq, bars, swing=sw)
    p = _seq({SHAKER:[0,32,0,32]*4}, ppq, bars, swing=sw)
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":p}

# ── TRAP ───────────────────────────────────────────────────────
_TRAP_KICK = [
    [100,0,0,0, 0,0,0,80, 0,0,95,0, 0,0,75,0],
    [100,0,0,0, 0,0,80,0, 0,95,0,0, 75,0,0,80],
    [100,0,0,80,0,0,0,0,  95,0,0,0, 0,75,0,0],
]
_TRAP_HH = [
    {HH_CL:[75,60,70,60,75,0,65,70,75,60,0,65,70,65,75,0],
     HH_OP:[0,0,0,0,0,0,55,0,0,0,0,0,0,55,0,0]},
    {HH_CL:[75,65,70,65,0,70,65,70,75,0,65,70,65,75,0,65],
     HH_OP:[0,0,0,0,0,55,0,0,0,0,0,55,0,0,0,0]},
    {HH_CL:[75,60,65,70,75,60,65,0,70,75,60,65,70,0,75,60],
     HH_OP:[0,0,0,55,0,0,55,0,0,0,55,0,0,55,0,0]},
]

def _trap(ppq, bars, v=0):
    k = _seq({KICK:_TRAP_KICK[v%3]}, ppq, bars)
    s = _seq({CLAP: [0,0,0,0,95,0,0,0,0,0,0,0,90,0,0,0],
              SNARE:[0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0]}, ppq, bars)
    h = _seq(_TRAP_HH[v%3], ppq, bars)
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":[]}

# ── CINEMATIC ──────────────────────────────────────────────────
def _cinematic(ppq, bars, v=0, chord_idx=0, total=1):
    pp = chord_idx / max(total-1, 1)
    beat = ppq
    k,s,h,p = [],[],[],[]

    # Kick builds with phrase
    k.append((_h(0,4), beat-20, KICK, _v(112,5)))
    if pp > 0.25: k.append((_h(beat*2,4), beat-20, KICK, _v(98,7)))
    if pp > 0.55: k.append((_h(beat*3,4), beat//2, KICK, _v(88,8)))

    # Snare from mid-phrase
    if pp > 0.35: s.append((_h(beat*2,4), beat-20, SNARE, _v(100,7)))
    if pp > 0.60: s.append((_h(beat,4), beat//2, SNARE, _v(72,10)))

    # HiHat density increases
    if   pp < 0.20: h = _seq({RIDE:[0,0,48,0]*4}, ppq, bars)
    elif pp < 0.50: h = _seq({RIDE:[52,0,48,0]*4, HH_HALF:[0,0,0,0,42,0,0,0]*2}, ppq, bars)
    else:           h = _seq({RIDE:[58,0,52,0]*4, HH_OP:[0,0,0,58,0,0,58,0]*2}, ppq, bars)

    # Crash at section starts
    if chord_idx % 4 == 0:
        p.append((_h(0,3), beat*2, CRASH, _v(108,5)))

    # Tom fill near end
    if chord_idx == total-2:
        for i,tom in enumerate([HI_TOM,MID_TOM,LO_TOM,LF_TOM]):
            p.append((_h(beat*3+i*(ppq//4),4), ppq//4-10, tom, _v(88-i*5,9)))

    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":p}

# ── PERSIAN / DARBUKA ──────────────────────────────────────────
_DARB_DOUM = [
    [100,0,0,0, 0,0,0,0, 0,0,85,0,  0,0,0,0],   # basic Maqsum
    [100,0,0,0, 85,0,0,0, 0,0,0,0,  0,85,0,0],   # Wahda
    [100,0,85,0,0,0,0,0,  100,0,0,85,0,0,0,0],   # Baladi
]
_DARB_TEK = [
    [0,0,0,0,0,75,0,0, 0,0,0,75, 0,0,60,0],
    [0,0,0,75,0,0,75,0,0,0,0,0, 75,0,0,0],
    [0,75,0,0,0,0,75,0,0,75,0,0,0,0,75,0],
]
_DARB_KA  = [
    [0,0,45,0,45,0,0,45,0,45,0,0,45,0,0,45],
    [0,45,0,45,0,0,45,0,45,0,45,0,0,45,0,0],
    [45,0,0,45,0,45,0,0,0,45,0,45,0,0,45,0],
]

def _persian(ppq, bars, v=0):
    k = _seq({KICK:   _DARB_DOUM[v%3]}, ppq, bars, swing=0.05)
    s = _seq({HI_TOM: _DARB_TEK[v%3],
              RIM:    _DARB_KA[v%3]},   ppq, bars, swing=0.05)
    h = _seq({TAMB:[0,52,0,52]*4},       ppq, bars, swing=0.05)
    p = []
    if v == 2:  # roll on last bar
        roll = ppq*3
        for i in range(6):
            p.append((_h(roll+i*(ppq//6),4), ppq//6-4, TAMB, _v(68,12)))
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":p}

# ── 3/4 Waltz ──────────────────────────────────────────────────
def _waltz_34(ppq, bars, style, v=0):
    spb = 12  # 12 sixteenth-notes per 3/4 bar
    kick_p = [100,0,0,0,0,0, 0,0,0,0,0,0]
    if style in ("Trap","R&B"):
        snare_p= [0,0,0,0,0,0, 90,0,0,0,0,0]
    else:
        snare_p= [0,0,0,0,0,0, 88,0,0,0,0,0]
    hh_p   = [68,0,60,0,60,0, 68,0,60,0,60,0]
    k = _seq({KICK:kick_p},   ppq, bars, steps_per_bar=spb)
    s = _seq({SNARE:snare_p}, ppq, bars, steps_per_bar=spb)
    h = _seq({HH_CL:hh_p},   ppq, bars, steps_per_bar=spb)
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":[]}

# ── 6/8 ────────────────────────────────────────────────────────
def _six_eight(ppq, bars, style, v=0):
    spb = 12
    if style in ("Persian","Cinematic"):
        kp = [100,0,0, 0,0,0, 85,0,0, 0,0,0]
        sp = [0,0,0,   80,0,0, 0,0,0, 80,0,0]
        hp = [65,55,55]*4
    else:
        kp = [100,0,0, 0,0,0, 85,0,0, 0,0,0]
        sp = [0,0,0,   85,0,0, 0,0,0, 80,0,0]
        hp = [68,58,58]*4
    k = _seq({KICK:kp},   ppq, bars, steps_per_bar=spb)
    s = _seq({SNARE:sp},  ppq, bars, steps_per_bar=spb)
    h = _seq({HH_CL:hp},  ppq, bars, steps_per_bar=spb)
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":[]}

# ── 5/4 ────────────────────────────────────────────────────────
def _five_four(ppq, bars, style, v=0):
    spb = 20
    kp = [100,0,0,0,0, 0,0,0,0,0, 80,0,0,0,0, 0,0,0,75,0]
    sp = [0,0,0,0,90, 0,0,0,0,0,  0,0,0,0,88, 0,0,0,0,0]
    hp = [65,0,60,0,60]*4
    k = _seq({KICK:kp},   ppq, bars, steps_per_bar=spb)
    s = _seq({SNARE:sp},  ppq, bars, steps_per_bar=spb)
    h = _seq({HH_CL:hp},  ppq, bars, steps_per_bar=spb)
    return {"Kick":k,"Snare":s,"HiHat":h,"Percussion":[]}

# ═══════════════════════════════════════════════════════════════
#  FILLS
# ═══════════════════════════════════════════════════════════════

def _fill(ppq, style, ftype=None):
    """One-bar fill. Returns grouped events."""
    if ftype is None:
        ftype = random.randint(0, 6)
    beat = ppq
    s16  = ppq // 4
    toms = [HI_TOM, MID_TOM, LO_TOM, LF_TOM]
    ev   = {"Kick":[],"Snare":[],"HiHat":[],"Percussion":[]}

    if ftype == 0:   # Tom cascade 8th notes
        for i in range(8):
            tom = toms[min(i//2, 3)]
            ev["Percussion"].append((_h(i*(beat//2),5), beat//2-12, tom, _v(88-i*3,8)))

    elif ftype == 1: # Snare roll accelerating
        for i in range(16):
            ev["Snare"].append((_h(i*s16,5), s16-6, SNARE, _v(55+i*4,8)))
        ev["Percussion"].append((_h(beat*4-8,3), beat, CRASH, _v(112,5)))

    elif ftype == 2: # Kick+Snare alternating
        for i in range(8):
            t = i*(beat//2)
            if i%2==0: ev["Kick"].append((_h(t,5), beat//2-12, KICK, _v(92,8)))
            else:       ev["Snare"].append((_h(t,5), beat//2-12, SNARE, _v(88,8)))

    elif ftype == 3: # Triplet tom roll
        tri = ppq // 3
        for i in range(12):
            t = i * tri
            if t < beat*4:
                ev["Percussion"].append((_h(t,4), tri-6, toms[i%4], _v(82,10)))

    elif ftype == 4: # 32nd hi-hat burst + crash
        s32 = ppq // 8
        for i in range(32):
            t = i*s32
            if t < beat*4:
                n = HH_OP if i>24 else HH_CL
                ev["HiHat"].append((_h(t,3), s32-3, n, _v(55+i*2,7)))
        ev["Snare"].append((_h(beat*2,4), beat-20, SNARE, _v(100,6)))
        ev["Percussion"].append((_h(beat*4-5,3), beat, CRASH, _v(112,5)))

    elif ftype == 5: # Cinematic impact
        ev["Kick"].append((_h(0,3), beat*2, KICK, _v(118,4)))
        ev["Snare"].append((_h(beat*2,3), beat-20, SNARE, _v(112,5)))
        ev["Percussion"].append((_h(0,3), beat*4, CRASH, _v(118,4)))
        for i,tom in enumerate(toms):
            ev["Percussion"].append((_h(beat*3+i*(beat//4),4), beat//4-6, tom, _v(92-i*5,8)))

    elif ftype == 6: # Trap fill: rapid 16th kicks + clap
        for i in range(4):
            ev["Kick"].append((_h(i*s16*2,5), s16*2-10, KICK, _v(95,8)))
        for i in range(8):
            ev["HiHat"].append((_h(beat*2+i*s16,4), s16-5, HH_CL, _v(70+i*4,8)))
        ev["Snare"].append((_h(beat*3+s16*2,4), s16*2-10, CLAP, _v(105,6)))

    return ev

# ═══════════════════════════════════════════════════════════════
#  ACCENT LAYER — adds velocity accent on beat 1 of every bar
# ═══════════════════════════════════════════════════════════════

def _accents(events_dict, ppq, bars_per_chord, accent_note=CRASH, vel=85):
    """Add subtle crash accent on beat 1 of bar 1."""
    events_dict["Percussion"].append((_h(0,3), ppq//2, accent_note, _v(vel,8)))

# ═══════════════════════════════════════════════════════════════
#  MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════

STYLE_44 = {
    "Pop":       _pop,
    "R&B":       _rnb,
    "Lo-fi":     _lofi,
    "Cinematic": None,
    "Trap":      _trap,
    "Persian":   _persian,
}

def generate_drums(
    progression: List[Chord],
    style: str,
    ppq: int = 480,
    bars_per_chord: int = 2,
    time_signature: str = "4/4",
    drum_variant: int = 0,
    fill_frequency: int = 4,
    seed: Optional[int] = None,
) -> Dict[str, List[DrumEvent]]:
    """
    Returns {"Kick":[], "Snare":[], "HiHat":[], "Percussion":[]}
    All events use absolute ticks.
    """
    random.seed(seed if seed is not None else 99)

    tpc = ppq * 4 * bars_per_chord
    result: Dict[str, List[DrumEvent]] = {g:[] for g in DRUM_GROUPS}
    total = len(progression)

    for i, chord in enumerate(progression):
        # Rotate variant per chord for natural variation
        v = (drum_variant + i) % 3
        tick = i * tpc

        # ── Build base pattern ─────────────────────────────
        if time_signature == "3/4":
            grp = _waltz_34(ppq, bars_per_chord, style, v)
        elif time_signature == "6/8":
            grp = _six_eight(ppq, bars_per_chord, style, v)
        elif time_signature == "5/4":
            grp = _five_four(ppq, bars_per_chord, style, v)
        else:  # 4/4
            if style == "Cinematic":
                grp = _cinematic(ppq, bars_per_chord, v, i, total)
            else:
                fn = STYLE_44.get(style, _pop)
                grp = fn(ppq, bars_per_chord, v)

        # ── Accent: crash/ride on phrase start ─────────────
        if i % 4 == 0 and style not in ("Cinematic",):
            accent = CRASH if i % 8 == 0 else RIDE
            grp["Percussion"].append((_h(0,3), ppq//2, accent, _v(88,7)))

        # ── Fill: replace last bar of chord with fill ──────
        if fill_frequency > 0 and i > 0 and i % fill_frequency == fill_frequency-1:
            fill_offset = tpc - ppq * 4  # last bar
            ftype = (i // fill_frequency) % 7
            fill_grp = _fill(ppq, style, ftype)
            for g, evts in fill_grp.items():
                for (s, d, n, vv) in evts:
                    if s < ppq * 4:
                        grp[g].append((fill_offset + s, d, n, vv))

        # ── Collect with absolute ticks ────────────────────
        for g, evts in grp.items():
            for (s, d, n, vv) in evts:
                result[g].append((tick + s, d, n, vv))

    return result
