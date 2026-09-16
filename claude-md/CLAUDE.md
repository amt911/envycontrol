# claude-md — Claude Guide

## What this repo is

This is the **meta / template repo**. It curates the `CLAUDE.md` (and companion) templates
that get synced into Andrés's other projects. It has **no runtime, no build system, no
dependencies** — it's a docs/markdown repo. When you work here you are editing the guides
that other repos will inherit, so precision and internal consistency matter more than usual.

Key files (all templates now live under `docs/starter-kit/`):

- `docs/starter-kit/CLAUDE.template.md` — **the single canonical `CLAUDE.md` template** (English).
  Projects copy it and fill in the `<…>` placeholders. It's layered: universal **governance**
  sections (kept verbatim across projects) plus an opinionated **pnpm-monorepo preset** (stack,
  module strategy, deploy) marked "replace for your stack". Serves both births (new project) and
  adaptations (existing repo — swap or delete the preset). This is the source of truth other repos
  are adapted from. *(Replaces the former root `CLAUDE-generic-template.md`, merged in here.)*
- `docs/starter-kit/` also holds the two other "genesis" fill-in templates a new project is born from:
  - `DESIGN-SYSTEM.template.md` → becomes `design-system.md` (palette, type, components).
  - `USER-STORIES.template.md` → becomes `user-stories.md` (roles, epics, MVP backlog).
  - `README.md` — explains the bootstrap flow from zero to first slice.
- `docs/PROMPT_TEMPLATES_WEB.md` — pasteable per-task prompt library (bootstrap, slice,
  page, endpoint, email, deploy, bug, PR verification). Its §0/§1 point at
  `CLAUDE.template.md` rather than restating the stack/rules, so there's one source of truth.

Because these files are templates, **intentional `<angle-bracket> placeholders` are
expected inside the template files** (the `*.template.md` files). Do not "clean them up" there —
they are the fill-in slots. Only *this* `CLAUDE.md` (the guide for working in this repo) must be
free of stray placeholders.

## ⚡ superpowers — use whenever applicable

Always prefer **superpowers** skills over ad-hoc approaches. If there's even a small chance a skill applies to the task, invoke it via the `Skill` tool before acting (including before clarifying questions).

- **Process skills first** — `brainstorming` before creative/feature work, `systematic-debugging` before fixing bugs, `test-driven-development` before writing implementation.
- **Then implementation skills** — domain-specific skills guide execution.
- **Verify before claiming done** — `verification-before-completion` / `requesting-code-review` before merging.

User instructions always take precedence over skills; skills override default behavior.

### Mode switch

- **"lite mode"** — fully disables superpowers: no skill is invoked, not even the applicability check, until **"normal mode"** is said.
- **"normal mode"** (default) — standard superpowers behavior, plus: when delegating coding work, dispatch at most 1 agent at a time, and never use a model above Sonnet (no Opus).
- **"modo desatendido"** (unattended mode) — the user is away and delegates autonomy: work without waiting for confirmations and make reasonable decisions yourself instead of asking. In this mode you MAY **`git push` the feature branches you create** and **open PRs via `gh`** on your own, so the work is ready for review when the user returns. The hard limits still hold and are NOT lifted: **never merge anything** (no `git merge`, no fast-forward integration, no `gh pr merge`), **never push to `main`** or any protected/default branch directly, and **never** `git push --force` / `--force-with-lease`. Deliver everything as pushed branches + PRs for the user to merge. Reverts to defaults on **"normal mode"**.

Confirm the switch briefly when it happens.

## Stack

- **None (no runtime).** Plain Markdown documents — no package manager, no build, no server.
- **Format** — GitHub-Flavored Markdown. Prose is intentionally mixed English / Spanish
  (the starter-kit docs are Spanish); match the language of the file you're editing.

## Commands

There is nothing to build, run, or serve. The only "commands" are optional local checks:

```bash
# markdown lint — rules live in `.markdownlint.jsonc` (MD013/MD033/MD024/MD060 are off on
# purpose: long table rows and <angle-bracket> placeholders are conventions here, not defects)
npx --yes markdownlint-cli "**/*.md"   # currently clean — keep it that way

# quick sanity: find leftover placeholders in a file that should have none
grep -n "\[.*\]" CLAUDE.md
```

Neither is a hard gate — treat the linter as advisory guidance, not CI.

## Quality

"Quality" here is documentation quality, not test coverage:

- **Markdown lint** — respect the `MD04x` (links) and `MD03x` (headings/lists) warnings.
  Keep heading levels sequential, fenced code blocks language-tagged, and lists
  consistently styled. The tree lints **clean** today, so any new warning is yours — don't
  silence it by widening `.markdownlint.jsonc`; a rule goes off only when it contradicts a
  documented convention of this repo, with the reason written next to it.
- **Internal consistency of the templates** — when you change one template, check the
  others still agree with it. A rule stated in `docs/starter-kit/CLAUDE.template.md` (the
  canonical `CLAUDE.md` template) should not contradict the design/user-stories templates or
  the prompt library. Governance lives once in `CLAUDE.template.md`; README and the prompt
  library summarize and link to it rather than restating it — keep those pointers accurate.
- **Intentional template edits** — because these files propagate into other repos, every
  edit should be deliberate. Preserve the fill-in `<…>` placeholders inside template files;
  don't reword governance sections (superpowers, Git & GitHub, Working rules) casually,
  since those are meant to stay verbatim across projects.
- **Review before done** — re-read the diff and confirm the change reads cleanly and
  doesn't break a placeholder or a cross-reference between docs.
- **Mutation gate (60%) — no aplica a este repo, y por eso está escrito.** El gate que la
  plantilla exige (`docs/starter-kit/CLAUDE.template.md` § *Mutation gate — the 60% floor*) es
  para los repos que heredan de ella: aquí no hay código ejecutable ni suite de tests que mutar,
  solo markdown. Si algún día entra un script con tests, la regla aplica desde ese día. No lo
  re-discutas cada trimestre: está decidido y anotado.

## Working rules

- **Use superpowers skills whenever they apply** — invoke via `Skill` before acting; process skills before implementation skills.
- **Reuse before you write — aquí eso significa no repetir prosa** — la governance vive una sola vez
  en `docs/starter-kit/CLAUDE.template.md`; el README del starter-kit y `docs/PROMPT_TEMPLATES_WEB.md`
  la resumen y **enlazan**, nunca la reescriben. Antes de añadir una sección, busca si ya existe en
  otro doc (`grep -rn "<concepto>" docs/`) y amplía esa; una regla contada en dos sitios se
  contradice sola en cuanto una de las dos copias se edita. Lo mismo para los prompts: un prompt
  nuevo referencia la sección del template, no copia sus reglas.
- **Templates carry placeholders on purpose** — don't strip `<…>` slots out of the
  template files; they are the fill-in points. Only non-template docs (like this guide)
  should be placeholder-free.
- **Keep governance sections verbatim** — the superpowers block, the Git & GitHub section,
  and the Working rules are universal. When editing a template, keep these consistent with
  the canonical wording rather than paraphrasing.
- **Edit templates deliberately** — a change here ripples into every project that syncs
  from it. Prefer small, reviewable edits; explain non-obvious changes in the commit.
- **Don't add tooling/dependencies without asking** — this repo is intentionally
  build-free (no `package.json`, no runtime). CI is deliberately lean: a single
  `.github/workflows/ci.yml` runs markdown lint and a secrets scan (both advisory), with
  `.github/dependabot.yml` keeping only the pinned GitHub Actions fresh — don't grow it into
  a build pipeline without asking.

## Git & GitHub

- **Commits and branches OK** — create commits and new branches whenever it makes sense, without asking first.
- **Never push** *(default)* — no `git push` under any circumstance, and absolutely never `git push --force` / `--force-with-lease`. Leave pushing to the user. **Exception:** when **"modo desatendido"** is active, you may push the feature branches you create (never `main`/protected branches, never force) so PRs are ready for review.
- **Never merge — no permission** — you do NOT have permission to merge anything into any branch, nor to merge any pull request. No `git merge`, no fast-forward integration, no `gh pr merge`. This holds in every mode, **including "modo desatendido"**. Leave every merge (branches and PRs alike) to the user.
- **GitHub via `gh`** — if the `gh` CLI is available, you may open pull requests, issues, and similar (comments, labels, etc.). These don't require pushing on your part beyond what `gh` itself does for an already-pushed branch.
- **Every PR must include a manual test plan** — when opening a PR, add a **How to test manually** section describing the exact steps to exercise the change by hand. Here that means: which markdown files changed, how to render/preview them (e.g. open in a Markdown viewer), any lint command to run, and the expected result. Where a template placeholder or cross-reference changed, note what to verify so the templates still read consistently together.
- **Agentic PR verification (MANDATORY on every PR)** — every PR MUST be verified before merge and the verdict MUST be posted as a PR comment (`gh pr comment`); running it is **not optional**. There's no app to drive here, so the "drive the running app" engine is adapted to a docs repo: render/preview each changed markdown file, run the markdown lint, and confirm no stray `<…>` placeholders leaked into non-template docs and no cross-reference between templates broke — then post that verdict on the PR. The agentic pass **never merges**; it waits for you.
