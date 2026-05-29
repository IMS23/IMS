"""
ui/ai_panel.py
AI Assistant panel - Ollama qwen2:7b
Features:
 - Parse AI chord suggestions and apply to timeline with one click
 - Streaming responses
 - Persian UI
"""
import json, re, urllib.request, urllib.error
from threading import Thread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QObject, QTimer

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2:7b-instruct-q5_K_M"
SYSTEM_PROMPT = """You are an expert music theory assistant. Help musicians build chord progressions.
You know harmony, voice leading, scales, modes, and styles like Pop, R&B, Lo-fi, Cinematic, Trap, Persian/Hijaz.
Be concise and practical. When suggesting chords, ALWAYS format them in a special block like this:
[CHORDS: Am, F, C, G]
This allows the app to automatically add them. Always include this block when suggesting progressions.
Respond in Persian (Farsi) unless asked otherwise."""

# Regex to extract chord block from AI response
CHORD_BLOCK_RE    = re.compile(r'\[CHORDS:\s*([^\]]+)\]', re.IGNORECASE)
SETTINGS_BLOCK_RE = re.compile(r'\[SETTINGS:\s*([^\]]+)\]', re.IGNORECASE)

def _parse_settings_block(text: str) -> dict:
    """Parse [SETTINGS: key=Am, scale=Natural Minor, style=Lo-fi, mood=Sad, bpm=75]"""
    result = {}
    matches = SETTINGS_BLOCK_RE.findall(text)
    for m in matches:
        for part in m.split(','):
            part = part.strip()
            if '=' in part:
                k, v = part.split('=', 1)
                result[k.strip().lower()] = v.strip()
    return result


class OllamaWorker(QObject):
    token_received = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        payload = json.dumps({
            "model": MODEL_NAME,
            "prompt": self.prompt,
            "system": SYSTEM_PROMPT,
            "stream": True,
            "options": {"temperature": 0.7, "num_predict": 700},
        }).encode()
        try:
            req = urllib.request.Request(
                OLLAMA_URL, data=payload,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token: self.token_received.emit(token)
                        if data.get("done"): break
                    except: continue
        except urllib.error.URLError:
            self.error.emit("خطا: Ollama در حال اجرا نیست.\nدر یک CMD جدید بزنید:\n  ollama serve")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


# ---------------------------------------------------------------------------
# Chord Apply Button — shown when AI suggests chords
# ---------------------------------------------------------------------------

class ChordApplyWidget(QFrame):
    apply_requested  = Signal(list)   # add to timeline
    replace_requested = Signal(list)  # replace timeline

    def __init__(self, chord_labels: list, parent=None):
        super().__init__(parent)
        self.chord_labels = chord_labels
        self._build(chord_labels)

    def _build(self, labels):
        self.setStyleSheet("""
            QFrame {
                background: #0d2d1a;
                border: 1px solid #166534;
                border-radius: 8px;
                margin: 4px 0;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel("🎵 آکوردهای پیشنهادی AI:")
        title.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: bold;")
        layout.addWidget(title)

        # Chord chips row
        chips_row = QHBoxLayout()
        chips_row.setSpacing(4)
        for label in labels:
            chip = QLabel(label)
            chip.setStyleSheet("""
                QLabel {
                    background: #166534;
                    color: #bbf7d0;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
            chip.setAlignment(Qt.AlignCenter)
            chips_row.addWidget(chip)
        chips_row.addStretch()
        layout.addLayout(chips_row)

        # Apply button
        btn_row = QHBoxLayout()

        replace_btn = QPushButton("🔄  جایگزین کردن Progression")
        replace_btn.setStyleSheet("""
            QPushButton {
                background: #1d4ed8;
                border: none; border-radius: 6px;
                color: white; padding: 6px 10px;
                font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        replace_btn.clicked.connect(lambda: self.replace_requested.emit(self.chord_labels))

        add_btn = QPushButton("➕  افزودن")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #166534;
                border: none; border-radius: 6px;
                color: white; padding: 6px 10px;
                font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: #15803d; }
        """)
        add_btn.clicked.connect(lambda: self.apply_requested.emit(self.chord_labels))

        btn_row.addWidget(replace_btn)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)


# ---------------------------------------------------------------------------
# Settings Apply Widget

class SettingsApplyWidget(QFrame):
    apply_requested = Signal(dict)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._build(settings)

    def _build(self, s):
        self.setStyleSheet("""
            QFrame {
                background: #1a1a2e;
                border: 1px solid #3b82f6;
                border-radius: 8px;
                margin: 4px 0;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,8,10,8)
        layout.setSpacing(6)

        title = QLabel("⚙️ تغییر تنظیمات پیشنهادی AI:")
        title.setStyleSheet("color:#60a5fa;font-size:11px;font-weight:bold;")
        layout.addWidget(title)

        chips_row = QHBoxLayout(); chips_row.setSpacing(4)
        labels = {
            "key":"🎵","scale":"🎼","style":"🎸","mood":"🎭","bpm":"⏱"
        }
        for k, v in s.items():
            if k in labels:
                chip = QLabel(f"{labels[k]} {v}")
                chip.setStyleSheet("background:#1e3a5f;color:#93c5fd;border-radius:4px;padding:3px 8px;font-size:11px;")
                chips_row.addWidget(chip)
        chips_row.addStretch()
        layout.addLayout(chips_row)

        btn = QPushButton("⚙️  اعمال تنظیمات")
        btn.setStyleSheet("""
            QPushButton {
                background:#1d4ed8;border:none;border-radius:6px;
                color:white;padding:6px 14px;font-size:12px;font-weight:bold;
            }
            QPushButton:hover{background:#2563eb;}
        """)
        btn.clicked.connect(lambda: self.apply_requested.emit(self._settings))
        layout.addWidget(btn)


# ---------------------------------------------------------------------------
# Message bubble
# ---------------------------------------------------------------------------

class MessageBubble(QFrame):
    chord_apply_requested   = Signal(list)
    chord_replace_requested = Signal(list)

    def __init__(self, text, is_user, parent=None):
        super().__init__(parent)
        self._text = text
        self._apply_widget = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        role = QLabel("شما" if is_user else "🤖 دستیار AI")
        role.setStyleSheet(f"color:{'#60a5fa' if is_user else '#4ade80'};font-size:10px;font-weight:bold;letter-spacing:1px;")

        self.body = QLabel(text)
        self.body.setWordWrap(True)
        self.body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.body.setStyleSheet("color:#e2e8f0;font-size:13px;line-height:1.6;")

        layout.addWidget(role)
        layout.addWidget(self.body)
        self._layout = layout

        bg = "#1a2540" if is_user else "#0f1a2e"
        border = "#3b82f6" if is_user else "#1e3a5f"
        self.setStyleSheet(f"QFrame{{background:{bg};border-left:3px solid {border};border-radius:6px;margin:2px 0;}}")

    def append(self, token):
        self._text += token
        # Hide [CHORDS:...] block from display text
        display = CHORD_BLOCK_RE.sub("", self._text).strip()
        self.body.setText(display)

    def finalize(self):
        """Called when streaming ends - check for chord suggestions."""
        matches = CHORD_BLOCK_RE.findall(self._text)
        if matches and not self._apply_widget:
            all_labels = []
            for m in matches:
                labels = [x.strip() for x in m.split(",") if x.strip()]
                all_labels.extend(labels)
            if all_labels:
                self._apply_widget = ChordApplyWidget(all_labels)
                self._apply_widget.apply_requested.connect(self.chord_apply_requested.emit)
                self._apply_widget.replace_requested.connect(self.chord_replace_requested.emit)
                self._layout.addWidget(self._apply_widget)


# ---------------------------------------------------------------------------
# Main AI Panel
# ---------------------------------------------------------------------------

class AIPanel(QWidget):
    apply_chords_requested   = Signal(list)  # add to timeline
    replace_chords_requested = Signal(list)  # replace timeline

    def __init__(self, parent=None):
        super().__init__(parent)
        self._context = ""
        self._bubble = None
        self._thread = None
        self._worker = None
        self._build_ui()
        self._check_ollama()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("AI ASSISTANT  •  Qwen2 7B")
        title.setObjectName("panelTitle")
        hdr.addWidget(title)
        hdr.addStretch()
        self._dot = QLabel("● بررسی...")
        self._dot.setStyleSheet("color:#94a3b8;font-size:10px;")
        hdr.addWidget(self._dot)
        layout.addLayout(hdr)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("separator")
        layout.addWidget(sep)

        # Quick buttons
        row = QHBoxLayout(); row.setSpacing(5)
        quick_btns = [
            ("🔍 تحلیل",   self._analyze),
            ("✨ پیشنهاد",  self._suggest),
            ("🎵 توضیح",   self._explain),
            ("🗑 پاک",      self._clear),
        ]
        for label, fn in quick_btns:
            b = QPushButton(label)
            b.setStyleSheet("""
                QPushButton {
                    background:#1e2535; border:1px solid #334155;
                    border-radius:5px; color:#94a3b8;
                    padding:5px 10px; font-size:11px;
                }
                QPushButton:hover { background:#243050; color:#e2e8f0; }
                QPushButton:pressed { background:#1d3461; }
            """)
            b.clicked.connect(fn)
            row.addWidget(b)
        layout.addLayout(row)

        # Chat scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self._scroll = scroll
        self._chat_w = QWidget()
        self._chat_l = QVBoxLayout(self._chat_w)
        self._chat_l.setContentsMargins(0, 0, 0, 0)
        self._chat_l.setSpacing(5)
        self._chat_l.addStretch()
        scroll.setWidget(self._chat_w)
        layout.addWidget(scroll, stretch=1)

        # Input row
        inp_frame = QFrame()
        inp_frame.setStyleSheet("background:#1e2535;border-radius:8px;border:1px solid #334155;")
        inp_row = QHBoxLayout(inp_frame)
        inp_row.setContentsMargins(8, 6, 6, 6)
        inp_row.setSpacing(6)
        self._input = QLineEdit()
        self._input.setPlaceholderText("سوال موسیقی بپرسید...")
        self._input.setStyleSheet("QLineEdit{background:transparent;border:none;color:#e2e8f0;font-size:13px;}")
        self._input.returnPressed.connect(self._send)
        self._send_btn = QPushButton("ارسال")
        self._send_btn.setStyleSheet("""
            QPushButton{background:#1d4ed8;border:none;border-radius:5px;color:white;padding:5px 14px;font-size:12px;}
            QPushButton:hover{background:#2563eb;}
            QPushButton:disabled{background:#334155;color:#64748b;}
        """)
        self._send_btn.clicked.connect(self._send)
        inp_row.addWidget(self._input)
        inp_row.addWidget(self._send_btn)
        layout.addWidget(inp_frame)

        self._add_ai(
            "سلام! 👋 من دستیار موسیقی شما هستم.\n\n"
            "• 🔍 تحلیل — progression فعلی را تحلیل کن\n"
            "• ✨ پیشنهاد — آکوردهای بعدی پیشنهاد بده و به timeline اضافه کن\n"
            "• 🎵 توضیح — تئوری موسیقی توضیح بده\n\n"
            "وقتی AI آکورد پیشنهاد می‌دهد، دکمه سبز ➕ ظاهر می‌شود!"
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def set_context(self, progression, settings):
        if not progression:
            self._context = ""
            return
        labels = " → ".join(c.label for c in progression)
        self._context = (
            f"Progression: {labels}\n"
            f"Key: {settings.root} | Scale: {settings.scale} | "
            f"Style: {settings.style} | Mood: {settings.mood} | BPM: {settings.bpm}"
        )

    # ------------------------------------------------------------------ #
    # Quick actions
    # ------------------------------------------------------------------ #

    def _analyze(self):
        if not self._context:
            self._add_ai("⚠️ ابتدا چند آکورد اضافه کنید."); return
        self._add_user("🔍 تحلیل progression")
        self._query(
            f"{self._context}\n\n"
            "این progression را به فارسی تحلیل کن:\n"
            "۱. نقش هارمونیک هر آکورد\n"
            "۲. حال و هوای کلی\n"
            "۳. حرکات جالب هارمونیک\n"
            "۴. پیشنهاد برای بهتر شدن"
        )

    def _suggest(self):
        self._add_user("✨ پیشنهاد هوشمند")
        ctx = self._context if self._context else "هنوز progression ای ساخته نشده"
        self._query(
            f"{ctx}\n\n"
            "لطفاً:\n"
            "۱. بهترین Key، Scale، Style و Mood را برای این پروژه پیشنهاد بده\n"
            "   در این فرمت: [SETTINGS: key=Am, scale=Natural Minor, style=Lo-fi, mood=Sad, bpm=75]\n"
            "۲. یک progression ۴ تا ۸ آکوردی کامل پیشنهاد بده\n"
            "   در این فرمت: [CHORDS: Am, F, C, G]\n"
            "۳. توضیح بده چرا این انتخاب‌ها مناسبند\n"
            "به فارسی جواب بده."
        )

    def _explain(self):
        if self._context:
            self._add_user("🎵 توضیح تئوری")
            self._query(f"{self._context}\n\nمفاهیم تئوری موسیقی این progression را به فارسی توضیح بده.")
        else:
            self._add_user("🎵 اصول هارمونی")
            self._query("اصول progression آکوردی و نقش‌های هارمونیک را برای مبتدیان به فارسی توضیح بده.")

    def _send(self):
        text = self._input.text().strip()
        if not text: return
        self._input.clear()
        self._add_user(text)
        prompt = f"{self._context}\n\nسوال: {text}" if self._context else text
        # If user asks for chords, remind AI to use format
        if any(w in text for w in ["پیشنهاد","آکورد","progression","chord"]):
            prompt += "\nاگر آکورد پیشنهاد می‌دهی، حتماً از فرمت [CHORDS: X, Y, Z] استفاده کن."
        self._query(prompt)

    # ------------------------------------------------------------------ #
    # Ollama
    # ------------------------------------------------------------------ #

    def _query(self, prompt):
        if self._thread and self._thread.is_alive(): return
        self._send_btn.setEnabled(False)
        self._bubble = self._add_ai("...")
        self._worker = OllamaWorker(prompt)
        self._worker.token_received.connect(self._on_token)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._thread = Thread(target=self._worker.run, daemon=True)
        self._thread.start()

    def _on_token(self, token):
        if self._bubble:
            if self._bubble._text == "...":
                self._bubble._text = ""
            self._bubble.append(token)
            self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            )

    def _on_done(self):
        self._send_btn.setEnabled(True)
        if self._bubble:
            self._bubble.finalize()
            # Connect apply/replace buttons to our signals
            self._bubble.chord_apply_requested.connect(self.apply_chords_requested.emit)
            self._bubble.chord_replace_requested.connect(self.replace_chords_requested.emit)
        self._bubble = None

    def _on_error(self, msg):
        if self._bubble:
            self._bubble.body.setText(f"❌ {msg}")
        self._send_btn.setEnabled(True)

    # ------------------------------------------------------------------ #
    # Chat helpers
    # ------------------------------------------------------------------ #

    def _add_user(self, text):
        b = MessageBubble(text, True)
        self._chat_l.insertWidget(self._chat_l.count() - 1, b)
        self._scroll_bottom()
        return b

    def _add_ai(self, text):
        b = MessageBubble(text, False)
        self._chat_l.insertWidget(self._chat_l.count() - 1, b)
        self._scroll_bottom()
        return b

    def _clear(self):
        while self._chat_l.count() > 1:
            item = self._chat_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _scroll_bottom(self):
        QTimer.singleShot(60, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))

    def _check_ollama(self):
        def ping():
            try:
                urllib.request.urlopen("http://localhost:11434", timeout=2)
                self._dot.setStyleSheet("color:#4ade80;font-size:10px;")
                self._dot.setText("● آنلاین")
            except:
                self._dot.setStyleSheet("color:#ef4444;font-size:10px;")
                self._dot.setText("● آفلاین — ollama serve را بزنید")
        Thread(target=ping, daemon=True).start()
