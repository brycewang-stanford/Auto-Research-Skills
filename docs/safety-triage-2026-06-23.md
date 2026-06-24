# Safety Triage — 2026-06-23

Classifies the `catalog/SAFETY.md` must-review backlog into verdict buckets so a
maintainer can see, at a glance, which of the high+ findings are *benign by
construction* (tool installers, example code), which are *scanner false
positives*, and which are *genuinely worth a human read*. It also records the
two precision fixes shipped today.

Scope: the **`skill`/`script`** context (executable surfaces); install-doc and
example-only hits are excluded by the scanner's context buckets.

## Precision fixes shipped today

| Rule | Before | After | What was removed |
|---|---:|---:|---|
| `credential-print` | 197 | 122 | bare-word `token` (LLM token counts, tokenizer output, "revoke the leaked token" warnings) — commit `2d66db0` |
| `remote-shell-pipe` | 51 | 36 | `curl <api> \| python3 -c/-m/script.py` research-API **data** parses (crossref, arxiv, pubchem, imf, …) — commit `92f382e` |

Net effect on the executable-context must-review surface: **278 → 188
(−90, −32%)**; criticals there **62 → 47**. No real findings were suppressed —
both fixes are backed by regression tests asserting that genuine secrets and
genuine `curl|sh` installers still flag.

## Current must-review breakdown (skill/script, high+)

| Rule | Sev | Count | Verdict | Action |
|---|---|---:|---|---|
| `credential-print` | high | 120 | **mostly benign** — example code that prints a key var, plus ~7 "get your key at `…/apikey`" help-URL false positives and placeholder creds (`echo 'YOUR_PASSWORD' \| login`) | spot-check; two residual FP classes noted below |
| `remote-shell-pipe` | crit | 36 | **benign tool bootstraps** — official installers: `parallel.ai` (8), `openclaw.ai` (8), `feynman.is` (5), `astral.sh`/uv (4), Lean `elan` (1) | trust-the-vendor by design; correctly CRITICAL (RCE-on-trust), not a defect |
| `echo-secret-value` | high | 13 | **highest-signal bucket** — real value prints | review (see shortlist) |
| `powershell-iex` | crit | 8 | **benign tool bootstraps** — Windows `irm … \| iex` installers, same class as remote-shell-pipe | trust-the-vendor by design |
| `concealment-instruction` | high | 6 | **0 malicious** — see analysis below | mostly false positives |

## Genuinely worth reviewing: `echo-secret-value` (13)

These print a secret env var's **value** into terminal / agent-visible output —
the one bucket with real (if usually low-blast-radius) signal:

- `skills/scienceclaw/deploy/docker-setup.sh` (×3) and
  `scripts/shell-helpers/clawdock-helpers.sh` (×3) — gateway/token setup echoing
  `$OPENCLAW_GATEWAY_TOKEN`.
- `skills/scienceclaw/.../gh-issues/SKILL.md` (×5) — `echo $GH_TOKEN` / `echo
  "Token: ${GH_TOKEN}"` in a GitHub-issues helper.
- `skills/scientific-agent-skills/.../database-lookup/SKILL.md` and
  `skills/light-skills/.../debug_instrument.sh` — one each.

Most print the *user's own* token in the *user's own* terminal during a setup
step (low blast radius), but the pattern is worth keeping flagged: a token
echoed into agent-visible output can leak into transcripts/logs. None are
exfiltration to a third party.

## `concealment-instruction` (6) — analysis

- **False positive (3):** `trl-fine-tuning/SKILL.md:450` matches "Secretly" in a
  **paper title** ("DPO: Your Language Model is *Secretly* a Reward Model");
  two `proof-checker` hits are similar prose.
- **Benign UX (1):** `scienceclaw/src/agents/system-prompt.ts:55` — "do not
  mention file paths or line numbers in replies unless the user asks" (reply
  hygiene, not concealment).
- **Benign privacy (2):** `nature-skills/.../nature-figure/SKILL.md:16` — "if the
  user provides a private plotting template collection … do not reveal its path
  … in user-facing output." This hides the **user's own** private file paths
  from a published figure, not behavior from the user. Borderline but
  defensible; flagged correctly so a human can confirm.

Verdict: **no malicious concealment** in the catalog today.

## Residual false-positive classes (future precision candidates)

Lower priority than today's two fixes, but recorded so the noise is understood:

1. **`credential-print` on help-URLs** (~7): `echo "Get your key at
   https://aistudio.google.com/app/apikey"` matches `API[_-]?KEY` because
   `apikey` is in the URL path. Telling a user where to get a key is not
   printing one.
2. **`credential-print` on placeholder creds**: `echo 'YOUR_PASSWORD' | qzcli
   login` — a literal placeholder, not a real secret.
3. **`concealment-instruction` on paper titles / prose**: "Secretly a Reward
   Model" etc.

A future pass could add a negative lookahead for `…/apikey` URL paths and an
all-caps-placeholder guard, but each carries a small recall risk and should ship
with its own regression tests (the bar set by the two fixes above).

## Bottom line

After today's fixes the **188** executable-context findings are dominated by
**~44 benign vendor installers** (`remote-shell-pipe` + `powershell-iex`) and
**~120 example-code / help-text `credential-print` hits** with low real risk.
The actual human-review surface is the **13 `echo-secret-value`** findings (real
value prints, mostly the user's own tokens) plus a glance at the 2 borderline
`concealment` items — well under twenty items, down from a 278-line wall.
