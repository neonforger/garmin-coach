# Garmin Coach

**A free, open-source AI running coach and sports nutritionist built on your own Garmin data.**
No app, no subscription, no server: just [Claude Code](https://claude.com/claude-code) + the
community [Garmin MCP](https://github.com/Taxuspt/garmin_mcp) + a few prompt files.

It works the way you need it to:

- **No coach?** It becomes your coach, end to end: it reads your current Garmin data, builds a block
  up to your race, writes each week from what you actually ran, **puts the workouts on your watch**
  (Garmin calendar, with HR targets), checks your recovery every morning if you want, and adjusts
  the next week from what you did.
- **Already have a coach or a plan?** It just analyzes your training and never contradicts your coach.
- **Either way**, it can fit your meals to each day's training (more carbs on hard days, less on
  rest days), because training and food work best planned together.

`/setup` asks which of these you want. Then ask things like:

- *"Plan my next week, I can run 4 days and want to do a sub-50 10K in March."*
- *"How did my training go this week compared with last month?"*
- *"Analyze Tuesday's intervals, am I fading on the last reps?"*
- *"My easy runs feel hard lately. Is it sleep, volume or am I running them too fast?"*
- *"Give me a meal plan for tomorrow, I have a long run in the morning."*

## How it works

```
Garmin Connect ──► Garmin MCP (live data) ──┐
        │                                   ├──► Claude Code + CLAUDE.md + agents ──► analysis / meal plans
        └──► scripts/garmin_export.py ─► data/ (local history) ┘
```

- **`CLAUDE.md`**: the coach's "brain": data sources, how to analyze, Garmin pitfalls, nutrition rules.
- **`.claude/agents/`**: two subagents, `coach` (training analysis and plans) and `nutri` (energy +
  meal plans). The training plan tags each day as rest / easy / hard, and the meal plan uses it.
- **`.claude/commands/`**: slash commands `/setup`, `/coach`, `/today`, `/sync`, `/week`, `/analyze`,
  `/plan`, `/meal-plan`.
- **`scripts/load.py`**: the load maths in code, not in the AI's head: weekly volume, acute:chronic
  ratio, monotony, and hard caps for next week. Every plan is checked against them before you see it.
- **`scripts/garmin_export.py`**: downloads up to 2 years of history to `data/` so analyses are fast
  and don't hammer Garmin's API.
- **`examples/data/`**: a small anonymized dataset to try it without a Garmin account.

Your data never leaves your machine except to talk to Garmin and to Claude. `data/`, `plans/` and
your profile are git-ignored.

## Setup (~10 minutes)

**Requirements:** [Claude Code](https://docs.claude.com/en/docs/claude-code/overview), [uv](https://docs.astral.sh/uv/getting-started/installation/), a Garmin Connect account.

```bash
git clone https://github.com/neonforger/garmin-coach.git
cd garmin-coach

# 1. Log in to Garmin once (supports MFA). Tokens are stored in ~/.garminconnect (~6 months).
uvx --python 3.12 --from git+https://github.com/Taxuspt/garmin_mcp garmin-mcp-auth

# 2. Open Claude Code in the repo. It will ask to enable the "garmin" MCP server from .mcp.json -> yes.
claude
```

Then inside Claude Code:

```
/setup        # checks the connection, asks coach / analyst / nutrition, creates profile/athlete.md
              # coach mode: then syncs your data and builds your block, first week, watch workouts and meals
/coach        # coach mode, once a week: review + next week + workouts on the watch + meals
/today        # coach mode, optional, each morning: keep / soften / swap today's session
/week         # analyst mode: your weekly review
```

Tokens expired? Run the auth command again with `--force-reauth`.

## Commands

| Command | What it does |
|---|---|
| `/setup` | Checks the Garmin connection, pulls your profile and HR zones, asks what you want (coach, analyst, nutrition) and only what's missing |
| `/coach` | Coach mode, weekly: syncs fresh data, reviews last week vs. plan, writes next week, schedules it on your watch, meals for the week |
| `/today [how you feel]` | Coach mode, daily: checks sleep / resting HR / body battery / readiness and keeps, softens or swaps today's session (and updates the watch) |
| `/sync [days]` | Downloads/updates your history into `data/` (resumable, rate-limit friendly) |
| `/plan [period]` | Coach mode: next week's training from your real volume, zones and goal, with pace + HR targets. Saved to `plans/` |
| `/week [period]` | Training + recovery review vs. your previous 4 weeks (coach mode: also planned vs. done) |
| `/analyze [activity]` | Deep dive into one workout: reps rebuilt from laps, zones, comparison with similar sessions |
| `/meal-plan [days]` | Calories and macros per day type + concrete meals, based on your real expenditure and your planned sessions |

You don't need the commands: you can just talk to it.

## Try it without Garmin

`examples/data/` contains ~40 activities with laps, HR zones, sleep and resting HR from a real
athlete, **anonymized** (no name, IDs, GPS or locations; dates shifted; workout names replaced).
Without `data/` and without Garmin login, the coach falls back to it and tells you so.

## Sharing your own data safely

If you want to share a sample of your data (bug reports, examples), anonymize it first:

```bash
uv run --no-project --python 3.12 python scripts/anonymize.py \
  --src data --dst examples/data --last 40 --forbid "Your Name,Your Town"
```

It uses an allow-list of fields, renumbers activity IDs, shifts dates by a random offset and runs a
leak check at the end. Still look at the output before publishing.

## Notes and limits

- The Garmin MCP uses Garmin Connect's **unofficial** API. If Garmin changes something it may break
  until the MCP is updated. Use at your own risk and respect Garmin's terms.
- Claude Code needs a Claude subscription or API credits. Check current plans on
  [claude.com](https://claude.com/pricing).
- Garmin estimates (calories, VO2max, race predictions, training status) are estimates. The coach
  is told to say which numbers are measured and which are estimated.
- In coach mode the plans are conservative by design (≤ ~10 % volume increase per week, mostly easy
  running, a lighter week every 3–4 weeks). The caps are enforced by `scripts/load.py`, and every plan
  ends with a "⚠ Warnings" section (load spikes, stale data, assumptions). If something hurts, it will tell you to stop and see a
  physio, not to push through.
- Workouts it sends to Garmin are named `GC <date> ...`. It asks before writing to your Garmin account
  the first time, and it never touches workouts you or other apps created.
- **Not medical advice.** For medical conditions, medication or eating disorders, see a professional.

## Credits

- [Taxuspt/garmin_mcp](https://github.com/Taxuspt/garmin_mcp): the MCP server that does the heavy lifting
- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect)

MIT licensed.
