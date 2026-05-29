"""
install.py
Run this from Downloads folder to install all updated files.
Usage: python install.py
"""
import os
import shutil

SRC = os.path.dirname(os.path.abspath(__file__))
DST = r"E:\App Creator"

FILES = [
    # (source_filename, destination_relative_path)
    ("main.py",               "main.py"),
    ("project.py",            r"core\project.py"),
    ("harmony_engine.py",     r"core\harmony_engine.py"),
    ("control_panel.py",      r"ui\control_panel.py"),
    ("suggestion_panel.py",   r"ui\suggestion_panel.py"),
    ("timeline_panel.py",     r"ui\timeline_panel.py"),
    ("main_window.py",        r"ui\main_window.py"),
    ("ai_panel.py",           r"ui\ai_panel.py"),
    ("bass_generator.py",     r"generators\bass_generator.py"),
    ("melody_generator.py",   r"generators\melody_generator.py"),
    ("arpeggio_generator.py", r"generators\arpeggio_generator.py"),
    ("drum_generator.py",     r"generators\drum_generator.py"),
    ("midi_exporter.py",      r"generators\midi_exporter.py"),
    ("audio_preview.py",      r"generators\audio_preview.py"),
]

print("=" * 50)
print("  MIDI Composer — File Installer")
print("=" * 50)

ok = 0
skip = 0

for src_name, dst_rel in FILES:
    src_path = os.path.join(SRC, src_name)
    dst_path = os.path.join(DST, dst_rel)

    if not os.path.exists(src_path):
        print(f"  SKIP  {src_name}  (not in Downloads)")
        skip += 1
        continue

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    shutil.copy2(src_path, dst_path)
    print(f"  OK    {src_name}  →  {dst_rel}")
    ok += 1

# Clear pycache
print("\n  Clearing __pycache__...")
for folder in ["core", "ui", "generators", ""]:
    cache = os.path.join(DST, folder, "__pycache__")
    if os.path.exists(cache):
        shutil.rmtree(cache)
        print(f"  Cleared {cache}")

print(f"\n{'='*50}")
print(f"  Done: {ok} files installed, {skip} skipped")
print(f"{'='*50}")
print(f"\n  Now run:")
print(f'  cd /d "{DST}"')
print(f"  python main.py")
input("\nPress Enter to exit...")
