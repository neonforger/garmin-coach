---
description: Your training plan for next week (or the period you say), built from your Garmin data, with matching meals
---

Build a training plan for: $ARGUMENTS (default: next Monday to Sunday).

1. Read `profile/athlete.md`.
   - If `Coaching mode` is `analyst` (they have a coach or plan): remind them in one line that their
     coach's plan comes first, and only continue if they confirm they want a plan from you.
   - If availability (days, time per session, track/gym access) or the goal is missing, ask for it
     in one short list before planning.
2. Fresh data first: sync up to yesterday (see `/sync`) without asking, and create `plans/block.md`
   if it doesn't exist (see "Coach mode is end-to-end").
3. Use the `coach` agent to build the week following "Prescribing" in `CLAUDE.md`:
   - baseline from the last 4–8 weeks, and planned vs. done for last week if there is a plan in `plans/`
   - one row per day: session, duration/distance, structure, pace range + HR range, purpose,
     day type (`rest` / `easy` / `hard/long`)
   - weekly totals vs. previous weeks and where the week sits in the block
   - caps from `scripts/load.py`, draft gated with `--check-km/--check-long` (must pass)
   - a `⚠ Warnings` section at the end
   - save to `plans/<monday-date>-training.md`
4. Send the sessions to the watch if `Send workouts to watch: yes` (ask once if it isn't set);
   see "Sending workouts to the watch" in `CLAUDE.md`.
5. Unless the profile says `Nutrition help: no`, end with one line offering the meal plan for the
   same days (`/meal-plan`), which will use these day types.
   (`/coach` does steps 2–5 plus the review of last week in one go.)
