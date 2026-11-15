"""Deterministic training-load numbers and caps for Garmin Coach.

The coach (an LLM) must not do this arithmetic in its head: run this script and use its numbers.

    uv run --no-project --python 3.12 python scripts/load.py                  # summary + caps for next week
    uv run --no-project --python 3.12 python scripts/load.py --check-km 42 --check-long 14
                                                                              # gate a draft plan: exit 1 if over a cap

Reads data/activities.json (falls back to examples/data/ and says so). Running activities only.
Load per run = Garmin "activityTrainingLoad" when most runs have it, otherwise duration in minutes.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_TYPES = ("running", "track_running", "treadmill_running", "trail_running", "street_running",
             "indoor_running", "virtual_run")

# Rules (also described in CLAUDE.md, "Prescribing"). Change them here, not in the prompt.
MAX_WEEKLY_INCREASE = 0.10   # next week's km <= base * 1.10
LONG_RUN_INCREASE = 0.10     # longest run <= longest of the last 4 weeks * 1.10
LONG_RUN_SHARE = 0.35        # ... and <= 35 % of the weekly cap (whichever is larger of the two limits for very low volume)
ACWR_CAUTION, ACWR_HIGH = 1.3, 1.5
MONOTONY_HIGH = 2.0
STALE_DAYS = 3


def load_runs(data_dir: Path) -> list[dict]:
    acts = json.loads((data_dir / "activities.json").read_text(encoding="utf-8"))
    runs = []
    for a in acts:
        kind = a.get("type") or (a.get("activityType") or {}).get("typeKey") or ""
        if kind not in RUN_TYPES:
            continue
        try:
            d = datetime.strptime(str(a["startTimeLocal"])[:10], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        runs.append({
            "date": d,
            "km": (a.get("distance") or 0) / 1000,
            "min": (a.get("duration") or 0) / 60,
            "tl": a.get("activityTrainingLoad"),
        })
    return sorted(runs, key=lambda r: r["date"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="data folder (default: data/, else examples/data/)")
    ap.add_argument("--today", default=None, help="YYYY-MM-DD (default: today)")
    ap.add_argument("--weeks", type=int, default=8, help="weeks to show")
    ap.add_argument("--check-km", type=float, default=None, help="planned km for next week")
    ap.add_argument("--check-long", type=float, default=None, help="planned longest run (km)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if args.data:
        data_dir, demo = Path(args.data), False
    elif (ROOT / "data" / "activities.json").exists():
        data_dir, demo = ROOT / "data", False
    else:
        data_dir, demo = ROOT / "examples" / "data", True
    runs = load_runs(data_dir)
    if not runs:
        print(f"No running activities in {data_dir}")
        return 2

    today = date.fromisoformat(args.today) if args.today else date.today()
    with_tl = sum(1 for r in runs[-30:] if r["tl"])
    use_tl = with_tl >= 0.8 * min(30, len(runs))
    unit = "Garmin training load" if use_tl else "minutes"

    def load_of(r):
        return (r["tl"] or 0) if use_tl else r["min"]

    # Weekly table (Monday-based), complete weeks only + current partial week
    this_monday = today - timedelta(days=today.weekday())
    weeks = []
    for i in range(max(args.weeks, 6), -1, -1):  # always enough weeks for the 4-week average
        start = this_monday - timedelta(weeks=i)
        wr = [r for r in runs if start <= r["date"] < start + timedelta(days=7)]
        weeks.append({
            "monday": start.isoformat(),
            # On Sunday (when the weekly review runs) the current week counts as done
            "complete": i > 0 or today.weekday() == 6,
            "runs": len(wr),
            "km": round(sum(r["km"] for r in wr), 1),
            "hours": round(sum(r["min"] for r in wr) / 60, 1),
            "longest_km": round(max((r["km"] for r in wr), default=0), 1),
            "load": round(sum(load_of(r) for r in wr)),
        })
    complete = [w for w in weeks if w["complete"]]
    last4 = complete[-4:]

    # Acute:chronic workload ratio (rolling 7 vs 28 days, ending yesterday)
    end = today
    daily = {}
    for r in runs:
        if end - timedelta(days=28) <= r["date"] < end:
            daily[r["date"]] = daily.get(r["date"], 0) + load_of(r)
    acute = sum(v for d, v in daily.items() if d >= end - timedelta(days=7))
    chronic_week = sum(daily.values()) / 4
    acwr = round(acute / chronic_week, 2) if chronic_week else None

    # Foster monotony over the last 7 days (rest days count as 0)
    last7 = [daily.get(end - timedelta(days=k), 0) for k in range(1, 8)]
    sd = statistics.pstdev(last7)
    monotony = round(statistics.mean(last7) / sd, 2) if sd else None
    strain = round(sum(last7) * monotony) if monotony else None

    # Caps for next week
    last_full = complete[-1]["km"] if complete else 0
    avg4 = round(sum(w["km"] for w in last4) / len(last4), 1) if last4 else 0
    base = max(last_full, avg4)
    cap_km = round(base * (1 + MAX_WEEKLY_INCREASE), 1)
    if acwr is not None and acwr > ACWR_CAUTION:
        cap_km = round(min(cap_km, avg4), 1)
    longest4 = max((w["longest_km"] for w in last4), default=0)
    cap_long = round(max(longest4 * (1 + LONG_RUN_INCREASE), 0), 1)
    cap_long = round(min(cap_long, max(cap_km * LONG_RUN_SHARE, longest4)), 1)

    last_date = runs[-1]["date"]
    flags = []
    if demo:
        flags.append("DEMO DATA (examples/data): not this athlete's real training")
    if (today - last_date).days > STALE_DAYS:
        flags.append(f"data is stale: last run {last_date} ({(today - last_date).days} days ago) - sync first")
    if acwr is not None and acwr > ACWR_HIGH:
        flags.append(f"ACWR {acwr} > {ACWR_HIGH}: load spike - hold or reduce volume next week")
    elif acwr is not None and acwr > ACWR_CAUTION:
        flags.append(f"ACWR {acwr} > {ACWR_CAUTION}: rising fast - cap set to the 4-week average")
    if monotony is not None and monotony > MONOTONY_HIGH:
        flags.append(f"monotony {monotony} > {MONOTONY_HIGH}: too little variation between days - add a rest/easy day")
    if last4 and last_full < 0.6 * avg4:
        flags.append("last week far below the 4-week average (break, illness?) - ask before building on it")

    check = []
    if args.check_km is not None:
        check.append(("weekly km", args.check_km, cap_km))
    if args.check_long is not None:
        check.append(("longest run km", args.check_long, cap_long))
    failed = [c for c in check if c[1] > c[2]]

    out = {
        "data": str(data_dir), "demo": demo, "today": today.isoformat(), "last_run": last_date.isoformat(),
        "load_unit": unit, "weeks": weeks, "avg4_km": avg4, "acwr": acwr, "monotony_7d": monotony,
        "strain_7d": strain, "cap_next_week_km": cap_km, "cap_long_run_km": cap_long, "flags": flags,
        "check": [{"what": w, "planned": p, "cap": c, "ok": p <= c} for w, p, c in check],
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Data: {data_dir}{'  [DEMO]' if demo else ''}, last run {last_date}, load unit: {unit}\n")
        print("| Week (Mon) | Runs | km | h | Longest | Load |")
        print("|---|---|---|---|---|---|")
        for w in weeks[-(args.weeks + 1):]:
            tag = "" if w["complete"] else " (current)"
            print(f"| {w['monday']}{tag} | {w['runs']} | {w['km']} | {w['hours']} | {w['longest_km']} | {w['load']} |")
        print(f"\n4-week avg: {avg4} km, ACWR (7d/28d): {acwr}, monotony 7d: {monotony}, strain 7d: {strain}")
        print(f"CAPS next week: <= {cap_km} km, longest run <= {cap_long} km")
        for c in out["check"]:
            print(f"CHECK {c['what']}: planned {c['planned']} vs cap {c['cap']} -> {'OK' if c['ok'] else 'OVER CAP'}")
        print("\nWarnings:" if flags else "\nWarnings: none")
        for f in flags:
            print(f"- {f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
