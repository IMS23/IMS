"""
ui/suggestion_panel.py
Chord suggestion buttons with audio preview on click.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
from typing import List
from core.theory import Chord
from core.harmony_engine import suggest_chords, starting_chords, score_chord

FUNCTION_COLORS = {
    "tonic":       "#4ade80",
    "predominant": "#60a5fa",
    "dominant":    "#f87171",
    "color":       "#c084fc",
    "passing":     "#fb923c",
}
FUNCTION_ABBR = {
    "tonic":"T","predominant":"PD","dominant":"D","color":"C","passing":"P",
}


class ChordButton(QPushButton):
    preview_requested = Signal(object, str)   # chord, style

    def __init__(self, chord: Chord, score: float, style: str = "Pop", parent=None):
        super().__init__(parent)
        self.chord = chord
        self._score = score
        self._style = style
        self._build()

    def _build(self):
        fn_color = FUNCTION_COLORS.get(self.chord.function, "#94a3b8")
        fn_abbr  = FUNCTION_ABBR.get(self.chord.function, "?")
        pct      = int(self._score * 100)
        self.setText(f"{self.chord.label}  [{fn_abbr}]  {pct}%")
        self.setObjectName("chordButton")
        self.setMinimumHeight(38)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                border-left: 4px solid {fn_color};
                text-align: left;
                padding-left: 10px;
            }}
            QPushButton:hover {{
                background: #1e3050;
                border-left: 4px solid {fn_color};
            }}
        """)

    def mousePressEvent(self, event):
        """Left click = preview sound + add to progression."""
        if event.button() == Qt.LeftButton:
            # Play preview first (non-blocking)
            self.preview_requested.emit(self.chord, self._style)
        super().mousePressEvent(event)


class SuggestionPanel(QWidget):
    chord_selected = Signal(object)   # Chord

    def __init__(self, parent=None):
        super().__init__(parent)
        self._style = "Pop"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("CHORD SUGGESTIONS")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        # Legend
        legend = QHBoxLayout()
        for fn, color in FUNCTION_COLORS.items():
            dot = QLabel(f"● {FUNCTION_ABBR[fn]}")
            dot.setStyleSheet(f"color:{color};font-size:10px;")
            legend.addWidget(dot)
        legend.addStretch()
        layout.addLayout(legend)

        # Preview hint
        hint = QLabel("🔊 کلیک = پیش‌نمایش + افزودن به progression")
        hint.setStyleSheet("color:#475569;font-size:10px;font-style:italic;")
        layout.addWidget(hint)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("separator")
        layout.addWidget(sep)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0,0,0,0); self._list_layout.setSpacing(4)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll)

        self._empty_label = QLabel("Select key/scale/style to see suggestions.")
        self._empty_label.setObjectName("hintLabel")
        self._empty_label.setWordWrap(True)
        self._empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._empty_label)

    def refresh(self, root, scale, style, mood, complexity, progression):
        self._style = style
        if progression:
            chords = suggest_chords(root, scale, style, mood, complexity, progression, top_n=16)
        else:
            chords = starting_chords(root, scale, style, mood, complexity)

        scored = []
        for ch in chords:
            s = score_chord(ch, progression, style, mood, complexity, len(progression), 8)
            scored.append((s, ch))
        scored.sort(key=lambda x: -x[0])

        # Clear
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not scored:
            self._empty_label.setVisible(True)
            return
        self._empty_label.setVisible(False)

        for score, chord in scored:
            btn = ChordButton(chord, score, style)
            # Preview sound on click
            btn.preview_requested.connect(self._on_preview)
            # Add to progression on click
            btn.clicked.connect(lambda checked=False, c=chord: self.chord_selected.emit(c))
            self._list_layout.insertWidget(self._list_layout.count()-1, btn)

    def _on_preview(self, chord, style):
        try:
            from generators.audio_preview import preview_chord
            preview_chord(chord, style, duration_ms=1000)
        except Exception as e:
            print(f"[Preview] {e}")
