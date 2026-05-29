"""
ui/timeline_panel.py
=====================
Horizontal progression timeline. Each chord is a card showing:
 - Chord label (big)
 - Harmonic function badge
 - Remove button (×)
Cards can be reordered via drag-and-drop.
Emits: `progression_changed()` when the list changes.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont
from typing import List

from core.theory import Chord

FUNCTION_COLORS = {
    "tonic":       "#4ade80",
    "predominant": "#60a5fa",
    "dominant":    "#f87171",
    "color":       "#c084fc",
    "passing":     "#fb923c",
}


class ChordCard(QFrame):
    remove_requested = Signal(int)  # index

    def __init__(self, chord: Chord, index: int, parent=None):
        super().__init__(parent)
        self.chord = chord
        self.index = index
        self._drag_start: QPoint | None = None
        self._build()

    def _build(self):
        fn_color = FUNCTION_COLORS.get(self.chord.function, "#94a3b8")
        self.setObjectName("chordCard")
        self.setFixedSize(100, 90)
        self.setStyleSheet(f"""
            QFrame#chordCard {{
                border: 2px solid {fn_color};
                border-radius: 8px;
                background: rgba(255,255,255,0.05);
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # Index badge
        idx_lbl = QLabel(str(self.index + 1))
        idx_lbl.setObjectName("cardIndex")
        idx_lbl.setAlignment(Qt.AlignLeft)

        # Chord label
        lbl = QLabel(self.chord.label)
        lbl.setObjectName("cardLabel")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)

        # Function badge
        fn_lbl = QLabel(self.chord.function.upper()[:2])
        fn_lbl.setObjectName("cardFn")
        fn_lbl.setAlignment(Qt.AlignCenter)
        fn_lbl.setStyleSheet(f"color:{fn_color};")

        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setObjectName("cardRemove")
        remove_btn.setFixedSize(18, 18)
        remove_btn.setFlat(True)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.index))

        top_row = QHBoxLayout()
        top_row.addWidget(idx_lbl)
        top_row.addStretch()
        top_row.addWidget(remove_btn)

        layout.addLayout(top_row)
        layout.addWidget(lbl)
        layout.addWidget(fn_lbl)

    # Drag support
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start and (event.pos() - self._drag_start).manhattanLength() > 10:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(str(self.index))
            drag.setMimeData(mime)
            px = self.grab()
            drag.setPixmap(px)
            drag.exec(Qt.MoveAction)
        super().mouseMoveEvent(event)


class TimelinePanel(QWidget):
    progression_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._chords: List[Chord] = []
        self._build_ui()
        self.setAcceptDrops(True)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel("PROGRESSION TIMELINE")
        title.setObjectName("panelTitle")
        header.addWidget(title)
        header.addStretch()

        self._chord_count = QLabel("0 chords")
        self._chord_count.setObjectName("hintLabel")
        header.addWidget(self._chord_count)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("actionButton")
        clear_btn.setFixedWidth(56)
        clear_btn.clicked.connect(self._clear_all)
        header.addWidget(clear_btn)
        outer.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("separator")
        outer.addWidget(sep)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(130)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._cards_widget = QWidget()
        self._cards_layout = QHBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(8)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_widget)
        outer.addWidget(self._scroll)

        self._empty_label = QLabel("Click a chord suggestion to build your progression →")
        self._empty_label.setObjectName("hintLabel")
        self._empty_label.setAlignment(Qt.AlignCenter)
        outer.addWidget(self._empty_label)

    # ---- Public API ----

    def set_chords(self, chords: List[Chord]):
        self._chords = list(chords)
        self._refresh_cards()

    def get_chords(self) -> List[Chord]:
        return list(self._chords)

    def add_chord(self, chord: Chord):
        self._chords.append(chord)
        self._refresh_cards()
        self.progression_changed.emit()
        # Scroll to end
        self._scroll.horizontalScrollBar().setValue(
            self._scroll.horizontalScrollBar().maximum()
        )

    def _remove_chord(self, index: int):
        if 0 <= index < len(self._chords):
            self._chords.pop(index)
            self._refresh_cards()
            self.progression_changed.emit()

    def _clear_all(self):
        self._chords.clear()
        self._refresh_cards()
        self.progression_changed.emit()

    def _refresh_cards(self):
        # Remove all cards (preserve stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._empty_label.setVisible(len(self._chords) == 0)
        self._chord_count.setText(f"{len(self._chords)} chord{'s' if len(self._chords)!=1 else ''}")

        for i, chord in enumerate(self._chords):
            card = ChordCard(chord, i)
            card.remove_requested.connect(self._remove_chord)
            self._cards_layout.insertWidget(i, card)

    # ---- Drag & Drop reorder ----

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            return
        from_idx = int(event.mimeData().text())
        # Determine drop position from mouse x
        x = event.position().x()
        to_idx = 0
        for i in range(self._cards_layout.count() - 1):
            item = self._cards_layout.itemAt(i)
            if item and item.widget():
                if x > item.widget().x() + item.widget().width() / 2:
                    to_idx = i + 1
        if from_idx != to_idx:
            chord = self._chords.pop(from_idx)
            insert_at = to_idx if to_idx <= from_idx else to_idx - 1
            self._chords.insert(insert_at, chord)
            self._refresh_cards()
            self.progression_changed.emit()
        event.acceptProposedAction()
