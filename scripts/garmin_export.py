"""Download your Garmin Connect history to ./data using the tokens in ~/.garminconnect.

Run `garmin-mcp-auth` once first (see README). Then, from the repo root:

    uv run --no-project --python 3.12 --with garminconnect python scripts/garmin_export.py            # last 730 days
    uv run --no-project --python 3.12 --with garminconnect python scripts/garmin_export.py --days 30  # incremental update

It is resumable: splits already downloaded are not requested again.
On Windows set PYTHONIOENCODING=utf-8 if the console mangles characters.

./data is git-ignored. Never commit it: it contains your name, IDs and GPS.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import date, timedelta
from pathlib import Path

from garminconnect import Garmin

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SPLITS_DIR = DATA / "splits"
PAUSE = 1.0  # seconds between calls to avoid HTTP 429
RUN_TYPES = {"running", "track_running", "treadmill_running", "trail_running", "indoor_running"}


def call(fn, *args, retries: int = 4):
    """Call the API with a pause and back-off on rate limits."""
    for attempt in range(retries):
        try:
            result = fn(*args)
            time.sleep(PAUSE)
            return result
        except Exception as exc:  # the library raises several types
            msg = str(exc)
            if "429" in msg or "Too Many" in msg:
                wait = 60 * (attempt + 1)
                print(f"  rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  error in {fn.__name__}{args}: {msg[:200]}")
            return None
    print(f"  giving up on {fn.__name__}{args} after {retries} attempts")
    return None


def save(name: str, obj) -> None:
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def load(name: str, default):
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def chunks(start: date, end: date, days: int):
    cur = start
    while cur <= end:
        stop = min(cur + timedelta(days=days - 1), end)
        yield cur.isoformat(), stop.isoformat()
        cur = stop + timedelta(days=1)


def merge_by_key(existing: list, new: list, key: str) -> list:
    out = {str(x.get(key)): x for x in existing if isinstance(x, dict)}
    out.update({str(x.get(key)): x for x in new if isinstance(x, dict)})
    return sorted(out.values(), key=lambda x: str(x.get(key)))


def export_activities(g: Garmin, start: date, end: date) -> list:
    print("Activities...")
    acts = call(g.get_activities_by_date, start.isoformat(), end.isoformat()) or []
    allacts = merge_by_key(load("activities.json", []), acts, "activityId")
    save("activities.json", allacts)

    cols = ["activityId", "startTimeLocal", "activityName", "type", "eventType", "distance",
            "duration", "movingDuration", "averageSpeed", "maxSpeed", "averageHR", "maxHR",
            "aerobicTrainingEffect", "anaerobicTrainingEffect", "activityTrainingLoad",
            "averageRunningCadenceInStepsPerMinute", "elevationGain", "vO2MaxValue", "calories"]
    with open(DATA / "activities.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for a in allacts:
            row = dict(a)
            row["type"] = (a.get("activityType") or {}).get("typeKey")
            row["eventType"] = (a.get("eventType") or {}).get("typeKey")
            w.writerow([row.get(c) for c in cols])
    print(f"  {len(acts)} new/updated, {len(allacts)} total")
    return acts


def export_splits(g: Garmin, acts: list) -> None:
    SPLITS_DIR.mkdir(exist_ok=True)
    runs = [a for a in acts if (a.get("activityType") or {}).get("typeKey") in RUN_TYPES]
    todo = [a for a in runs if not (SPLITS_DIR / f"{a['activityId']}.json").exists()]
    print(f"Laps + HR zones: {len(todo)} runs to download")
    for i, a in enumerate(todo, 1):
        aid = a["activityId"]
        splits = call(g.get_activity_splits, aid)
        if splits is None:
            continue
        zones = call(g.get_activity_hr_in_timezones, aid)
        (SPLITS_DIR / f"{aid}.json").write_text(
            json.dumps({"splits": splits, "hr_zones": zones}, ensure_ascii=False), encoding="utf-8")
        if i % 25 == 0:
            print(f"  {i}/{len(todo)}")


def export_health(g: Garmin, start: date, end: date) -> None:
    print("Sleep...")
    sleep = call(g.get_sleep_daily, start.isoformat(), end.isoformat()) or []
    save("sleep.json", merge_by_key(load("sleep.json", []), sleep, "calendarDate"))

    print("Resting HR...")
    rhr = []
    for s, e in chunks(start, end, 180):
        rhr += call(g.get_rhr_daily, s, e) or []
    save("rhr.json", rhr if rhr else load("rhr.json", []))

    print("HRV...")
    hrv = []
    for s, e in chunks(start, end, 30):
        r = call(g.get_hrv_data_range, s, e) or {}
        hrv += r.get("hrvSummaries", []) if isinstance(r, dict) else []
    save("hrv.json", merge_by_key(load("hrv.json", []), hrv, "calendarDate"))

    print("VO2max...")
    vo2 = []
    for s, e in chunks(start, end, 30):
        r = call(g.get_max_metrics_range, s, e)
        vo2 += r if isinstance(r, list) else ([r] if r else [])
    save("vo2max.json", vo2 if vo2 else load("vo2max.json", []))

    print("Training status (weekly sample)...")
    status = load("training_status.json", {})
    d = start
    while d <= end:
        if d.isoformat() not in status:
            r = call(g.get_training_status, d.isoformat())
            if r is not None:
                status[d.isoformat()] = r
        d += timedelta(days=7)
    save("training_status.json", status)

    print("Personal records...")
    pr = call(g.get_personal_record)
    if pr is not None:
        save("personal_records.json", pr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--skip-splits", action="store_true")
    ap.add_argument("--skip-health", action="store_true")
    args = ap.parse_args()

    DATA.mkdir(exist_ok=True)
    end = date.today()
    start = end - timedelta(days=args.days)

    g = Garmin()
    g.login(str(Path.home() / ".garminconnect"))
    print(f"Connected. Range: {start} -> {end}")

    acts = export_activities(g, start, end)
    if not args.skip_splits:
        export_splits(g, acts)
    if not args.skip_health:
        export_health(g, start, end)
    save("_export_meta.json", {"last_run": end.isoformat(), "days": args.days})
    print("Done.")


if __name__ == "__main__":
    main()
