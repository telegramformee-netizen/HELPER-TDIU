"""
analyzer.py — Ball tahlili: xavf hisoblash, kerakli ball
"""
from dataclasses import dataclass
from typing import Optional

PASS_THRESHOLD = 55.0
MAX_FINAL      = 50.0
NB_LIMIT       = 0.20   # 20%


@dataclass
class Analysis:
    subject:        str
    current:        Optional[float]
    midterm:        Optional[float]
    final:          Optional[float]
    total:          Optional[float]
    fail_risk:      bool
    needed_final:   Optional[float]
    already_failed: bool
    attendance_pct: Optional[float]
    nb_warning:     bool
    letter:         Optional[str]


def analyze(subject, cur, mid, fin, total_hours, missed_hours, semester="") -> Analysis:
    c = cur or 0.0
    m = mid or 0.0

    if fin is not None:
        total = c + m + fin
        fail_risk     = total < PASS_THRESHOLD
        already_failed = fail_risk
        needed_final  = None
    else:
        needed = PASS_THRESHOLD - c - m
        if needed <= 0:
            fail_risk, needed_final, already_failed = False, 0.0, False
        elif needed > MAX_FINAL:
            fail_risk, needed_final, already_failed = True, None, False
        else:
            fail_risk     = needed >= MAX_FINAL * 0.85
            needed_final  = round(needed, 1)
            already_failed = False
        total = c + m

    att_pct, nb_warn = None, False
    if total_hours and total_hours > 0:
        missed   = missed_hours or 0
        att_pct  = round((total_hours - missed) / total_hours * 100, 1)
        nb_warn  = (missed / total_hours) >= NB_LIMIT

    return Analysis(
        subject=subject, current=cur, midterm=mid, final=fin,
        total=total, fail_risk=fail_risk, needed_final=needed_final,
        already_failed=already_failed, attendance_pct=att_pct,
        nb_warning=nb_warn, letter=_letter(total if fin else None)
    )


def _letter(score):
    if score is None: return None
    if score >= 86: return "A"
    if score >= 71: return "B"
    if score >= 55: return "C"
    return "D"


def risk_text_uz(a: Analysis) -> Optional[str]:
    parts = []
    if a.already_failed:
        parts.append(f"❌ <b>{a.subject}</b>: {a.total:.1f} ball — siz o'ta olmadingiz! Qayta topshirish kerak.")
    elif a.fail_risk and a.needed_final is None:
        parts.append(f"🚫 <b>{a.subject}</b>: Maksimal ball olsangiz ham o'ta olmaysiz!")
    elif a.fail_risk and a.needed_final:
        parts.append(f"🟠 <b>{a.subject}</b>: O'tish uchun yakuniyda <b>{a.needed_final}/50</b> kerak.")
    if a.nb_warning:
        parts.append(f"📍 <b>{a.subject}</b>: Davomat {a.attendance_pct:.0f}% — 20% chegarasiga yaqin!")
    return "\n".join(parts) if parts else None
