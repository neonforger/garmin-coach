---
description: Meal plan for today or the coming days, adjusted to your training and goal
---

Use the `nutri` agent to build a meal plan for: $ARGUMENTS (default: today).

- energy and macro targets per day, based on Garmin expenditure + the goal in `profile/athlete.md`
- day types from the current `plans/*-training.md` if there is one; otherwise, if the planned
  sessions for those days aren't known, ask first
- meals with foods and grams, kcal/macros per meal and per day, workout fueling
- if asked for a file, save it to `plans/<date>.md`
