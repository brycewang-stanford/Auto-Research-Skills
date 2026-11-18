# Codex adapter

Installs the crew into [Codex](https://github.com/openai/codex) as skills: `crew-pi` to
start or resume a project as the PI, and `crew-<role>` for each role. The skills point
at this checkout's `crew/` directory, so keep the clone where it is.

```bash
python3 crew/adapters/codex/install.py            # into ~/.codex/skills
python3 crew/adapters/codex/install.py --dry-run  # show what would be written
```

Then, in Codex: *"use crew-pi to start seed ss-dml-401k"*.

When the crew runs in Codex, the authors are OpenAI models, so the Reviewer runs on
Claude: `python3 crew/scripts/cross_review.py <workspace> <target> <round> --via claude`.
