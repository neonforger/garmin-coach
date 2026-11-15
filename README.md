# Garmin Coach

**A free, open-source AI running coach and sports nutritionist built on your own Garmin data.**
No app, no subscription, no server: just [Claude Code](https://claude.com/claude-code) + the
community [Garmin MCP](https://github.com/Taxuspt/garmin_mcp) + a few prompt files.

Ask things like:

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
- **`.claude/agents/`**: two subagents, `coach` (training analysis) and `nutri` (energy + meal plans).
- **`.claude/commands/`**: slash commands `/setup`, `/sync`, `/week`, `/analyze`, `/meal-plan`.
- **`scripts/garmin_export.py`**: downloads up to 2 years of history to `data/` so analyses are fast
  and don't hammer Garmin's API.
- **`examples/data/`**: a small anonymized dataset to try it without a Garmin account.

Your data never leaves your machine except to talk to Garmin and to Claude. `data/` and your
profile are git-ignored.

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
/setup        # checks the connection and creates profile/athlete.md
/sync         # optional but recommended: downloads your history to data/
/week         # your first weekly review
```

Tokens expired? Run the auth command again with `--force-reauth`.

## Commands

| Command | What it does |
|---|---|
| `/setup` | Checks the Garmin connection, pulls your profile and HR zones, asks only what's missing |
| `/sync [days]` | Downloads/updates your history into `data/` (resumable, rate-limit friendly) |
| `/week [period]` | Training + recovery review vs. your previous 4 weeks |
| `/analyze [activity]` | Deep dive into one workout: reps rebuilt from laps, zones, comparison with similar sessions |
| `/meal-plan [days]` | Calories and macros per day type + concrete meals, based on your real expenditure |

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
- **Not medical advice.** For medical conditions, medication or eating disorders, see a professional.

## Credits

- [Taxuspt/garmin_mcp](https://github.com/Taxuspt/garmin_mcp): the MCP server that does the heavy lifting
- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect)

MIT licensed.
