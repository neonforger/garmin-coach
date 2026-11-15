---
description: First-time setup - check the Garmin connection and create your athlete profile
---

Set up Garmin Coach for this athlete:

1. **Check the Garmin MCP.** Call a cheap tool (e.g. `get_full_name` or `get_user_profile`).
   - If it fails with an auth error, tell the athlete to run in a terminal:
     `uvx --python 3.12 --from git+https://github.com/Taxuspt/garmin_mcp garmin-mcp-auth`
     and then restart Claude Code. Stop here until it works.
2. **Pull what Garmin already knows**: profile (weight, height, age, sex), HR zones
   (`get_heart_rate_zones`), last 4 weeks of activities, latest VO2max / race predictions.
3. **Ask only what is missing**, in one short list:
   - main sport/event and goal (e.g. "sub-20 5K in March", "lose 3 kg by summer")
   - follows a coach/plan? (yes → you'll analyze, not prescribe)
   - injuries or limitations
   - nutrition: goal, preferences/diet, allergies, meals per day
4. **Write `profile/athlete.md`** using `profile/athlete.example.md` as the template.
   This file is git-ignored.
5. **Offer the historical export**: `/sync` (recommended for analyses over more than a few weeks).
6. Finish with a 3–5 line summary of what you see in the last 4 weeks and the commands available:
   `/week`, `/analyze`, `/meal-plan`, `/sync`.

$ARGUMENTS
