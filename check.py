#!/usr/bin/env python3
"""Check every voice in voices/ and build voices.json, the list YakScout downloads.

    python3 check.py           check, then (re)build voices.json
    python3 check.py --check   check, and fail if voices.json isn't up to date (what GitHub runs on each pull request)

Only Python's standard library: no installs needed."""
import datetime, glob, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_ID = "campplus-en-voxceleb-16k/fbank80-2s-avg/1"   # must match YakScout's MODEL_ID
SAME_VOICE = 0.25                                        # YakScout's match limit: closer than this is one voice
ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{2,39}")
VID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
FIELDS = {"id", "model", "added", "channels", "examples", "note", "print"}


def problems(v, filename):
    """What's wrong with one voice file (an empty list if nothing)."""
    out = []
    if not isinstance(v, dict):
        return ["not a JSON object"]
    extra = set(v) - FIELDS
    if extra:
        out.append(f"unexpected fields: {', '.join(sorted(extra))}")
    if not (isinstance(v.get("id"), str) and ID_RE.fullmatch(v["id"])):
        out.append("id: 3-40 lower-case letters, digits and dashes")
    elif filename != v["id"] + ".json":
        out.append(f"the file must be named {v['id']}.json")
    if v.get("model") != MODEL_ID:
        out.append(f"model must be {MODEL_ID} (re-learn the voice with an up-to-date YakScout)")
    try:
        datetime.date.fromisoformat(v.get("added", ""))
    except (TypeError, ValueError):
        out.append("added: a date like 2026-11-14")
    ch = v.get("channels")
    if not (isinstance(ch, list) and all(isinstance(c, str) and 0 < len(c) <= 100 for c in ch)):
        out.append("channels: a list of channel names")
    elif len({c.lower() for c in ch}) < 2:
        out.append("channels: at least 2 different channels (one channel's voice isn't evidence of a farm)")
    ex = v.get("examples")
    if not (isinstance(ex, list) and all(isinstance(x, str) and VID_RE.fullmatch(x) for x in ex)):
        out.append("examples: a list of 11-character YouTube video ids")
    elif len(set(ex)) < 2:
        out.append("examples: at least 2 Shorts (reviewers listen to them)")
    if not isinstance(v.get("note", ""), str) or len(v.get("note", "")) > 200:
        out.append("note: up to 200 characters")
    p = v.get("print")
    if not (isinstance(p, list) and len(p) == 512 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in p)):
        out.append("print: 512 numbers (the voiceprint YakScout's Share makes)")
    elif abs(math.sqrt(sum(x * x for x in p)) - 1) > 0.01:
        out.append("print: not a unit-length voiceprint (don't edit it by hand)")
    return out


def gap(p, q):
    return 1 - sum(x * y for x, y in zip(p, q))


def main(check_only=False):
    voices, bad = [], 0
    for path in sorted(glob.glob(os.path.join(HERE, "voices", "*.json"))):
        name = os.path.basename(path)
        try:
            with open(path) as f:
                v = json.load(f)
        except ValueError as ex:
            print(f"{name}: not valid JSON ({ex})")
            bad += 1
            continue
        why = problems(v, name)
        for w in why:
            print(f"{name}: {w}")
        bad += bool(why)
        if not why:
            voices.append(v)
    for i, a in enumerate(voices):                      # the same voice twice: merge them (add channels/examples)
        for b in voices[i + 1:]:
            if gap(a["print"], b["print"]) <= SAME_VOICE:
                print(f"{a['id']} and {b['id']} are the same voice ({gap(a['print'], b['print']):.2f} apart): merge them")
                bad += 1
    if bad:
        print(f"{bad} problem(s); voices.json not built")
        return 1
    voices.sort(key=lambda v: v["id"])
    out = {"format": "yakscout-voices", "version": 1, "model": MODEL_ID, "voices": voices}
    text = json.dumps(out, separators=(",", ":")) + "\n"
    target = os.path.join(HERE, "voices.json")
    try:
        with open(target) as f:
            current = f.read()
    except OSError:
        current = ""
    if check_only:
        if current != text:
            print("voices.json is out of date: run python3 check.py and commit it")
            return 1
        print(f"OK: {len(voices)} voices, voices.json up to date")
        return 0
    with open(target, "w") as f:
        f.write(text)
    print(f"OK: {len(voices)} voices; built voices.json")
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv[1:]))
