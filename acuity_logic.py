"""
acuity_logic.py
================
Implements a proper binary search visual acuity test.

How it works:
-------------
1. Start in the MIDDLE of the Snellen chart (20/40)
2. User reads the row
3. Pass → jump UP (better vision side)
   Fail → jump DOWN (worse vision side)
4. Range narrows each round like this:

   [20/200 -------- 20/40 -------- 20/16]
                      ^
                   Start here

   Pass → [20/40 --- 20/25 --- 20/16]
                       ^
                    Try here

   Fail → [20/40 --- 20/32 --- 20/25]
                       ^
                    Try here

5. When range collapses to 1 line = that is the threshold
6. Best-of-3 confirms the threshold (need 2/3 fails to truly fail)
7. Letters are scored order-independently (set matching not position)

Clinical reference:
-------------------
Binary search acuity testing is validated in:
- Carkeet A. (2001) "Modeling logMAR visual acuity scores"
- ETDRS protocol uses similar staircase methodology
"""

import random

# ── Snellen chart — ordered worst to best ────────────────────────────────────
# Each entry: (snellen_label, denominator, diopter_estimate, description)
CHART = [
    ("20/200", 200, -5.00, "Legally blind threshold. Cannot function without strong correction."),
    ("20/160", 160, -4.00, "Severe impairment. Faces and signs unrecognisable at distance."),
    ("20/125", 125, -3.25, "High myopia. Everything beyond arm's reach is blurry."),
    ("20/100", 100, -2.50, "Significant impairment. Daily tasks without glasses are unsafe."),
    ("20/80",   80, -2.00, "Moderate-high myopia. Reading possible, distance vision poor."),
    ("20/63",   63, -1.50, "Moderate myopia. Driving without glasses is unsafe."),
    ("20/50",   50, -1.00, "Mild-moderate myopia. Glasses beneficial for distance."),
    ("20/40",   40, -0.75, "Mild myopia. Legal driving limit in most countries."),
    ("20/32",   32, -0.50, "Near-normal. Slight blur at distance, glasses optional."),
    ("20/25",   25, -0.25, "Near-normal. Very slight blur, most go uncorrected."),
    ("20/20",   20,  0.00, "Perfect normal vision. No correction needed."),
    ("20/16",   16, +0.25, "Above normal. Some people have naturally sharp vision."),
]

TOTAL = len(CHART)                  # 12 levels
SLOAN = list("CDHKNORSVZ")          # standard optometry letter set


# ── Letter set helpers ────────────────────────────────────────────────────────

def new_letters(count: int = 5) -> str:
    """Return `count` unique random Sloan letters, space-separated."""
    return " ".join(random.sample(SLOAN, min(count, len(SLOAN))))


def score_answer(user_answer: str, correct_letters: str) -> dict:
    """
    Order-independent letter scoring.

    Real optometrists count correct letters regardless of sequence.
    5 correct letters on a row = pass, regardless of order.

    Returns dict with keys: correct, total, pct, passed
    """
    user_set    = set(user_answer.strip().upper().replace(" ", ""))
    correct_set = set(correct_letters.strip().upper().replace(" ", ""))

    if not correct_set:
        return {"correct": 0, "total": 0, "pct": 1.0, "passed": True}

    correct_count = len(user_set & correct_set)   # set intersection
    total         = len(correct_set)
    pct           = correct_count / total

    # Clinical standard: 3/5 correct letters = pass on that line
    passed = correct_count >= 3

    return {
        "correct": correct_count,
        "total":   total,
        "pct":     pct,
        "passed":  passed,
    }


# ── Binary Search State Machine ───────────────────────────────────────────────

class AcuityTest:
    """
    Binary search acuity test engine.

    Usage
    -----
    test = AcuityTest()
    test.start()

    loop:
        level = test.current_level()
        letters = test.current_letters()
        # show image, get user answer
        done = test.submit_answer(user_answer)
        if done: break

    result = test.get_result()
    """

    def __init__(self):
        self.reset()

    def reset(self):
        # Binary search bounds (indices into CHART)
        self.lo          = 0                    # worst vision end
        self.hi          = TOTAL - 1            # best vision end
        self.current_idx = TOTAL // 2           # start in the middle (20/40)

        # Best-of-3 tracking for threshold confirmation
        self.attempts       = []                # list of (idx, passed) for current line
        self.confirmed_idx  = None              # threshold confirmed at this index
        self.done           = False

        # History for display
        self.history        = []                # list of {idx, label, passed, correct, total}

        # Current row letters (regenerated each attempt)
        self._letters       = new_letters()

        # Previous index — to detect when we've narrowed to 1 line
        self._prev_idx      = None

    def start(self):
        """Call once after calibration to initialise."""
        self.reset()
        self._letters = new_letters()

    def current_level(self) -> dict:
        """Return info about the current Snellen level."""
        label, denom, diopter, desc = CHART[self.current_idx]
        return {
            "index":    self.current_idx,
            "label":    label,
            "denom":    denom,
            "diopter":  diopter,
            "desc":     desc,
            "lo":       self.lo,
            "hi":       self.hi,
            "attempts": len(self.attempts),
        }

    def current_letters(self) -> str:
        """The correct answer for the current image."""
        return self._letters

    def submit_answer(self, user_answer: str) -> bool:
        """
        Submit user's answer for the current row.

        Returns True when the test is complete, False to continue.
        """
        score = score_answer(user_answer, self._letters)
        passed = score["passed"]

        # Record in history
        label = CHART[self.current_idx][0]
        self.history.append({
            "idx":     self.current_idx,
            "label":   label,
            "passed":  passed,
            "correct": score["correct"],
            "total":   score["total"],
        })

        # Track attempts on this line for best-of-3
        self.attempts.append(passed)

        # ── Decision logic ────────────────────────────────────────────────
        # Need 2 results on same line before making a decision
        if len(self.attempts) < 2:
            # First attempt — give them a second go on same line
            # with fresh letters
            self._letters = new_letters()
            return False

        # Count passes and fails across attempts on this line
        passes = sum(self.attempts)
        fails  = len(self.attempts) - passes

        if passes >= 2:
            # ── PASS this line ────────────────────────────────────────────
            # Move search range UP (toward better vision)
            self.lo = self.current_idx + 1
        else:
            # ── FAIL this line ────────────────────────────────────────────
            # Move search range DOWN (toward worse vision)
            self.hi = self.current_idx - 1

        # Reset attempt tracker for next line
        self.attempts = []

        # ── Check if search is complete ───────────────────────────────────
        if self.lo > self.hi:
            # Range collapsed — threshold found
            # Best result is lo-1 (last passed line) or hi (if started failing from top)
            self.confirmed_idx = max(0, self.lo - 1)
            self.done = True
            return True

        # ── Move to next binary search position ──────────────────────────
        # New midpoint of remaining range
        next_idx = (self.lo + self.hi) // 2

        # Safety: if we'd go to same line, nudge
        if next_idx == self.current_idx:
            if passes >= 2:
                next_idx = min(self.hi, self.current_idx + 1)
            else:
                next_idx = max(self.lo, self.current_idx - 1)

        # If range is down to 1 line remaining, do a tie-break attempt
        if self.lo == self.hi:
            self.confirmed_idx = self.lo
            self.done = True
            return True

        self._prev_idx  = self.current_idx
        self.current_idx = next_idx
        self._letters    = new_letters()
        return False

    def skip_line(self) -> bool:
        """
        Called when user presses 'Cannot See' without attempting.
        Counts as a direct fail on current line.
        """
        label = CHART[self.current_idx][0]
        self.history.append({
            "idx":     self.current_idx,
            "label":   label,
            "passed":  False,
            "correct": 0,
            "total":   5,
        })
        self.attempts.append(False)
        self.attempts.append(False)   # instant 2 fails = definite fail
        return self.submit_answer("")  # trigger decision with empty answer

    def get_result(self) -> dict:
        """
        Return final result after test is complete.
        """
        if not self.done:
            return {"done": False}

        idx = self.confirmed_idx if self.confirmed_idx is not None else self.current_idx
        idx = max(0, min(idx, TOTAL - 1))

        label, denom, diopter, desc = CHART[idx]

        # Build prescription advice
        advice = _prescription_advice(diopter)

        return {
            "done":         True,
            "index":        idx,
            "label":        label,
            "denom":        denom,
            "diopter":      diopter,
            "desc":         desc,
            "advice":       advice,
            "history":      self.history,
            "total_rows":   len(self.history),
        }


# ── Prescription advice ───────────────────────────────────────────────────────

def _prescription_advice(diopter: float) -> dict:
    if diopter == 0.0:
        return {
            "title":    "No Glasses Needed",
            "rx":       "0.00 D (Plano)",
            "category": "Normal",
            "detail":   "Your vision tests at 20/20. No corrective lenses required.",
            "urgency":  "none",
            "type":     "Normal Vision",
            "color":    "#43e8b0",
        }

    abs_d = abs(diopter)
    side  = "Myopia" if diopter < 0 else "Hyperopia"
    tasks = "distance (driving, boards, screens)" if diopter < 0 else "near (reading, phone, computer)"

    if abs_d <= 0.25:
        category, urgency = "Trace",    "none"
        detail = f"Trace {side.lower()}. No glasses needed yet — monitor annually."
        color  = "#43e8b0"
    elif abs_d <= 0.75:
        category, urgency = "Mild",     "low"
        detail = f"Mild {side.lower()}. Glasses optional but helpful for {tasks}."
        color  = "#ffd000"
    elif abs_d <= 1.50:
        category, urgency = "Moderate", "moderate"
        detail = f"Moderate {side.lower()}. Regular glasses or contacts recommended for {tasks}."
        color  = "#ffa500"
    elif abs_d <= 3.00:
        category, urgency = "High",     "high"
        detail = f"High {side.lower()}. Full-time corrective lenses needed for safe daily function."
        color  = "#ff6584"
    else:
        category, urgency = "Severe",   "urgent"
        detail = f"Severe {side.lower()}. Strong prescription essential. See an optometrist urgently."
        color  = "#ff3366"

    return {
        "title":    f"Estimated Prescription: {diopter:+.2f} D",
        "rx":       f"{diopter:+.2f} D Spherical Equivalent",
        "category": category,
        "detail":   detail,
        "urgency":  urgency,
        "type":     side,
        "color":    color,
    }