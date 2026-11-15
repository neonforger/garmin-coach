---
description: Download / update your Garmin history into data/ (git-ignored)
---

Update the local Garmin export.

1. If `data/_export_meta.json` exists, compute days since `last_run` and use `--days <that + 3>`.
   Otherwise this is the first export: use `--days 730` (or the number in $ARGUMENTS) and warn the
   athlete it can take a while (it pauses between calls to avoid rate limits; it is resumable).
2. Run from the repo root:
   `uv run --no-project --python 3.12 --with garminconnect python scripts/garmin_export.py --days N`
   (on Windows, set `PYTHONIOENCODING=utf-8`). Run it in the background for long exports.
3. If it fails with an auth error, tell the athlete to run `garmin-mcp-auth` (see README).
4. When done, report: number of activities, date range, and anything that came back empty
   (e.g. HRV not supported by the watch).
