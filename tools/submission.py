#!/usr/bin/env python3
"""Turn a "Submit a farm voice" issue into a pull request (run by .github/workflows/submission.yml).

It reads the issue form (example Shorts, channels, why it's a farm, the voice file), checks it with check.py's rules,
and then either opens or updates a pull request adding the voice (or adding the channels and examples to a voice
already on the list), or comments on the issue saying what to fix. Everything in the issue is treated as data: nothing
from it is run, and the voice file is only downloaded from GitHub's own attachment addresses.

    python3 tools/submission.py --dry-run issue-body.txt     what it would do with an issue body (no GitHub needed)
"""
import datetime, glob, json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import check  # noqa: E402

VID = re.compile(r"(?:youtube\.com/(?:shorts/|watch\?v=|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})")
ATTACH = re.compile(r"https://github\.com/user-attachments/files/\d+/[^\s)\]]+?\.json")
SECTIONS = {"Example Shorts": "examples", "Channels": "channels", "Why it's a content farm": "evidence",
            "Voice file": "voice"}


def sections(body):
    """The issue form's answers: {examples, channels, evidence, voice} (text under each ### heading)."""
    out, key = {}, None
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        m = re.match(r"###\s+(.+?)\s*$", line)
        if m:
            key = SECTIONS.get(m.group(1).strip())
            if key:
                out[key] = ""
            continue
        if key:
            out[key] += line + "\n"
    return {k: v.strip() for k, v in out.items()}


def find_voice(text, download):
    """The voice file: from an attachment link, or pasted JSON. Returns (dict or None, problem)."""
    m = ATTACH.search(text or "")
    if m:
        try:
            raw = download(m.group(0))
        except Exception as ex:
            return None, f"couldn't download the voice file ({str(ex)[:60]})"
    else:
        start, end = (text or "").find("{"), (text or "").rfind("}")
        if start < 0 or end < start:
            return None, "no voice file: drag the voice-….json file from Share into the Voice file box"
        raw = text[start:end + 1].encode()
    try:
        v = json.loads(raw)
    except ValueError:
        return None, "the voice file isn't valid (use the file Share made, unchanged)"
    return (v, "") if isinstance(v, dict) else (None, "the voice file isn't valid")


def lines(text):
    out = []
    for ln in (text or "").split("\n"):
        ln = re.sub(r"^\s*[-*\d.)]+\s*", "", ln).strip()
        if ln and ln.lower() not in ("_no response_",) and ln not in out:
            out.append(ln[:100])
    return out


def plan(body, existing, download, today=None):
    """Decide what to do with one issue. existing = {id: voice dict} already on the list.
    Returns {"problems": [...]} or {"file": name, "voice": dict, "new": bool, "id": ...}."""
    s = sections(body)
    examples = list(dict.fromkeys(VID.findall(s.get("examples", ""))))
    channels = lines(s.get("channels", ""))
    voice, problem = find_voice(s.get("voice", ""), download)
    problems = [problem] if problem else []
    if len(examples) < 2:
        problems.append("at least 2 example Short links are needed")
    if len({c.lower() for c in channels}) < 2:
        problems.append("at least 2 different channels are needed")
    if problems or voice is None:
        return {"problems": problems}
    print_ = voice.get("print")
    same = next((v for v in existing.values() if check.problems(v, v["id"] + ".json") == [] and
                 isinstance(print_, list) and len(print_) == 512 and check.gap(v["print"], print_) <= check.SAME_VOICE), None)
    if same:                                            # a voice already on the list: add the new channels and Shorts
        merged = dict(same, channels=same["channels"] + [c for c in channels if c.lower() not in
                                                         {x.lower() for x in same["channels"]}],
                      examples=same["examples"] + [x for x in examples if x not in same["examples"]])
        if merged == same:
            return {"problems": [f"that's {same['id']}, already on the list with these channels and Shorts. Thanks!"]}
        return {"file": same["id"] + ".json", "voice": merged, "new": False, "id": same["id"]}
    n = max([int(m.group(1)) for k in existing for m in [re.fullmatch(r"farm-(\d{4})", k)] if m] + [0]) + 1
    vid = f"farm-{n:04d}"
    note = re.sub(r"\s+", " ", s.get("evidence", ""))[:200]
    entry = {"id": vid, "model": voice.get("model"), "added": today or datetime.date.today().isoformat(),
             "channels": channels, "examples": examples, "note": note, "print": print_}
    bad = check.problems(entry, vid + ".json")
    return {"problems": bad} if bad else {"file": vid + ".json", "voice": entry, "new": True, "id": vid}


def existing_voices():
    out = {}
    for p in glob.glob(os.path.join(HERE, "voices", "*.json")):
        with open(p) as f:
            v = json.load(f)
        out[v.get("id", os.path.basename(p)[:-5])] = v
    return out


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "yakscout-voices-bot"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read(200_001)
    if len(data) > 200_000:
        raise ValueError("too big")
    return data


def run(*args):
    return subprocess.run(list(args), check=True, capture_output=True, text=True).stdout.strip()


def comment(repo, issue, text):
    run("gh", "issue", "comment", str(issue), "--repo", repo, "--body", text)


def label(repo, issue, add):
    """Mark an issue 'incomplete' (or clear it). A failure here never stops the submission."""
    try:
        if add:
            subprocess.run(["gh", "label", "create", "incomplete", "--repo", repo, "--color", "d4c5f9",
                            "--description", "Missing something; closes itself after 30 days"], capture_output=True)
        run("gh", "issue", "edit", str(issue), "--repo", repo, "--add-label" if add else "--remove-label", "incomplete")
    except Exception:
        pass


def main():
    if "--dry-run" in sys.argv:
        with open(sys.argv[-1]) as f:
            print(json.dumps({k: (v if k != "voice" else {**v, "print": f"[{len(v['print'])} numbers]"})
                              for k, v in plan(f.read(), existing_voices(), download).items()}, indent=1))
        return
    with open(os.environ["GITHUB_EVENT_PATH"]) as f:
        event = json.load(f)
    repo, issue = os.environ["GITHUB_REPOSITORY"], int(event["issue"]["number"])
    result = plan(event["issue"].get("body", ""), existing_voices(), download)
    if result.get("problems"):
        label(repo, issue, add=True)                    # so the maintainer can skip these; the stale workflow closes them
        comment(repo, issue, "Thanks! This can't be added yet:\n\n" + "\n".join(f"- {p}" for p in result["problems"]) +
                "\n\nEdit the issue to fix it, and this check runs again. "
                "(It closes by itself after 30 days; reopen it any time.)")
        return
    label(repo, issue, add=False)
    branch = f"submission-{issue}"
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "checkout", "-B", branch)
    with open(os.path.join(HERE, "voices", result["file"]), "w") as f:
        json.dump(result["voice"], f, indent=1)
    run("git", "add", os.path.join("voices", result["file"]))
    title = (f"Add {result['id']}" if result["new"] else f"{result['id']}: more channels and Shorts") + f" (from #{issue})"
    run("git", "commit", "-m", title)
    run("git", "push", "--force", "origin", branch)
    existing = run("gh", "pr", "list", "--repo", repo, "--head", branch, "--json", "number", "--jq", ".[0].number")
    if existing:
        comment(repo, issue, f"Updated the submission: #{existing}.")
        return
    body = (f"From #{issue}. Made by the submission bot from the issue form.\n\n"
            "Maintainer: in YakTube, **Settings → Scout → Submissions → Check**, and merge if it says ✅.\n\n"
            f"Closes #{issue}")
    url = run("gh", "pr", "create", "--repo", repo, "--head", branch, "--base", "main", "--title", title, "--body", body)
    comment(repo, issue, f"Thanks! It's ready for review: {url}")


if __name__ == "__main__":
    main()
