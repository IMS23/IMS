"""
ui/control_panel.py
Settings panel - all controls actually affect MIDI output.
BPM has simple +/- buttons, no automation.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QFrame, QPushButton,
)
from PySide6.QtCore import Signal

KEYS       = ["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"]
SCALES     = ["Major","Natural Minor","Harmonic Minor","Dorian","Phrygian Dominant","Hijaz"]
STYLES     = ["Pop","R&B","Lo-fi","Cinematic","Trap","Persian"]
MOODS      = ["Happy","Sad","Dark","Epic","Romantic","Tense"]
COMPLEXITY = ["Simple","Medium","Advanced"]


def _row(label_text, widget, parent=None):
    container = QWidget(parent)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0,0,0,4)
    layout.setSpacing(3)
    lbl = QLabel(label_text)
    lbl.setObjectName("controlLabel")
    layout.addWidget(lbl)
    layout.addWidget(widget)
    return container


class ControlPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12,12,12,12)
        layout.setSpacing(8)

        title = QLabel("SETTINGS")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("separator")
        layout.addWidget(sep)

        # Key
        self.key_combo = QComboBox(); self.key_combo.addItems(KEYS); self.key_combo.setObjectName("controlCombo")
        layout.addWidget(_row("KEY", self.key_combo))

        # Scale
        self.scale_combo = QComboBox(); self.scale_combo.addItems(SCALES); self.scale_combo.setObjectName("controlCombo")
        layout.addWidget(_row("SCALE", self.scale_combo))

        # Style
        self.style_combo = QComboBox(); self.style_combo.addItems(STYLES); self.style_combo.setObjectName("controlCombo")
        layout.addWidget(_row("STYLE", self.style_combo))

        # Mood
        self.mood_combo = QComboBox(); self.mood_combo.addItems(MOODS); self.mood_combo.setObjectName("controlCombo")
        layout.addWidget(_row("MOOD", self.mood_combo))

        # Complexity
        self.complexity_combo = QComboBox(); self.complexity_combo.addItems(COMPLEXITY)
        self.complexity_combo.setCurrentIndex(1); self.complexity_combo.setObjectName("controlCombo")
        layout.addWidget(_row("COMPLEXITY", self.complexity_combo))

        # BPM — simple spinbox, no automation buttons
        self.bpm_spin = QSpinBox()
        self.bpm_spin.setRange(40, 240)
        self.bpm_spin.setValue(90)
        self.bpm_spin.setSuffix(" BPM")
        self.bpm_spin.setObjectName("controlCombo")
        self.bpm_spin.setButtonSymbols(QSpinBox.NoButtons)  # hide ugly arrows
        # Manual +/- buttons
        bpm_widget = QWidget()
        bpm_row = QHBoxLayout(bpm_widget)
        bpm_row.setContentsMargins(0,0,0,0); bpm_row.setSpacing(4)
        btn_minus = QPushButton("−"); btn_minus.setFixedSize(26,26)
        btn_minus.setStyleSheet("QPushButton{background:#1e2535;border:1px solid #334155;border-radius:4px;color:#94a3b8;font-size:14px;}QPushButton:hover{background:#243050;color:white;}")
        btn_plus  = QPushButton("+"); btn_plus.setFixedSize(26,26)
        btn_plus.setStyleSheet("QPushButton{background:#1e2535;border:1px solid #334155;border-radius:4px;color:#94a3b8;font-size:14px;}QPushButton:hover{background:#243050;color:white;}")
        btn_minus.clicked.connect(lambda: self.bpm_spin.setValue(self.bpm_spin.value()-5))
        btn_plus.clicked.connect(lambda:  self.bpm_spin.setValue(self.bpm_spin.value()+5))
        bpm_row.addWidget(btn_minus)
        bpm_row.addWidget(self.bpm_spin, stretch=1)
        bpm_row.addWidget(btn_plus)
        layout.addWidget(_row("BPM", bpm_widget))

        # Bars per chord
        self.bpc_combo = QComboBox()
        self.bpc_combo.addItems(["1","2","4"]); self.bpc_combo.setCurrentIndex(1)
        self.bpc_combo.setObjectName("controlCombo")
        layout.addWidget(_row("BARS / CHORD", self.bpc_combo))

        # Drum Pattern selector
        self.drum_combo = QComboBox()
        self.drum_combo.addItems([
            "Auto (match style)",
            "Pop - Standard",
            "Pop - Syncopated",
            "Pop - Half-time",
            "R&B - Groove",
            "R&B - Trap-Soul",
            "Lo-fi - Sparse",
            "Lo-fi - Very Sparse",
            "Cinematic - Epic",
            "Cinematic - Driving",
            "Trap - Standard",
            "Trap - Hi-hat Triplets",
            "Trap - Bouncy",
            "Persian - Darbuka",
            "Persian - 6/8",
        ])
        self.drum_combo.setObjectName("controlCombo")
        self.drum_combo.currentIndexChanged.connect(lambda _: self.settings_changed.emit())
        layout.addWidget(_row("DRUM PATTERN", self.drum_combo))

        # Time Signature
        self.timesig_combo = QComboBox()
        self.timesig_combo.addItems(["4/4","3/4","6/8","5/4"])
        self.timesig_combo.setObjectName("controlCombo")
        layout.addWidget(_row("TIME SIG", self.timesig_combo))

        # Drum Variant
        self.drumvar_combo = QComboBox()
        self.drumvar_combo.addItems(["Variant A","Variant B","Variant C"])
        self.drumvar_combo.setObjectName("controlCombo")
        layout.addWidget(_row("DRUM PATTERN", self.drumvar_combo))

        # Fill Frequency
        self.filfreq_combo = QComboBox()
        self.filfreq_combo.addItems(["No Fill","Every 2","Every 4","Every 8"])
        self.filfreq_combo.setCurrentIndex(2)
        self.filfreq_combo.setObjectName("controlCombo")
        layout.addWidget(_row("DRUM FILL", self.filfreq_combo))

        layout.addStretch()

        # Connect all — use lambda to ignore the index/value argument
        for w in (self.key_combo, self.scale_combo, self.style_combo,
                  self.mood_combo, self.complexity_combo, self.bpc_combo,
                  self.timesig_combo, self.drumvar_combo, self.filfreq_combo):
            w.currentIndexChanged.connect(lambda _: self.settings_changed.emit())
        self.bpm_spin.valueChanged.connect(lambda _: self.settings_changed.emit())

    @property
    def root(self): return self.key_combo.currentText()
    @property
    def scale(self): return self.scale_combo.currentText()
    @property
    def style(self): return self.style_combo.currentText()
    @property
    def mood(self): return self.mood_combo.currentText()
    @property
    def complexity(self): return self.complexity_combo.currentText()
    @property
    def bpm(self): return self.bpm_spin.value()
    @property
    def bars_per_chord(self): return int(self.bpc_combo.currentText())

    @property
    def drum_pattern(self): return self.drum_combo.currentText()

    @property
    def time_signature(self): return self.timesig_combo.currentText()
    @property
    def drum_variant(self): return self.drumvar_combo.currentIndex()
    @property
    def fill_frequency(self):
        m = {"No Fill":0,"Every 2":2,"Every 4":4,"Every 8":8}
        return m.get(self.filfreq_combo.currentText(), 4)

    def apply_settings(self, root, scale, style, mood, complexity, bpm, bars_per_chord):
        for combo, val in [(self.key_combo,root),(self.scale_combo,scale),
                           (self.style_combo,style),(self.mood_combo,mood),
                           (self.complexity_combo,complexity)]:
            idx = combo.findText(val)
            if idx >= 0: combo.setCurrentIndex(idx)
        self.bpm_spin.setValue(bpm)
        idx = self.bpc_combo.findText(str(bars_per_chord))
        if idx >= 0: self.bpc_combo.setCurrentIndex(idx)
        # drum_pattern not saved in old projects - leave default
