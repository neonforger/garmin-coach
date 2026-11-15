---
description: Deep dive into one workout (default - the latest one)
---

Use the `coach` agent to analyze one activity: $ARGUMENTS
(an activity ID, a date, or a description like "Tuesday's intervals"; if empty, the latest activity).

- reconstruct the structure (warm-up, reps, recoveries, cool-down) from the laps
- per-rep pace, HR, cadence; fade or drift across reps
- time in HR zones and whether it matches the intent of the session
- compare with the 3 most similar past sessions
- conclusion in 3 bullets
