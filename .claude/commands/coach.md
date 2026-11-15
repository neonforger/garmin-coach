---
description: Your weekly coaching session, end to end - fresh data, review, next week's plan, workouts on your watch and meals
---

Run the full weekly loop from "Coach mode is end-to-end" in `CLAUDE.md`. $ARGUMENTS

1. Read `profile/athlete.md`. If `Coaching mode` is not `coach`, say in one line that this command
   is for when Garmin Coach is their coach, and offer `/week` (analyst) or `/meal-plan` instead.
   If goal, event date or availability are missing, ask for them in one short list first.
2. **Fresh data**: sync up to yesterday (see `/sync`) without asking. Say which date the data reaches.
   Recovery needs a trend, not a single day: if `data/` has no `sleep.json` / `rhr.json` covering the
   last 4 weeks, pull those 28 days of sleep and resting HR from the Garmin MCP before reviewing.
3. **Block**: create or update `plans/block.md` if it's missing or the goal changed.
   Say which phase and week of the block we're in.
4. **Review** with the `coach` agent: last week planned vs. done, key sessions, recovery, and what
   changes next week and why. Short.
5. **Next week** with the `coach` agent: run `scripts/load.py` for the caps, draft the plan, gate it
   with `--check-km/--check-long` (must exit 0), and save it to `plans/<monday-date>-training.md`
   with its `⚠ Warnings` section. Then **run the check yourself** (don't trust the agent's report):
   `scripts/load.py --check-km <total> --check-long <longest>` must exit 0. Show the caps and the
   check result in one line.
6. **Watch**: if `Send workouts to watch` is `yes`, create and schedule the sessions (see
   "Sending workouts to the watch"); if it's not set, ask once and save the answer. Report what was
   scheduled on which day.
7. **Meals**: unless `Nutrition help: no`, use the `nutri` agent for the week's targets per day type and
   a concrete menu for each day type, plus the shopping list. Save to `plans/<monday-date>-meals.md`.
8. End with 3 lines: the goal of this week, the one session that matters most, and when to run
   `/coach` again (next Sunday or Monday).
