#!/usr/bin/env python3
"""Listen to the example Shorts of each voice file given and report how close each one's voice is to the file's
voiceprint, as a Markdown table (for a pull request's check summary).

    python3 tools/verify_pr.py <path to YakScout's scout.py folder> voices/farm-0003.json ...

Starts with a plain verdict (✅ checks out, ❌ don't merge, ⏸ couldn't check yet). Exits 1 unless the voice checked
out: an example with a different voice, or none that could be heard (YouTube sometimes refuses GitHub's servers)."""
import json, os, sys


def main(scout_dir, paths):
    sys.path.insert(0, os.path.abspath(scout_dir))
    import scout
    lines, different, measured, unchecked = [], 0, 0, 0
    for path in paths:
        try:
            with open(path) as f:
                entry = json.load(f)
        except (OSError, ValueError) as ex:
            lines += [f"### `{path}`", f"Couldn't read it: {ex}", ""]
            continue
        if not scout.good_print(entry.get("print")):
            lines += [f"### `{path}`", "No voiceprint in it (see check.py's message).", ""]
            continue
        lines += [f"### `{entry.get('id', path)}`", "", f"Channels: {', '.join(entry.get('channels', [])) or '-'}", "",
                  "| Example | Its channel | Gap | Result |", "|---|---|---|---|"]
        for vid, channel, gap in scout.verify_entry(entry):
            link = f"[{vid}](https://www.youtube.com/shorts/{vid})"
            if isinstance(gap, float):
                ok = gap <= scout.VOICE_MATCH
                different += not ok
                measured += 1
                lines.append(f"| {link} | {channel or '?'} | {gap + 0.0:.3f} | {'same voice' if ok else '**different voice**'} |")
            else:
                lines.append(f"| {link} | {channel or '?'} | - | couldn't check: {gap or 'no talking at the start'} |")
                unchecked += 1
        lines.append("")
    if different:
        verdict = "❌ **Don't merge.** Some example Shorts have a different voice from the one submitted."
    elif measured and not unchecked:
        verdict = "✅ **The voice checks out.** Every example Short has the submitted voice. Last step: look at the channels " \
                  "(lots of near-identical Shorts, not one person's channel), then merge."
    elif measured:
        verdict = "✅ **Mostly checked.** The examples that could be heard have the submitted voice; the rest couldn't be " \
                  "fetched. Look at the channels, then merge."
    else:
        verdict = "⏸ **Couldn't check yet.** YouTube didn't let GitHub listen to any example. Don't merge yet: re-run " \
                  "this check later (Re-run jobs), or ask for it to be checked at home."
    lines = [verdict, ""] + lines + [f"(Same voice = gap {scout.VOICE_MATCH} or less.)"]
    text = "\n".join(lines) + "\n"
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("## Voice check\n\n" + text)
    return 1 if different or not measured else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2:]))
