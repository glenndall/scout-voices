# YakScout Voices

## 1. Overview & Purpose

- **What it is:** a shared, community-reviewed list of the synthetic voices that YouTube content farms reuse across
  channel after channel. [YakScout](https://github.com/glenndall/yakscout) downloads it once a day and uses it alongside
  the voices each person teaches it, so a farm one person catches is caught for everyone.
- **Why voices:** farms open new channels faster than anyone can list them, but they keep the same text-to-speech
  voice. A voice on the list is recognised on a brand-new channel the first time it posts.
- **What it isn't:** a list of AI content. People make clever, funny things with AI voices; only voices with evidence
  of being reused across several farm channels belong here. And never a real person's voice.

## 2. How the List Works

- Each farm voice is one small file in [`voices/`](voices/): a **voiceprint** (512 numbers describing how the voice
  sounds, not a recording), the **channels** it has been heard on, and **example Shorts** as evidence.
- [`check.py`](check.py) checks every file and builds [`voices.json`](voices.json), the single file YakScout downloads.
  GitHub checks every pull request, listens to its example Shorts, and rebuilds `voices.json` after each merge.
- A voice heard on 2 or more channels counts for 50 points in YakScout, enough to drop a Short by itself (see
  YakScout's README).
- Voiceprints are only comparable when made by the same model and method, so every file names its `model`. If
  YakScout ever changes how it makes voiceprints, the list moves to a new model id together with it.

**Current voices**

| Voice | Heard on | Examples |
|---|---|---|
| `farm-0001` | Drip Dyl, Volze, GreenBroRants, Gneef | 5 |
| `farm-0002` | BreezyBEE, SensBlox | 3 |

## 3. Using the List

- **YakScout 0.6 or later uses it automatically:** nothing to set up. It downloads
  `https://raw.githubusercontent.com/glenndall/yakscout-voices/main/voices.json` at start-up and once a day, and keeps
  it in `shared-voices.json` next to its own `voices.json`.
- **Download it now:** `python scout.py lists`.
- **Hide a voice for yourself:** **×** on it in YakTube's **Settings → YakScout → Voices**. The list itself is untouched.
- **Other lists, or none:** set `SCOUT_LISTS` to one or more list URLs (space-separated), or to `off`.
- **Other projects:** `voices.json` is plain JSON (see section 7) and free to use under the MIT license.

## 4. Contributing a Voice

1. **Teach YakScout the voice** from at least 2 farm Shorts on 2 different channels: in YakTube, **Settings →
   YakScout → Voices → Learn**, or `python scout.py learn <link>`. Learning a voice it already knows adds the channel
   and the Short to it.
2. **Make the submission file:** `python scout.py share <voice name>` writes `voice-<name>.json`, holding its
   voiceprint, channels and example Shorts.
3. **Rename it** to a free id (`farm-0003.json`, with the same `id` inside) and add a short `note` describing the
   Shorts (e.g. "Roblox story Shorts that open 'In this world, everyone ...'").
4. **Check it (optional):** put it in `voices/` and run `python3 check.py --check`. GitHub runs the same check.
5. **Open a pull request** adding just your file. Say how you know the channels are farms. You don't need to touch
   `voices.json`: GitHub rebuilds it after the merge.

If it's a voice already on the list, `check.py` says so: add your channels and examples to that file instead.

## 5. Review Process

- **check (automatic):** makes sure each file is complete, has its evidence, uses the right model, and isn't a voice
  already on the list.
- **verify (automatic):** listens to every example Short with YakScout and posts a plain verdict as a comment on the
  pull request: ✅ the voice checks out, ❌ don't merge (an example has a different voice), or 🏠 check it at
  home (usually: YouTube doesn't let GitHub listen). A table under it shows each example.
- **At home (YakTube's Submissions list):** YouTube usually refuses GitHub's servers, so the maintainer's YakTube
  does the listening: **Settings → YakScout → Submissions → Check** runs the voice check and the titles & captions farm
  check on every open pull request and shows one verdict (✅ looks good to merge, ⚠️ look at the channels, ❌ don't
  merge, ⏸ couldn't check yet).
- **Final approval (the maintainer):** read the verdict, glance at the channels (lots of near-identical Shorts, not one
  person's channel), and press **Merge** on GitHub. Nothing reaches the list without that.
- **build (automatic):** after the merge, GitHub rebuilds `voices.json`; every YakScout picks it up within a day.
- **Not merged:** a single channel, examples that don't match, or any sign that it's a real person's voice.
- **Removal:** if a voice catches honest creators, or you believe it's yours, open an issue with an example. Voices
  that do more harm than good are removed.

## 6. Responsible Use & Rules

- **Synthetic farm voices only.** Never submit a real person's voice, and never use this list or YakScout to identify,
  follow or profile people. Recognising someone by their voice can be biometric processing, which privacy laws (for
  example the GDPR and Illinois' BIPA) restrict without consent.
- **Evidence, not guesses.** Every voice needs 2 or more channels and 2 or more example Shorts that reviewers can
  listen to.
- **A match isn't proof.** It means two voices sound alike. Stock voices are used by honest creators too, which is why
  YakScout has **Never drop** and **Bring back**.
- **No poisoning.** Submitting an honest creator's voice to get them blocked is the one thing this list must not
  allow; reviewers check, and bad-faith submitters are blocked.

## 7. File Format (For Integrations)

`voices.json`:
```json
{"format": "yakscout-voices", "version": 1, "model": "campplus-en-voxceleb-16k/fbank80-2s-avg/1",
 "voices": [{"id": "farm-0001", "model": "...", "added": "2026-11-14",
             "channels": ["Drip Dyl", "Volze"], "examples": ["tbQTA6u4lEM", "AeyLzuVhr1s"],
             "note": "...", "print": [0.0123, -0.0456, "... 512 numbers, unit length"]}]}
```
- Two voiceprints are the same voice when `1 - (p · q)` is 0.25 or less.
- The voiceprint comes from the CAM++ model (3D-Speaker), fed the first 15 seconds of a Short's original audio in
  2-second pieces and averaged; YakScout's README has the details.

## License

MIT. See [LICENSE](LICENSE).
