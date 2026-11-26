#!/usr/bin/env python3
"""The Internet in One Word -- entry builder (FINAL).

The competition entry is exactly ONE word written to entry.txt in
MAKEFUN_OUTPUT_DIR (default /output), UTF-8, 1-30 chars, NO trailing
newline. The judge (per RULES.txt) compares words pairwise, weighing,
in order:
  1. A single word that captures the WHOLE internet (not a phrase/list).
  2. Earns a laugh by itself, no explanation needed.
  3. True about the internet as a whole, not one app/site/mood.
  4. Surprising -- not the first obvious word anyone would reach for.
  5. Lands in one beat: correctly spelled, instantly readable, short.

This program holds a pool of candidates (dictionary words + coined
portmanteaus/neologisms), scores each on those criteria, and writes
only the winner.

JURI KEJAM (harsh-judge) ROUND 1 -- draft pass:
  - Obvious dictionary words (Chaos, Everything, Noise, Memes) are
    penalised on surprise: the judge has seen them a thousand times.
  - Narrow words (Cats, TikTok-ish moods, one app) are penalised on
    whole-internet fit.
  - Long words (>13 chars) are penalised on the one-beat test.
  - Shock-only words score low on fit.
JURI KEJAM ROUND 2 -- head-to-head of the draft finalists:
  - Scrolliosis vs Doomloop: Doomloop is shorter and punchier, but
    "doom" narrows it to ONE mood (bad news), which the brief's
    criterion 3 explicitly discounts. Scrolliosis names the behaviour
    everyone performs on every app. Doomloop fit 8 -> 7.
  - Scrolliosis vs Scrollnosis: "-nosis" (hypnosis) parses slower;
    "-osis" is the instantly recognised medical suffix AND carries a
    second joke -- scoliosis, the hunched spine of a person bent over
    a screen. Two laugh layers in one word; Scrolliosis stays top.
  - Scrolliosis vs Infobesity: Infobesity is a pre-existing term, so
    it is less surprising (7 -> 6), and it covers only information
    volume, not the behavioural loop that IS the modern internet.
  - Scrolliosis vs Buffering: a real dictionary contender, but
    buffering is one (increasingly rare) experience, not the whole.
  Verdict: "Scrolliosis" -- a fake diagnosis for the whole internet:
  the endless-scroll condition. Funny with zero explanation, true of
  every platform at once, nobody's first obvious reach, and it still
  lands in one beat (scroll-ee-OH-sis, 11 chars).

The final program also verifies the winner the way the judge decides:
pairwise duels down the brief's criteria in order (see duel()), and a
read-back byte check of the written file.
"""

import os
import sys

# Each candidate: (word, kind, funny, fit, surprise, readability)
# Sub-scores are 0-10, curated against the judge's brief.
#   funny       -- laughs with zero explanation
#   fit         -- true of the whole internet, not one corner of it
#   surprise    -- not the first word anyone would reach for
#   readability -- instantly parseable / pronounceable in one beat
CANDIDATES = [
    # --- dictionary words ---
    ("Chaos",           "dict",   4, 8, 2, 10),
    ("Everything",      "dict",   3, 9, 2, 10),
    ("Noise",           "dict",   3, 7, 3, 10),
    ("Memes",           "dict",   6, 6, 3, 10),
    ("Cats",            "dict",   6, 4, 4, 10),
    ("Scroll",          "dict",   4, 8, 4, 10),
    ("Buffering",       "dict",   7, 7, 5,  9),
    ("Distraction",     "dict",  5, 9, 3,  9),
    ("Addiction",       "dict",   4, 8, 3,  9),
    ("Procrastination", "dict",   6, 7, 4,  6),
    ("Infinite",        "dict",   3, 8, 3, 10),
    ("Clickbait",       "dict",   6, 7, 4,  9),
    ("Viral",           "dict",   4, 7, 3, 10),
    ("Again",           "dict",   5, 6, 6, 10),
    # --- coined words / portmanteaus ---
    ("Scrolliosis",     "coined", 9, 9, 9,  8),
    ("Doomloop",        "coined", 7, 7, 7, 10),
    ("Infobesity",      "coined", 8, 8, 6,  8),
    ("Tabocalypse",     "coined", 8, 6, 8,  8),
    ("Clicknosis",      "coined", 8, 8, 8,  7),
    ("Scrollnosis",     "coined", 8, 9, 8,  7),
    ("Memeverything",   "coined", 7, 8, 7,  6),
    ("Doomscrolltopia", "coined", 7, 8, 7,  5),
    ("Procrastinet",    "coined", 7, 7, 8,  7),
    ("Catspiracy",      "coined", 7, 5, 8,  8),
]


def score(word, kind, funny, fit, surprise, readability):
    """Weighted total following the judge's priority order.

    Fit and funny dominate (criteria 1-3 in the brief are really
    'captures the whole internet' + 'funny' + 'true'), surprise is
    the tie-breaker that separates coined words from dictionary
    defaults, readability/length is the one-beat gate.
    """
    total = 3.0 * fit + 3.0 * funny + 2.0 * surprise + 1.5 * readability
    # One-beat penalty: every character past 10 costs a little.
    total -= max(0, len(word) - 10) * 0.8
    # A coined word that still reads instantly gets a small bonus:
    # it is the only way to be both fitting AND surprising.
    if kind == "coined" and readability >= 8:
        total += 2.0
    return total


def duel(a, b):
    """Pairwise verdict the way the judge's brief prescribes.

    Go through the criteria in the brief's order -- whole-internet
    fit, funny, true-of-the-whole (folded into fit), surprise, then
    one-beat readability/length -- and let the FIRST criterion where
    the two differ decide, unless a later criterion differs by much
    more (>= 5 points), in which case that later one decides.
    Returns True when candidate a beats candidate b.
    """
    def keys(c):
        word, _kind, funny, fit, surprise, readability = c
        one_beat = readability - max(0, len(word) - 10)
        return (fit, funny, surprise, one_beat)

    ka, kb = keys(a), keys(b)
    decision = None
    for i, (x, y) in enumerate(zip(ka, kb)):
        if x != y:
            decision = (i, x - y)
            break
    if decision is None:
        # Identical on every criterion: the judge's tie-break in the
        # brief is the smaller text, then the earlier receipt.
        return len(a[0]) <= len(b[0])
    idx, diff = decision
    for x, y in zip(ka[idx + 1:], kb[idx + 1:]):
        if abs(x - y) >= 5 and (x - y) * diff < 0:
            return x > y
    return diff > 0


def pick_winner():
    ranked = sorted(
        CANDIDATES,
        key=lambda c: score(*c),
        reverse=True,
    )
    return ranked[0][0], ranked


def main():
    winner, ranked = pick_winner()
    # The winner must also survive pairwise duels against the five
    # strongest rivals, judged the way the real judge judges.
    champ = ranked[0]
    for rival in ranked[1:6]:
        assert duel(champ, rival), f"{winner} loses a duel to {rival[0]}"
    # Gate self-check, mirroring RULES.txt: UTF-8, 1-30 chars,
    # not only whitespace, exactly one word, no trailing newline.
    assert 1 <= len(winner) <= 30, winner
    assert winner.strip() == winner and " " not in winner, winner
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.txt")
    # newline="" + explicit no trailing newline: the file must be
    # exactly the word and nothing else.
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(winner)
    # Read-back byte check: exactly the word's UTF-8 bytes, nothing
    # more -- in particular no trailing newline.
    raw = open(out_path, "rb").read()
    assert raw == winner.encode("utf-8"), raw
    assert not raw.endswith(b"\n"), raw
    assert 1 <= len(raw.decode("utf-8")) <= 30, raw
    print(f"winner: {winner} ({len(winner)} chars) -> {out_path}")
    for c in ranked[:5]:
        print(f"  runner-up pool: {c[0]:<16} score={score(*c):.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
