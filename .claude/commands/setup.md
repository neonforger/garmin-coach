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
   - what they want from you, offering both:
     - **training**: "Do you already have a coach or a plan (I'll analyze it), or do you want me to
       be your coach and plan your weeks?" → `Coaching mode: analyst | coach`
     - **nutrition**: "I can also adjust your meals to each day's training. Want that too?"
       → `Nutrition help: yes | no`
   - if `coach`: days available per week, time per session, track/gym access
   - injuries or limitations
   - if nutrition: goal, preferences/diet, allergies, meals per day
4. **Write `profile/athlete.md`** using `profile/athlete.example.md` as the template.
   This file is git-ignored.
5. **Offer the historical export**: `/sync` (recommended for analyses over more than a few weeks).
6. **If `coach` mode, don't stop at the profile: start coaching now.** Run the export (`/sync`;
   the last 8 weeks via the MCP are enough to start if the full export is still running), then
   the `/coach` loop: block to the goal, first week, workouts on the watch (ask once), meals.
7. Otherwise finish with a 3–5 line summary of what you see in the last 4 weeks and the next step
   that fits: `analyst` → `/week`; nutrition only → `/meal-plan`.
   List the other commands in one line: `/coach`, `/today`, `/week`, `/analyze`, `/plan`,
   `/meal-plan`, `/sync`.

$ARGUMENTS
