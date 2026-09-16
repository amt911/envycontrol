# FINDINGS — <PROJECT>

> **Template.** Copy to `docs/FINDINGS.md` in the new repo and delete this quote block.
>
> This is the repo's **non-obvious gotchas log**. `CLAUDE.template.md` § *Start here* makes it
> mandatory reading before debugging or touching the build, and mandatory writing whenever you
> discover something that cost you time and **is not deducible from the code**.

## What goes here

An entry earns its place only if **all** of these hold:

- It cost real time to discover (a wrong path taken, a silent failure, a misleading error).
- It is **not** deducible by reading the code or the tests — a reader of the source would not
  infer it.
- It will bite again: it's a property of the stack, the environment or the tooling, not a
  one-off typo you already fixed.

Not here: how the architecture works (that's `CLAUDE.md`), what a feature does (that's
`user-stories.md`), or a bug you fixed in the same change (that's the commit + its regression test).

## Format

One `###` entry per finding, newest first. Keep each to a few lines — a long entry means it
belongs in `CLAUDE.md` instead.

```markdown
### <Short symptom, as you'd search for it>

**Symptom.** <What you actually saw — the error string, the wrong output, the hang.>
**Cause.** <The real mechanism, once known.>
**Fix / workaround.** <The command, flag or code change that resolves it.>
**Why it isn't obvious.** <Why the code doesn't tell you this.>

Found: <YYYY-MM-DD> · <area: build | tests | db | ci | deploy | env>
```

---

## Findings

### <First finding title>

**Symptom.** <…>
**Cause.** <…>
**Fix / workaround.** <…>
**Why it isn't obvious.** <…>

Found: <YYYY-MM-DD> · <area>
