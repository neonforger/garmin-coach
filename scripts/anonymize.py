"""Build a small, anonymized sample dataset from a real Garmin export.

It uses an ALLOW-LIST: only the fields listed below are copied, everything else
(name, owner/device IDs, GPS, location names, profile images, absolute
elevation, UUIDs, epoch timestamps...) is dropped. On top of that:

  * activity IDs are renumbered (real IDs link to your Garmin Connect profile)
  * activity names are replaced by generic labels ("Easy run", "Intervals"...)
  * every date is shifted by a random number of days (the offset is not saved)

Usage:
    uv run --no-project --python 3.12 python scripts/anonymize.py \
        --src data --dst examples/data --last 40 --forbid "YourName,YourTown"

The script finishes with a leak check: if any forbidden key or string survives,
it deletes nothing but exits with an error so you don't publish it.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

ACTIVITY_FIELDS = [
    "distance", "duration", "movingDuration", "averageSpeed", "maxSpeed",
    "averageHR", "maxHR", "aerobicTrainingEffect", "anaerobicTrainingEffect",
    "activityTrainingLoad", "averageRunningCadenceInStepsPerMinute",
    "avgStrideLength", "elevationGain", "elevationLoss", "vO2MaxValue",
    "calories", "lapCount",
]
LAP_FIELDS = [
    "lapIndex", "distance", "duration", "movingDuration", "averageSpeed",
    "maxSpeed", "averageHR", "maxHR", "averageRunCadence", "strideLength",
    "elevationGain", "elevationLoss", "calories", "intensityType",
]
ZONE_FIELDS = ["zoneNumber", "secsInZone", "zoneLowBoundary"]
SLEEP_FIELDS = [
    "totalSleepTimeInSeconds", "deepTime", "lightTime", "remTime", "awakeTime",
    "restingHeartRate", "respiration", "bodyBatteryChange", "sleepScore",
]
# Generic words that are safe to keep because they describe the workout, not the person.
WORKOUT_KEYWORDS = {
    "test": "Test", "interval": "Intervals", "series": "Intervals", "reps": "Intervals",
    "fartle": "Fartlek", "tempo": "Tempo", "threshold": "Threshold", "umbral": "Threshold",
    "hill": "Hills", "cuesta": "Hills", "progres": "Progression", "long": "Long run",
    "tirada": "Long run", "recov": "Recovery", "regener": "Recovery",
}
TYPE_LABELS = {
    "running": "Run", "track_running": "Track session", "treadmill_running": "Treadmill run",
    "trail_running": "Trail run", "indoor_running": "Indoor run", "walking": "Walk",
    "lap_swimming": "Swim", "strength_training": "Strength", "indoor_cycling": "Indoor bike",
    "cycling": "Bike", "indoor_cardio": "Cardio",
}
FORBIDDEN_KEYS = {
    "ownerFullName", "ownerDisplayName", "ownerId", "deviceId", "userProfileId",
    "locationName", "startLatitude", "startLongitude", "endLatitude", "endLongitude",
    "activityUUID", "ownerProfileImageUrlSmall", "ownerProfileImageUrlMedium",
    "ownerProfileImageUrlLarge", "maxElevation", "minElevation", "timeZoneId",
}


def pick(d: dict, fields: list[str]) -> dict:
    return {k: d.get(k) for k in fields if d.get(k) is not None}


def generic_name(raw: str, type_key: str) -> str:
    low = (raw or "").lower()
    for kw, label in WORKOUT_KEYWORDS.items():
        if kw in low:
            return label
    return TYPE_LABELS.get(type_key, "Workout")


def load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="data")
    ap.add_argument("--dst", default="examples/data")
    ap.add_argument("--last", type=int, default=40, help="number of most recent activities to keep")
    ap.add_argument("--forbid", default="", help="comma-separated strings that must not appear in the output")
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    (dst / "splits").mkdir(parents=True, exist_ok=True)
    shift = timedelta(days=random.SystemRandom().randint(200, 900))

    acts = sorted(load(src / "activities.json", []), key=lambda a: a.get("startTimeLocal") or "")
    acts = acts[-args.last:]
    if not acts:
        sys.exit("No activities found in source folder.")

    def shift_dt(s: str) -> str:
        return (datetime.fromisoformat(s[:19]) - shift).strftime("%Y-%m-%d %H:%M:%S")

    def shift_d(s: str) -> str:
        return (datetime.fromisoformat(s[:10]) - shift).strftime("%Y-%m-%d")

    out_acts = []
    for new_id, a in enumerate(acts, 1):
        type_key = (a.get("activityType") or {}).get("typeKey") or "other"
        row = {
            "activityId": new_id,
            "startTimeLocal": shift_dt(a["startTimeLocal"]),
            "activityName": generic_name(a.get("activityName"), type_key),
            "type": type_key,
            **pick(a, ACTIVITY_FIELDS),
        }
        out_acts.append(row)

        sp = load(src / "splits" / f"{a['activityId']}.json", None)
        if sp:
            laps = [pick(l, LAP_FIELDS) for l in (sp.get("splits") or {}).get("lapDTOs", [])]
            zones = [pick(z, ZONE_FIELDS) for z in (sp.get("hr_zones") or [])]
            dump(dst / "splits" / f"{new_id}.json", {"activityId": new_id, "laps": laps, "hr_zones": zones})

    dump(dst / "activities.json", out_acts)
    cols = ["activityId", "startTimeLocal", "activityName", "type"] + ACTIVITY_FIELDS
    with open(dst / "activities.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out_acts)

    first = acts[0]["startTimeLocal"][:10]
    last = acts[-1]["startTimeLocal"][:10]
    in_range = lambda d: first <= (d or "")[:10] <= last

    sleep = [
        {"calendarDate": shift_d(s["calendarDate"]), **pick(s.get("values") or {}, SLEEP_FIELDS)}
        for s in load(src / "sleep.json", []) if in_range(s.get("calendarDate"))
    ]
    dump(dst / "sleep.json", sleep)
    rhr = [
        {"calendarDate": shift_d(r["calendarDate"]), "value": r.get("value")}
        for r in load(src / "rhr.json", []) if in_range(r.get("calendarDate"))
    ]
    dump(dst / "rhr.json", rhr)

    # ---- leak check ---------------------------------------------------------
    forbidden = [s.strip().lower() for s in args.forbid.split(",") if s.strip()]
    for a in load(src / "activities.json", []):  # real IDs must not survive
        forbidden.append(str(a.get("activityId")))
    # ignore trivially short strings / small numbers (e.g. a deviceId of 0) to avoid false positives
    forbidden = sorted({s for s in forbidden if len(s) >= 4 and not (s.isdigit() and len(s) < 6)})
    problems = []
    for p in dst.rglob("*"):
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        low = text.lower()
        for key in FORBIDDEN_KEYS:
            if f'"{key}"' in text:
                problems.append(f"{p}: key {key}")
        for s in forbidden:
            if re.search(rf"(?<![\w]){re.escape(s)}(?![\w])", low):
                problems.append(f"{p}: forbidden string '{s}'")
    if problems:
        print("LEAK CHECK FAILED:\n  " + "\n  ".join(problems[:50]))
        sys.exit(1)
    print(f"OK: {len(out_acts)} activities, {len(sleep)} sleep days, {len(rhr)} RHR days -> {dst}")
    print("Leak check passed. Still review the output by eye before publishing.")


if __name__ == "__main__":
    main()
