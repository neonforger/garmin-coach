---
description: Daily check - is today's planned session still right for how you've recovered?
---

Daily check for coach mode. $ARGUMENTS (optional: how they feel, e.g. "legs heavy", "slept badly").

1. Read today's session from the current `plans/*-training.md`. If there's no plan, say so and
   offer `/coach`.
2. Pull today's recovery from the Garmin MCP: last night's sleep, resting HR, body battery,
   training readiness and HRV if available. Compare with their own 2–4 week baseline, not with
   generic norms. Run `scripts/load.py` for ACWR and monotony (a spike or high monotony is a
   reason to soften).
3. Decide, with a one-line reason:
   - **Keep** it as planned.
   - **Soften** it (shorter, fewer reps, easy instead of hard).
   - **Swap** it with another day of the week (respecting no two hard days in a row).
   - **Rest** (pain, illness, very poor recovery).
   Pain or illness overrides everything: no hard session, and suggest a professional if it persists.
4. If anything changed and workouts go to the watch, update the Garmin calendar (unschedule/delete
   the old `GC` workout, create and schedule the new one) and update the plan file.
5. If nutrition is on and the day type changed (e.g. hard → easy), give the adjusted targets for
   today in one line.
