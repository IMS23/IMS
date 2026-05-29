"""
ui/main_window.py
==================
QMainWindow that hosts:
  - ControlPanel (left)
  - SuggestionPanel (center-left)
  - TimelinePanel (bottom)
  - Export / Save / Load actions (toolbar + menu)
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QFileDialog, QMessageBox,
    QLabel, QCheckBox, QStatusBar, QMenuBar, QMenu, QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence

from core.project import Project, ProjectSettings
from core.theory import Chord
from ui.control_panel import ControlPanel
from ui.suggestion_panel import SuggestionPanel
from ui.timeline_panel import TimelinePanel
from generators.midi_exporter import export_midi
from ui.ai_panel import AIPanel


APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: 'Consolas', 'Menlo', monospace;
    font-size: 13px;
}

QLabel#panelTitle {
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
    color: #94a3b8;
    padding: 4px 0px;
}

QLabel#hintLabel {
    color: #475569;
    font-size: 11px;
    font-style: italic;
}

QLabel#controlLabel {
    font-size: 10px;
    letter-spacing: 1.5px;
    color: #64748b;
}

QComboBox#controlCombo, QSpinBox#controlCombo {
    background: #1e2535;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e2e8f0;
    selection-background-color: #3b82f6;
}
QComboBox#controlCombo::drop-down { border: none; }
QComboBox#controlCombo QAbstractItemView {
    background: #1e2535;
    border: 1px solid #3b82f6;
    selection-background-color: #3b82f6;
}

QPushButton#chordButton {
    background: #1a2035;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #e2e8f0;
    padding: 6px 10px;
    text-align: left;
    font-size: 13px;
}
QPushButton#chordButton:hover {
    background: #243050;
    border-color: #60a5fa;
}
QPushButton#chordButton:pressed {
    background: #1d3461;
}

QPushButton#exportButton {
    background: #1d4ed8;
    border: none;
    border-radius: 6px;
    color: white;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#exportButton:hover { background: #2563eb; }
QPushButton#exportButton:pressed { background: #1e40af; }

QPushButton#actionButton {
    background: #1e2535;
    border: 1px solid #334155;
    border-radius: 5px;
    color: #94a3b8;
    padding: 4px 10px;
}
QPushButton#actionButton:hover {
    background: #243050;
    color: #e2e8f0;
}

QLabel#cardLabel {
    font-size: 15px;
    font-weight: bold;
    color: #f1f5f9;
}
QLabel#cardIndex {
    font-size: 9px;
    color: #64748b;
}
QLabel#cardFn {
    font-size: 10px;
    letter-spacing: 1px;
}
QPushButton#cardRemove {
    color: #ef4444;
    font-size: 14px;
    font-weight: bold;
    background: transparent;
    border: none;
}
QPushButton#cardRemove:hover { color: #fca5a5; }

QFrame#separator {
    color: #1e2d3d;
    max-height: 1px;
}

QScrollArea { background: transparent; border: none; }
QScrollBar:horizontal {
    background: #0f1117;
    height: 6px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 3px;
}
QScrollBar:vertical {
    background: #0f1117;
    width: 6px;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 3px;
}

QSplitter::handle { background: #1e2d3d; width: 1px; }

QStatusBar { background: #0a0d14; color: #475569; font-size: 11px; }

QMenuBar { background: #0a0d14; color: #94a3b8; }
QMenuBar::item:selected { background: #1e2535; color: #e2e8f0; }
QMenu { background: #1e2535; border: 1px solid #334155; color: #e2e8f0; }
QMenu::item:selected { background: #3b82f6; }

QCheckBox { color: #94a3b8; font-size: 12px; }
QCheckBox::indicator { width: 14px; height: 14px; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project = Project()
        self.setWindowTitle("MIDI Composition Assistant")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(APP_STYLESHEET)
        self._build_menu()
        self._build_ui()
        self._build_statusbar()
        self._refresh_suggestions()

    # ------------------------------------------------------------------ #
    # Build                                                                #
    # ------------------------------------------------------------------ #

    def _build_menu(self):
        mb = self.menuBar()
        file_menu = mb.addMenu("File")

        new_act = QAction("New Project", self)
        new_act.setShortcut(QKeySequence.New)
        new_act.triggered.connect(self._new_project)
        file_menu.addAction(new_act)

        open_act = QAction("Open Project…", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self._load_project)
        file_menu.addAction(open_act)

        save_act = QAction("Save Project", self)
        save_act.setShortcut(QKeySequence.Save)
        save_act.triggered.connect(self._save_project)
        file_menu.addAction(save_act)

        saveas_act = QAction("Save Project As…", self)
        saveas_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        saveas_act.triggered.connect(lambda: self._save_project(force_dialog=True))
        file_menu.addAction(saveas_act)

        file_menu.addSeparator()
        export_act = QAction("Export MIDI…", self)
        export_act.setShortcut(QKeySequence("Ctrl+E"))
        export_act.triggered.connect(self._export_midi)
        file_menu.addAction(export_act)

        file_menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top toolbar strip
        toolbar = self._build_toolbar()
        root_layout.addWidget(toolbar)

        # Main splitter: controls | suggestions | (future: piano roll)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        self.control_panel = ControlPanel()
        self.control_panel.setFixedWidth(180)
        splitter.addWidget(self.control_panel)

        self.suggestion_panel = SuggestionPanel()
        self.suggestion_panel.setMinimumWidth(260)
        splitter.addWidget(self.suggestion_panel)

        # Right: info area (expandable in future)
        right_widget = self._build_right_panel()
        splitter.addWidget(right_widget)

        self.ai_panel = AIPanel()
        self.ai_panel.setMinimumWidth(300)
        self.ai_panel.apply_chords_requested.connect(self._apply_ai_chords)
        self.ai_panel.replace_chords_requested.connect(self._replace_ai_chords)
        splitter.addWidget(self.ai_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        splitter.setStretchFactor(3, 2)

        root_layout.addWidget(splitter, stretch=1)

        # Timeline at bottom
        self.timeline_panel = TimelinePanel()
        root_layout.addWidget(self.timeline_panel)

        # Wire signals
        self.control_panel.settings_changed.connect(self._on_settings_changed)
        self.suggestion_panel.chord_selected.connect(self._on_chord_selected)
        self.timeline_panel.progression_changed.connect(self._on_progression_changed)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("toolbar")
        bar.setFixedHeight(52)
        bar.setStyleSheet("background: #0a0d14; border-bottom: 1px solid #1e2d3d;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        title_lbl = QLabel("⬡  MIDI COMPOSER")
        title_lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#60a5fa; letter-spacing:3px;")
        layout.addWidget(title_lbl)

        layout.addStretch()

        self.arp_check = QCheckBox("Include Arpeggio")
        self.arp_check.setChecked(True)
        layout.addWidget(self.arp_check)
        self.drum_check = QCheckBox("Include Drums")
        self.drum_check.setChecked(True)
        layout.addWidget(self.drum_check)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("actionButton")
        self.save_btn.setFixedWidth(60)
        self.save_btn.clicked.connect(self._save_project)
        layout.addWidget(self.save_btn)

        self.load_btn = QPushButton("Load")
        self.load_btn.setObjectName("actionButton")
        self.load_btn.setFixedWidth(60)
        self.load_btn.clicked.connect(self._load_project)
        layout.addWidget(self.load_btn)

        self.export_btn = QPushButton("⬇  Export MIDI")
        self.export_btn.setObjectName("exportButton")
        self.export_btn.clicked.connect(self._export_midi)
        layout.addWidget(self.export_btn)

        self.play_btn = QPushButton("▶  Play")
        self.play_btn.setStyleSheet("""
            QPushButton{background:#166534;border:none;border-radius:6px;
            color:white;padding:8px 18px;font-weight:bold;font-size:13px;}
            QPushButton:hover{background:#15803d;}
            QPushButton:pressed{background:#14532d;}
        """)
        self.play_btn.clicked.connect(self._play_midi)
        layout.addWidget(self.play_btn)

        return bar

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        info_title = QLabel("PROGRESSION INFO")
        info_title.setObjectName("panelTitle")
        layout.addWidget(info_title)

        sep = self._sep()
        layout.addWidget(sep)

        self.info_label = QLabel("Add chords to your progression to see analysis here.")
        self.info_label.setObjectName("hintLabel")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignTop)
        layout.addWidget(self.info_label)

        layout.addStretch()

        # Generator info
        gen_title = QLabel("AUTO-GENERATION")
        gen_title.setObjectName("panelTitle")
        layout.addWidget(gen_title)
        layout.addWidget(self._sep())

        gen_info = QLabel(
            "On export, the following tracks are auto-generated:\n\n"
            "  Track 1 — Chords\n"
            "  Track 2 — Bass\n"
            "  Track 3 — Melody\n"
            "  Track 4 — Arpeggio (optional)\n\n"
            "Bass style adapts to the selected style.\n"
            "Melody uses motif-based generation."
        )
        gen_info.setObjectName("hintLabel")
        gen_info.setWordWrap(True)
        layout.addWidget(gen_info)

        layout.addStretch()
        return panel

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_lbl = QLabel("Ready — no project saved")
        sb.addWidget(self._status_lbl)

    def _sep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        return sep

    # ------------------------------------------------------------------ #
    # Signal handlers                                                      #
    # ------------------------------------------------------------------ #

    def _on_settings_changed(self):
        s = self.project.settings
        s.root       = self.control_panel.root
        s.scale      = self.control_panel.scale
        s.style      = self.control_panel.style
        s.mood       = self.control_panel.mood
        s.complexity = self.control_panel.complexity
        s.bpm        = self.control_panel.bpm
        s.bars_per_chord = self.control_panel.bars_per_chord
        s.drum_pattern = self.control_panel.drum_pattern
        self._refresh_suggestions()
        self._update_info()

    def _on_chord_selected(self, chord: Chord):
        self.project.add_chord(chord)
        self.timeline_panel.add_chord(chord)
        self._refresh_suggestions()
        self._update_info()
        self.ai_panel.set_context(self.project.progression, self.project.settings)
        self._status_lbl.setText(f"Added: {chord.label}  ({len(self.project.progression)} chords)")

    def _on_progression_changed(self):
        self.project.progression = self.timeline_panel.get_chords()
        self._refresh_suggestions()
        self._update_info()
        self.ai_panel.set_context(self.project.progression, self.project.settings)

    def _refresh_suggestions(self):
        s = self.project.settings
        self.suggestion_panel.refresh(
            s.root, s.scale, s.style, s.mood, s.complexity,
            self.project.progression,
        )

    def _update_info(self):
        prog = self.project.progression
        if not prog:
            self.info_label.setText("Add chords to your progression to see analysis here.")
            return
        lines = []
        for i, ch in enumerate(prog):
            borrowed = " [borrowed]" if ch.borrowed else ""
            sec = f" [V/{ch.secondary_target}]" if ch.secondary_target else ""
            lines.append(f"  {i+1:2}. {ch.label:<12} {ch.function.upper()}{borrowed}{sec}")
        self.info_label.setText("\n".join(lines))

    # ------------------------------------------------------------------ #
    # Actions                                                              #
    # ------------------------------------------------------------------ #

    def _new_project(self):
        reply = QMessageBox.question(
            self, "New Project", "Start a new project? Unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.project = Project()
            self.timeline_panel.set_chords([])
            self._refresh_suggestions()
            self._update_info()
            self._status_lbl.setText("New project")

    def _save_project(self, force_dialog=False):
        path = self.project.filename
        if not path or force_dialog:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Project", "", "MIDI Composer Projects (*.json)"
            )
        if path:
            if not path.endswith(".json"):
                path += ".json"
            self.project.save(path)
            self._status_lbl.setText(f"Saved: {os.path.basename(path)}")

    def _load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "MIDI Composer Projects (*.json)"
        )
        if path:
            try:
                self.project = Project.load(path)
                s = self.project.settings
                self.control_panel.apply_settings(
                    s.root, s.scale, s.style, s.mood, s.complexity,
                    s.bpm, s.bars_per_chord,
                )
                self.timeline_panel.set_chords(self.project.progression)
                self._refresh_suggestions()
                self._update_info()
                self._status_lbl.setText(f"Loaded: {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", str(e))

    def _export_midi(self):
        if not self.project.progression:
            QMessageBox.warning(self, "Nothing to export",
                                "Add at least one chord before exporting.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export MIDI", "progression.mid", "MIDI Files (*.mid *.midi)"
        )
        if path:
            if not path.endswith((".mid", ".midi")):
                path += ".mid"
            try:
                export_midi(
                    self.project, path,
                    include_arpeggio=self.arp_check.isChecked(),
                )
                self._status_lbl.setText(f"Exported: {os.path.basename(path)}")
                QMessageBox.information(
                    self, "Export Successful",
                    f"MIDI file saved to:\n{path}\n\n"
                    f"Tracks: Chords, Bass, Melody"
                    f"{', Arpeggio' if self.arp_check.isChecked() else ''}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _play_midi(self):
        import tempfile
        if not self.project.progression:
            QMessageBox.warning(self, "هیچ چیزی نیست", "ابتدا آکورد اضافه کنید.")
            return
        try:
            from generators.midi_exporter import export_midi
            tmp = os.path.join(tempfile.gettempdir(), "midi_preview.mid")
            export_midi(self.project, tmp, include_arpeggio=self.arp_check.isChecked(), include_drums=self.drum_check.isChecked())
            os.startfile(tmp)
            self._status_lbl.setText("▶ در حال پخش پیش‌نمایش MIDI...")
            self.play_btn.setText("⏹  Stop")
            self.play_btn.setStyleSheet("""
                QPushButton{background:#991b1b;border:none;border-radius:6px;
                color:white;padding:8px 18px;font-weight:bold;font-size:13px;}
                QPushButton:hover{background:#7f1d1d;}
            """)
            from PySide6.QtCore import QTimer
            bars = len(self.project.progression) * self.project.settings.bars_per_chord
            bpm  = self.project.settings.bpm
            ms   = int((bars * 4 * 60 / bpm) * 1000) + 2000
            QTimer.singleShot(ms, self._reset_play_btn)
        except Exception as e:
            QMessageBox.critical(self, "خطای پخش", str(e))

    def _reset_play_btn(self):
        self.play_btn.setText("▶  Play")
        self.play_btn.setStyleSheet("""
            QPushButton{background:#166534;border:none;border-radius:6px;
            color:white;padding:8px 18px;font-weight:bold;font-size:13px;}
            QPushButton:hover{background:#15803d;}
        """)
        self._status_lbl.setText("پخش پایان یافت.")

    def _apply_ai_chords(self, chord_labels: list):
        from core.theory import build_diatonic_chords
        from core.harmony_engine import suggest_chords
        s = self.project.settings
        palette   = build_diatonic_chords(s.root, s.scale, s.complexity)
        suggested = suggest_chords(s.root, s.scale, s.style, s.mood, s.complexity,
                                   self.project.progression, top_n=50)
        all_chords = {c.label: c for c in palette + suggested}
        added, missing = 0, []
        for label in chord_labels:
            label = label.strip()
            if label in all_chords:
                chord = all_chords[label]
                self.project.add_chord(chord)
                self.timeline_panel.add_chord(chord)
                added += 1
            else:
                missing.append(label)
        self._refresh_suggestions()
        self._update_info()
        self.ai_panel.set_context(self.project.progression, self.project.settings)
        msg = f"✅ {added} آکورد از AI اضافه شد."
        if missing:
            msg += f"  |  یافت نشد: {', '.join(missing)}"
        self._status_lbl.setText(msg)

    def _replace_ai_chords(self, chord_labels: list):
        """Replace entire progression with AI suggestions."""
        from core.theory import build_diatonic_chords
        from core.harmony_engine import suggest_chords
        s = self.project.settings
        palette = build_diatonic_chords(s.root, s.scale, s.complexity)
        sugg = suggest_chords(s.root, s.scale, s.style, s.mood,
                              s.complexity, [], top_n=60)
        all_ch = {c.label: c for c in palette + sugg}

        new_prog, missing = [], []
        for lbl in chord_labels:
            lbl = lbl.strip()
            if lbl in all_ch:
                new_prog.append(all_ch[lbl])
            else:
                missing.append(lbl)

        if not new_prog:
            self._status_lbl.setText("⚠️ هیچ آکوردی یافت نشد.")
            return

        # Replace progression
        self.project.progression = new_prog
        self.timeline_panel.set_chords(new_prog)
        self._refresh_suggestions()
        self._update_info()
        self.ai_panel.set_context(self.project.progression, self.project.settings)
        msg = f"🔄 Progression با {len(new_prog)} آکورد AI جایگزین شد."
        if missing: msg += f"  ⚠️ یافت نشد: {', '.join(missing)}"
        self._status_lbl.setText(msg)


