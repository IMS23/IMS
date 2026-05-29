"""
core/harmony_engine.py
Chord scoring engine - style, mood, complexity fully affect output.
"""
import json, os
from typing import List, Dict
from .theory import (
    Chord, build_diatonic_chords,
    voice_leading_score, bass_motion_score,
)

FUNCTION_TRANSITION: Dict[str, Dict[str, float]] = {
    "tonic":        {"tonic":0.5,"predominant":0.95,"dominant":0.75,"color":0.8,"passing":0.5},
    "predominant":  {"tonic":0.5,"predominant":0.4,"dominant":1.0,"color":0.7,"passing":0.6},
    "dominant":     {"tonic":1.0,"predominant":0.2,"dominant":0.3,"color":0.4,"passing":0.3},
    "color":        {"tonic":0.8,"predominant":0.8,"dominant":0.8,"color":0.6,"passing":0.6},
    "passing":      {"tonic":0.7,"predominant":0.6,"dominant":0.8,"color":0.6,"passing":0.4},
    "start":        {"tonic":1.0,"predominant":0.5,"dominant":0.2,"color":0.5,"passing":0.2},
}

# Style → preferred qualities (boosted), avoided qualities (penalized)
STYLE_QUALITY = {
    "Pop":       {"prefer":["maj","min","add9","maj7","min7"],        "avoid":["dim7","aug","m7b5"]},
    "R&B":       {"prefer":["maj7","min7","9","maj9","m9","11","m11"],"avoid":["dim","sus2"]},
    "Lo-fi":     {"prefer":["maj7","min7","m9","add9","madd9"],       "avoid":["7","aug","dim7"]},
    "Cinematic": {"prefer":["sus2","sus4","maj7","m9","madd9"],       "avoid":["dim"]},
    "Trap":      {"prefer":["min","min7","dim","m7b5"],               "avoid":["maj9","11","sus2"]},
    "Persian":   {"prefer":["maj","min","7","min7","dim"],            "avoid":["maj9","11"]},
}

# Mood → preferred qualities
MOOD_QUALITY = {
    "Happy":    {"prefer":["maj","add9","maj7","sus2"],    "avoid":["dim","dim7","m7b5"]},
    "Sad":      {"prefer":["min","min7","m9","madd9"],     "avoid":["maj","aug"]},
    "Dark":     {"prefer":["min","dim","m7b5","dim7","min7"],"avoid":["maj","add9"]},
    "Epic":     {"prefer":["maj","sus4","sus2","maj7"],    "avoid":["dim7"]},
    "Romantic": {"prefer":["maj7","min7","m9","add9","9"], "avoid":["dim","aug"]},
    "Tense":    {"prefer":["dim","7","m7b5","aug","dim7"], "avoid":["maj","sus2"]},
}

# Style → which scale degrees to emphasize
STYLE_DEGREE_BOOST = {
    "Pop":       {0:0.1, 3:0.1, 4:0.1, 5:0.05},
    "R&B":       {0:0.1, 1:0.1, 3:0.1, 4:0.05},
    "Lo-fi":     {0:0.15, 2:0.1, 5:0.1},
    "Cinematic": {0:0.1, 5:0.15, 2:0.1},
    "Trap":      {0:0.1, 2:0.15, 5:0.1, 6:0.1},
    "Persian":   {0:0.2, 1:0.2, 4:0.15},
}

# Complexity → allowed qualities
COMPLEXITY_ALLOW = {
    "Simple":   {"maj","min","dim","aug","sus2","sus4"},
    "Medium":   {"maj","min","dim","aug","sus2","sus4","maj7","min7","7","m7b5","dim7","minmaj7","add9","madd9"},
    "Advanced": None,  # all allowed
}


def _style_score(chord: Chord, style: str, complexity: str) -> float:
    prefs = STYLE_QUALITY.get(style, {})
    prefer = prefs.get("prefer", [])
    avoid  = prefs.get("avoid", [])
    # Complexity filter
    allowed = COMPLEXITY_ALLOW.get(complexity)
    if allowed and chord.quality not in allowed:
        return 0.1  # heavily penalize complex chords in Simple mode
    if chord.quality in prefer:
        score = 1.0
    elif chord.quality in avoid:
        score = 0.15
    else:
        score = 0.55
    # Degree boost
    deg_boosts = STYLE_DEGREE_BOOST.get(style, {})
    if chord.degree is not None:
        score += deg_boosts.get(chord.degree, 0)
    # Borrowed chord handling
    if chord.borrowed:
        if style in ("Cinematic","R&B","Persian"): score += 0.15
        elif style in ("Pop","Lo-fi"):              score -= 0.15
        elif style == "Trap":                       score -= 0.05
    return min(1.0, max(0.0, score))


def _mood_score(chord: Chord, mood: str) -> float:
    prefs = MOOD_QUALITY.get(mood, {})
    prefer = prefs.get("prefer", [])
    avoid  = prefs.get("avoid", [])
    if chord.quality in prefer:
        return 1.0
    elif chord.quality in avoid:
        return 0.1
    return 0.55


def score_chord(candidate: Chord, progression: List[Chord],
                style: str, mood: str, complexity: str,
                form_position: int, phrase_length: int = 8) -> float:

    W = {"function":0.22, "voice_lead":0.12, "bass_motion":0.08,
         "style":0.25, "mood":0.20, "repetition":0.13}

    # 1. Harmonic function transition
    prev_func = progression[-1].function if progression else "start"
    func_score = FUNCTION_TRANSITION.get(prev_func, {}).get(candidate.function, 0.5)
    if form_position >= phrase_length - 1 and candidate.function == "tonic":
        func_score = min(1.0, func_score + 0.25)
    if form_position == 0 and candidate.function != "tonic":
        func_score *= 0.7

    # 2. Voice leading
    vl = voice_leading_score(progression[-1], candidate) if progression else 0.65

    # 3. Bass motion
    bm = bass_motion_score(progression[-1], candidate) if progression else 0.65

    # 4. Style score (includes complexity filter + degree boost)
    style_s = _style_score(candidate, style, complexity)

    # 5. Mood score
    mood_s = _mood_score(candidate, mood)

    # 6. Repetition avoidance
    recent = [c.label for c in progression[-4:]]
    rep_count = recent.count(candidate.label)
    rep_score = max(0.0, 1.0 - rep_count * 0.5)

    total = (W["function"]   * func_score +
             W["voice_lead"] * vl +
             W["bass_motion"]* bm +
             W["style"]      * style_s +
             W["mood"]       * mood_s +
             W["repetition"] * rep_score)

    return round(total, 4)


def suggest_chords(root, scale, style, mood, complexity,
                   progression, top_n=12) -> List[Chord]:
    all_chords = build_diatonic_chords(root, scale, complexity)
    form_pos   = len(progression)

    scored = []
    for ch in all_chords:
        s = score_chord(ch, progression, style, mood, complexity, form_pos)
        scored.append((s, ch))
    scored.sort(key=lambda x: -x[0])

    # De-duplicate by label
    seen, results = set(), []
    for s, ch in scored:
        if ch.label not in seen:
            seen.add(ch.label)
            results.append(ch)
        if len(results) >= top_n:
            break
    return results


def starting_chords(root, scale, style, mood, complexity) -> List[Chord]:
    return suggest_chords(root, scale, style, mood, complexity, [], top_n=8)
