from pathlib import Path

root = Path(r"c:\Users\Anshu Shukla\OneDrive\Desktop\BeyondyourBubble\backend")
files = [
    root / "accounts" / "serializers.py",
    root / "accounts" / "views.py",
]
for p in files:
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    bad_idx = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("\\n") or line.startswith("\\n"):
            bad_idx = i
            break
    if bad_idx is None:
        print("no bad line", p)
        continue
    head = "".join(lines[:bad_idx])
    corrupt = lines[bad_idx].rstrip("\r\n")
    decoded = corrupt.encode("utf-8").decode("unicode_escape")
    if not decoded.startswith("\n"):
        decoded = "\n" + decoded
    p.write_text(head + decoded, encoding="utf-8")
    print("fixed", p, "bad_idx", bad_idx+1)