# <PROJECT> — Claude Guide

<One or two sentences: what the product is and who it's for.>

> **Template.** Copy to `CLAUDE.md` at the new repo's root and fill the `<…>`.
> Replace `@<scope>/shared` with the real package scope (e.g. `@myapp/shared`).
>
> The **Module strategy**, **Stack**, **Monorepo structure**, **Dev workflow**, **Docker & deploy**
> and **CI & git hooks** sections are the opinionated **pnpm-monorepo preset** — replace them with
> your stack, or delete the monorepo-only ones for a single-package or polyrepo project. The
> **governance** sections (Start here, graphify, superpowers, Tests & quality, Quality beyond
> coverage, Real-environment verification, Debugging, Agentic PR verification, Agent orchestration,
> Reuse first, Working rules, Git & GitHub) are universal — keep them verbatim.
>
> Delete this quote block.

## Start here

- **Run `/graphify` before each session.** The persistent graph at `graphify-out/graph.json`
  summarizes architecture, dependencies and cross-cutting concepts without re-reading the repo.
- **Before touching UI:** use the `impeccable` skill. If the project has no design context yet
  (`PRODUCT.md` / `DESIGN.md` at the root), **run `$impeccable teach` first** — it explores the code
  and **interviews you** about the project's direction (register, users, personality, visual
  direction) and writes `PRODUCT.md` + `DESIGN.md`; never hand-author it. Also read `design-system.md`
  (palette/type/components) and `user-stories.md` before defining a slice.
- **Read `docs/FINDINGS.md` before debugging or touching the build** — non-obvious gotchas.
  **Convention:** when you discover something non-obvious that cost time and isn't deducible from the
  code, add a short entry to `docs/FINDINGS.md`.
- **`docs/FACTS.md` is the working-memory file, not a second FINDINGS** — verified facts about this
  repo that every fresh agent would otherwise rediscover (real selectors, which fakes exist, what a
  helper accepts). Read it when you start, append to it when you finish. See
  [Agent orchestration](#agent-orchestration--parallel-where-its-free-batched-where-its-yours).
- **`docs/ENDPOINT_PERMISSIONS.md`** is the authoritative endpoint-permissions reference. Keep it
  current in the same change that adds or modifies endpoints.

## ⚡ graphify — use every session

```text
/graphify            # first run (builds graph from scratch)
/graphify --update   # incremental update (only re-extracts changed files)
/graphify query "<question>"    # architecture questions instead of opening multiple files
/graphify explain "<name>"      # locate a concept or symbol
/graphify path "A" "B"          # dependency path between two modules
```

Outputs in `graphify-out/`: `graph.json` (source of truth), `GRAPH_REPORT.md` (god nodes,
communities, surprising connections), `graph.html` (interactive view).

Run `/graphify --update` at end of session if you touched docs or images (code changes rebuild via
hook if installed).

## ⚡ superpowers — use whenever applicable

Always prefer **superpowers** skills over ad-hoc approaches. If there's even a small chance a skill
applies to the task, invoke it via the `Skill` tool before acting (including before clarifying
questions).

- **Process skills first** — `brainstorming` before creative/feature work, `systematic-debugging`
  before fixing bugs, `test-driven-development` before writing implementation.
- **Then implementation skills** — domain-specific skills guide execution.
- **Verify before claiming done** — `verification-before-completion` / `requesting-code-review`
  before merging.

Flow: `brainstorming → spec (you approve) → writing-plans → plan (you approve) →
subagent-driven-development → finishing-a-development-branch`. **Nothing is implemented without an
approved spec.**

User instructions always take precedence over skills; skills override default behavior. **Skills
refine *how* the work is done; they never override the rules in this file. When a skill and this
`CLAUDE.md` conflict, this file wins.**

### Mode switch

- **"lite mode"** — fully disables superpowers: no skill is invoked, not even the applicability
  check, until **"normal mode"** is said.
- **"normal mode"** (default) — standard superpowers behavior, plus: when delegating coding work,
  dispatch at most 1 agent at a time, and never use a model above Sonnet (no Opus). The cap counts
  **implementation** agents: a read-only review agent runs alongside one, and should — see
  [Agent orchestration](#agent-orchestration--parallel-where-its-free-batched-where-its-yours).
- **"modo desatendido"** (unattended mode) — the user is away and delegates autonomy: work without
  waiting for confirmations and make reasonable decisions yourself instead of asking. In this mode you
  MAY **`git push` the feature branches you create** and **open PRs via `gh`** on your own, so the
  work is ready for review when the user returns. The hard limits still hold and are NOT lifted:
  **never merge anything** (no `git merge`, no fast-forward integration, no `gh pr merge`), **never
  push to `main`** or any protected/default branch directly, and **never** `git push --force` /
  `--force-with-lease`. Deliver everything as pushed branches + PRs for the user to merge. Reverts to
  defaults on **"normal mode"**.

Confirm the switch briefly when it happens.

---

## 🧠 Heavy jobs run inside a memory cgroup (MANDATORY)

**No exceptions:** any long or parallel job started here — the full test suite, coverage, mutation
testing, a production build, Playwright, a `turbo`/workspace fan-out, anything that spawns workers —
runs under a kernel-enforced memory ceiling:

```bash
systemd-run --user --scope --quiet -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- <command>
```

**6 GB is the standing ceiling on this machine** (raised from 4 GB by the user on 2026-08-11); don't
exceed it without being told to. `MemoryHigh` throttles and reclaims, `MemoryMax` is the hard stop,
`MemorySwapMax=0` keeps the job from thrashing swap instead of respecting either. Verify it is
actually in force rather than assuming:
`systemctl --user show <scope> -p MemoryMax -p MemoryHigh -p MemoryCurrent`.

**Cap the tool too — but never *instead* of the cgroup.** Pass the tool's own concurrency limit
(`--concurrency`, `--maxWorkers`, `workers`, `--parallel`) so the job isn't throttled to a crawl by
the ceiling. A tool's default concurrency is not a budget, and an estimate of per-worker RSS is not a
ceiling. Only the cgroup is.

**Check that the ceiling reaches the process that does the work.** A job wrapped in the scope can
hand the real work to a **daemon or worker pool that lives outside it** — a build daemon reconnected
from a previous run, a container engine, a language server, a test runner attaching to workers that
were already up. The wrapper still reports the limit as applied, over a process that isn't doing
anything. The tell is `MemoryCurrent` sitting near zero while the machine swaps. Confirm against the
**worker's** cgroup, not the scope's: `cat /proc/<worker-pid>/cgroup`. If the worker is outside,
either kill the daemon so the job starts its own inside the scope, or configure the daemon's own
limit — a wrapper that reports success over an idle process is worse than no wrapper, because it
buys confidence and delivers nothing.

**Why this is a rule and not advice:** a mutation-testing run on this 24-core box sized its worker
pool from the core count and spawned **23 workers at ~2.3 GB each** — ~50 GB of demand on 31 GB of
RAM. It took the whole machine down hard enough that the user had to power-cycle it; `systemd-oomd`
did not save it. The run before that was wasted too: with the machine starving, **139 of the first
142 mutants "timed out"**, and a timeout is scored as *killed*, so the result came out inflated by
starvation and meant nothing. A job that OOMs the box doesn't merely fail — it also hands you
numbers you'd trust by mistake.

## Module strategy (source of truth — don't deviate) · *pnpm-monorepo preset*

1. **`@<scope>/shared` is COMPILED, not consumed as raw TS.** It has a `build` with `tsc` that emits
   `dist/` (CommonJS + `.d.ts`); `main`/`types`/`exports` point at `dist/`. `api`, `web` and the seed
   import it as compiled JS.
2. **CommonJS in `apps/api` and `packages/shared`.** No `"type":"module"`, no `.js` extensions in
   imports. NestJS's default ts-jest works as-is.
3. **The seed runs with `tsx`** (not ts-node).
4. **`apps/web` (Next 15)** uses Bundler resolution + `transpilePackages:['@<scope>/shared']`.
5. **Recompile `shared` before any consumer uses it:** `pnpm build:shared`. The test/coverage scripts
   (turbo `^build`) and the seed do it automatically.
6. **Prisma pinned to v6.** Prisma 7 generates an ESM client incompatible with the CommonJS `api`.
   Don't bump without migrating the module to ESM.

---

## Stack · *preset*

### Backend (`apps/api/`)

| Tech                      | Version | Role                                                            |
| ------------------------- | ------- | -------------------------------------------------------------- |
| NestJS                    | v10     | Framework — modules, DI, guards, interceptors                  |
| Prisma                    | v6      | ORM — single schema, generated client, migrations             |
| PostgreSQL                | 16      | Primary database                                               |
| Zod (`packages/shared`)   | v3      | DTO validation (`ZodValidationPipe`), shared with the frontend |
| Redis + BullMQ            | —       | *(if applicable)* cache + async jobs                           |
| Passport + JWT            | —       | *(if applicable)* `jwt`, `jwt-refresh`, OAuth strategies       |
| Resend / Mailpit          | —       | transactional email (Mailpit as dev sink), transport switch    |
| S3-compatible + Sharp     | —       | *(if applicable)* images & processing; signed URLs; driver switch |

> **Email and storage are pluggable, never provider-coupled** — both pick the backend by env, behind
> an interface:
>
> - **Email** — a `MailTransport` interface; `MAIL_TRANSPORT` selects Mailpit/SMTP in dev, Resend in prod.
> - **Storage** — a storage driver (`StorageModule.forRoot()`); `STORAGE_DRIVER` selects
>   `local` | `supabase` | `s3`. Use a **self-hosted S3-compatible store (RustFS / MinIO)** in dev for
>   parity with prod. Self-hosted S3 often needs **separate internal vs public** endpoints
>   (`S3_ENDPOINT` for the API, `S3_PUBLIC_URL` for the browser). The API serves **signed URLs, never
>   binaries**.

### Frontend (`apps/web/`)

| Tech           | Version         | Role                                                                                    |
| -------------- | --------------- | --------------------------------------------------------------------------------------- |
| Next.js        | 15 (App Router) | SSR, RSC, routing                                                                       |
| shadcn/ui      | —               | base components in `components/ui/` (DO NOT hand-edit); custom per `design-system.md`    |
| Tailwind CSS   | v4              | Styles                                                                                  |
| TanStack Query | v5              | Server state                                                                            |
| Zustand        | —               | *(if applicable)* client state                                                          |

### Shared (`packages/shared/`)

Enums + Zod schemas + shared TS DTOs between `api` and `web`. Everything that crosses the HTTP
boundary is defined here once. Compiles to `dist/`.

---

## Monorepo structure (pnpm workspaces + Turborepo) · *preset*

```text
/
├── apps/
│   ├── api/            # NestJS 10 + Prisma 6 (CommonJS)
│   │   ├── prisma/     # schema.prisma (entities + enums), migrations/, seed.ts (tsx)
│   │   └── src/        # prisma/ (PrismaService @Global), common/ (ZodValidationPipe, guards),
│   │                   #   health/, <domain modules>
│   └── web/            # Next 15 App Router
│       ├── app/        # routes, providers.tsx (QueryClientProvider), layout.tsx, [locale]/ (if i18n)
│       ├── components/ # ui/ (shadcn, DO NOT edit), <domain folders>
│       ├── hooks/      # custom hooks
│       ├── mutations/  # TanStack mutations
│       ├── schemas/    # form / client-side Zod schemas
│       ├── contexts/   # React contexts
│       ├── types/      # local TS types
│       ├── locales/    # i18n messages (if applicable)
│       └── lib/        # api.ts (typed fetch that validates with shared schemas), utils.ts
└── packages/
    └── shared/         # compiles to dist/ (CommonJS): enums/, schemas/, dto/
```

> DB entities = `apps/api/prisma/schema.prisma` (it's Prisma, not TypeORM; there's no `entities/`
> folder). Infra (Postgres/Redis/Mailpit) lives in `docker-compose`.

---

## Tests and quality

- **Backend:** Jest + supertest — unit `*.spec.ts` colocated with source; e2e separate.
- **Frontend / shared:** Vitest + Testing Library + jsdom — `*.test.tsx` colocated.
- **Browser E2E: Playwright — mandatory**, not "when there are navigation flows". See
  [E2E (Playwright) — mandatory](#e2e-playwright--mandatory) below.
- **Coverage gate: 80%** (statements/branches/functions/lines) in `api`, `web` and `shared`.
  Critical logic ≥90%. Don't lower the gate — exclude infra with justification (Prisma client,
  migrations, `seed.ts`, `main.ts`, `*.module.ts`, `prisma.service.ts`, shadcn-generated). Before PR:
  `pnpm pr-check` (= `pnpm lint` + `pnpm test:cov`).
- **Mutation gate: 60% minimum** over the core-logic scope, blocking on push and reported in CI. A
  coverage gate is blind to a test with no asserts; this one is not. See
  [Mutation gate — the 60% floor](#mutation-gate--the-60-floor-and-it-only-goes-up).

### E2E (Playwright) — mandatory

**Why this is a hard rule.** Unit tests pass while the product is broken: the component renders, the
type-check is green, and then a real click hits an endpoint that doesn't exist, sends the wrong
payload shape, or returns 500. Mocked fetches hide exactly that class of bug, because the mock
encodes what the author *assumed* the API does. Only driving the running app against the real API
proves the feature works.

- **Every user flow needs a spec** — create / edit / delete, navigation, forms, filters, auth-gated
  screens. A slice with UI is not done until its flow has a Playwright spec.
- **Against the running app and the REAL API.** Boot the stack from Playwright's `webServer` (or a
  compose target) and hit real endpoints against a **disposable test database** — never the dev DB.
  **Do not stub the network layer in E2E**; that's what the unit/integration layer is for.
- **The minimum assert is not "the button exists".** A flow is verified when: the request actually
  goes out, it answers 2xx, the UI reflects the change, and **the change survives a reload**
  (i.e. it was persisted, not just optimistic local state).
- **Fail loudly on noise.** Wire `page.on('console')` and `page.on('response')` so the spec fails on
  console errors and on unexpected 4xx/5xx — those are the API mismatches this layer exists to catch.
- **Accessible locators only** — `getByRole`, `getByLabel`, `getByText`; never brittle CSS/XPath.
  This doubles as the semantics layer the agentic PR verification depends on (see
  [Agentic PR verification](#agentic-pr-verification-mandatory-on-every-pr)).
- **Blocking on push.** `pnpm test:e2e` runs in the pre-push hook; a red E2E means no push.
- **A UI bug fix gets a failing E2E first**, then the fix — same rule as unit regressions.
- **Non-web surfaces generalize.** Native Android (Jetpack Compose) → **Maestro**, which has the same
  mandatory status Playwright has here — see
  [Native Android (Jetpack Compose) — Maestro](#native-android-jetpack-compose--maestro) below;
  desktop shell → Playwright's `_electron`; API-only services → a `pytest` + `httpx` (or supertest)
  smoke that exercises the real HTTP surface. The rule is "drive the real thing", not "use Playwright".

### Native Android (Jetpack Compose) — Maestro

**Maestro is the E2E engine for native Android, exactly as Playwright is for the web** — same status,
same rule: a slice with a Compose screen is not done until its journey has a committed flow that runs
green against the real APK on an emulator. It is also the **discovery** tool: how you find out what
the running app actually exposes, instead of guessing selectors from the source.

Flows are YAML under `.maestro/`, one file per user journey (optional workspace `config.yaml` at the
root):

```yaml
# .maestro/<flow-name>.yaml
appId: <com.example.app>
name: <what this journey proves>
tags:
  - smoke
---
- launchApp:
    clearState: true
- tapOn:
    id: "<fab_add_item>"       # Modifier.testTag — needs the opt-in below
- inputText: "<text>"
- tapOn: "<Visible label>"     # visible text also works
- assertVisible:
    text: ".*<regex>.*"        # selectors accept regex
- extendedWaitUntil:
    visible: "<Screen title>"
    timeout: 10000
```

```bash
maestro list-devices                          # what is actually connected
maestro start-device --platform=android --device-model=pixel_6 --device-os=android-33
maestro test .maestro/                        # a directory works; whole suite
maestro test .maestro/<flow>.yaml -c          # --continuous: re-runs on save while you iterate
maestro test .maestro/ --include-tags=smoke --format=JUNIT --test-output-dir=build/maestro
maestro check-syntax .maestro/<flow>.yaml     # exits 1 on an invalid command — a usable hard gate
maestro record --local .maestro/<flow>.yaml   # video, for a bug report or a PR comment
```

**The Compose gotcha that costs an afternoon.** `Modifier.testTag("x")` is **invisible to Maestro by
default**: Compose keeps test tags in its own semantics tree, while Maestro reads the Android view
hierarchy through UiAutomator. Until you opt in, only `text` and `contentDescription` are matchable —
so flows silently fall back to user-visible strings and break on the first copy edit or in the other
locale. Turn tags into resource ids once, on a root composable:

```kotlin
@OptIn(ExperimentalComposeUiApi::class)
Box(Modifier.semantics { testTagsAsResourceId = true }) { <AppNavHost>() }
```

Then `tapOn: { id: "<fab_add_item>" }` resolves.

#### Discovery — ask the running app, don't guess

```bash
maestro hierarchy             # full view hierarchy of the connected device
maestro hierarchy --compact   # CSV: element_num,depth,attributes,parent_num — greppable
maestro mcp                   # MCP server over STDIO: device + automation as tools for an agent
```

`maestro hierarchy` is the ground truth about what is reachable: **if a control isn't in that tree, no
flow can tap it and no screen reader can announce it** — that is an accessibility bug before it is a
test problem. Run it before writing a flow and after adding a screen. `maestro mcp` exposes the same
capabilities to an LLM agent over MCP, which is what the agentic PR pass should drive instead of
screenshot coordinates.

> `maestro studio` was removed in Maestro 2.x — use `hierarchy` and `mcp`. Check `maestro --help`
> before trusting a command you remember; the CLI moves.

The rules mirror the Playwright ones:

- **Against the real APK on an emulator**, never a mocked backend. Boot one with `maestro start-device`
  if `maestro list-devices` shows nothing; `--device` picks the target when several are attached.
- **`clearState: true`** at the top makes a flow independent — and it **wipes that app's data on the
  device**, so flows belong on a dedicated emulator, never on a daily phone.
- **Prefer `id` over `text`** once `testTagsAsResourceId` is on. Text selectors are copy- and
  locale-dependent; if the app ships two locales, a text-only flow is a flow that passes in one of them.
- **A UI bug fix gets a failing flow first**, then the fix.
- **`maestro check-syntax` in the pre-commit hook** — it exits non-zero on an invalid command, so a
  typo'd `tapOnn` never reaches CI. `--format=JUNIT --test-output-dir=…` is what CI consumes.
- **`--headless` is web-only.** It does nothing for an Android run; don't reach for it when a flow hangs.

### Run before declaring done

| Change touches               | Run before claiming success                                          |
| ---------------------------- | -------------------------------------------------------------------- |
| backend service/controller   | `pnpm --filter @<scope>/api test` (+ `pnpm test:e2e` if cross-module) |
| frontend component/hook/util | `pnpm --filter @<scope>/web test`                                    |
| **any user-facing flow** (new screen, form, button wired to an endpoint) | `pnpm test:e2e` — **required**, unit tests do not prove the flow works |
| something ambiguous or large | `pnpm test:all`                                                      |

### What to test per folder

| Folder | What | Status |
| --- | --- | --- |
| `lib/` | Pure utilities, hooks — deterministic, minimal mocks | Pending |
| `components/` | Logic-bearing components: forms, dialogs, toggles. Mount + `user-event`. Exclude UI primitives | Pending |
| `hooks/` | Custom hooks via `renderHook`. Mock timers/fetch only when unavoidable | Pending |
| `src/*` services / `app/api/` | Call the exported handler/service directly; check status codes, validation, error paths | Pending |

### TDD — required for new logic

For new code in `services/`, `lib/`, `hooks/`, non-primitive `components/`, shared schemas and form logic:

1. **Red** — write a failing test that describes the behavior.
2. **Green** — implement the minimum to pass.
3. **Refactor** — clean up under green tests.

Exceptions (TDD not required): pure visual/style changes (CSS, layout, copy); UI primitives (tested
indirectly by consumers); spikes/exploration — but add tests before merging.

### Hard rules (no exceptions)

- **Never claim done without showing test output.** "Type-check passes" is not "it works".
- **New endpoint / DTO / hook / schema → needs a test.** No exceptions.
- **A bug fix needs a failing regression test first**, then the fix (see `systematic-debugging`).
- **Never delete, `.skip` or `.only` a test to get green.** Fix the code or the test on purpose.
- **No feature with UI is done without a green E2E against the real API.** Driving the running app
  is the proof — **Playwright** on web, a **Maestro flow on a real emulator** for a Compose screen;
  type-check, unit tests and a screenshot are not. If the flow has no spec, the flow is not finished.
- **Never mock the API to make an E2E pass.** A mocked E2E proves the mock works, not the product.
- **Don't lower the 80% gate to ship** — exclude untestable modules in config with a written reason.
- **Test over mock** — exercise real code with minimal stubs; don't mock entire modules.

### Operative conventions

- **Global setup file** — define `matchMedia`, `ResizeObserver`, `IntersectionObserver`,
  `localStorage` stubs once. Don't redefine per test.
- **Split by aspect** when a test file exceeds ~300 LoC: `.flow.test.ts`, `.errors.test.ts`,
  `.branches.test.ts`.
- **Exclude with justification** in config, never silently. Example:

  ```js
  // JSDOM cannot simulate layout/animation timing — cover via E2E
  exclude: ['src/hooks/use-grid-reflow.ts']
  ```

## Quality beyond coverage

**Coverage measures how much code runs, not whether it's correct.** This is especially treacherous
with AI: it tends to write the test *and* the code in one move, so if it misread the requirement, both
encode the same mistake and the test passes happily. 80% coverage with weak asserts is a false sense
of security. These gates attack that blind spot.

- **Mutation testing** *(highest priority — and the one gate with a hard number, see below)* —
  **Stryker** (JS/TS), **PITest** (Kotlin/JVM), **mutmut** / **cosmic-ray** (Python),
  **cargo-mutants** (Rust) inject deliberate bugs (`>` → `>=`, drop a line, flip a boolean) and check
  some test fails. A surviving mutant means the code is *covered but not verified*. **Concrete recipe
  that works:** scope `mutate` to a **pure compute function extracted out of the service**
  (mocked-ORM tests can't kill query-shape mutants), pick the runner per package (jest-runner vs
  vitest-runner), and set `thresholds: { high: 90, low: 80, break: 60 }` — `break` is the gate and 60
  is the floor. This is the direct antidote to AI's misleading coverage.
- **Property-based testing** *(highest priority)* — **fast-check** (JS/TS), **Hypothesis** (Python).
  Define invariants ("deserialize(serialize(x)) == x", "final price is never negative") and let the
  framework generate hundreds of cases, including the weird boundaries nobody thinks of. Catches logic
  errors that hand-picked examples miss.
- **Runtime boundary validation** — **Zod** (TS), **Pydantic** (Python) to validate everything
  crossing a boundary: API responses, forms, DB data. AI trusts types that don't hold at runtime; this
  turns those assumptions into explicit errors instead of silent failures.
- **Strict types + static analysis** — TypeScript in real `strict` mode (**including
  `noUncheckedIndexedAccess`**), type-aware ESLint, and a SAST (**Semgrep** or **CodeQL**). SAST
  matters because AI introduces vulnerabilities easily (injection, hardcoded secrets) that no
  functional test catches.
- **E2E / smoke tests** *(mandatory, not a nice-to-have)* — **Playwright** (web), **Maestro**
  (native Android/iOS — YAML flows plus `maestro hierarchy`/`maestro mcp` for discovery). Verify what
  unit tests can't: that the app *actually boots* and the full flow
  works. Code routinely passes every unit test while the app won't start or the frontend assumes an
  API contract the backend doesn't honor. This is the single highest-yield gate against
  "implemented but broken on first click" — see the hard rules in
  [E2E (Playwright) — mandatory](#e2e-playwright--mandatory).
- **Dependency auditing** — AI invents non-existent packages ("slopsquatting") and pulls vulnerable
  versions. Use `npm ci` with a frozen lockfile, `npm audit` / Dependabot / Snyk in CI, and verify
  every new dependency actually exists and is the one you think it is.
- **Dead-code elimination** — **Knip** (JS/TS) finds unused files, exports, types and dependencies
  across the workspace (monorepo-aware; auto-detects Next/Vite and `pnpm` workspaces). Drop a
  `knip.json` at the repo root (zero-config to start: `{ "$schema": "https://unpkg.com/knip@5/schema.json" }`)
  and run `pnpm dlx knip` — or add a `"knip"` script once you want it in the loop. Pruning dead code
  shrinks the surface every session (and the AI) has to reason about and keeps `package.json` honest,
  complementing the dependency audit above. AI-written code accretes orphaned helpers and unused
  exports fast, so run it periodically on web projects.

**Process rule (worth more than any tool): don't let the AI define the acceptance criteria.** You
write or review the important test cases yourself — at least the key asserts and the requirement's
edge cases — and have the AI implement against them. That breaks the loop where the same
misunderstanding lives in both the test and the code. Mutation testing is the automated backstop for
this, but the judgment about *what the system should do* stays yours.

Priority by immediate payoff: **mutation + property-based testing first** (they hit the current blind
spot), then **runtime validation and a couple of E2E smoke tests**.

### Mutation gate — the 60% floor, and it only goes up

Coverage answers *"did any test run this line?"*. Mutation answers *"would any test have noticed if
the line were wrong?"*. A test with no assert scores 100% coverage, which is why this gate is the one
with a hard number attached.

- **Floor: 60%**, measured over the **core-logic scope** — `<domain/, services/, pure compute
  modules>` — not the whole tree. Repositories, DAOs, framework glue and view code dilute the score
  into noise: a mutant inside a mocked query is not a bug anyone can write a test against. Scope
  narrow, gate hard; scope wide, gate meaningless.
- **The threshold is a ratchet.** Set it to today's real score rounded down, never under 60, and
  raise it in the same PR that raises the score. **Lowering it to make a push go through is exactly
  what the gate exists to prevent** — a score that dropped means a test stopped verifying something.
- **Not at 60 yet?** Ship the gate **advisory** (it reports, it never fails) with the current score
  and the date written next to it, and owe a PR that reaches 60 before the next feature. Advisory is
  a waypoint, not a resting place.
- **Doesn't apply to this repo?** Write that here, with the reason (no executable code; packaging-only;
  byte-matching decompilation; generated sources). An unwritten exemption gets re-litigated every few
  months; a written one does not.
- **It does not mean chasing 100%.** Equivalent mutants exist (inlined stdlib, generated glue,
  coroutine/async branches) and are annotated and left alone, not tested into submission.

Read the report before quoting a number: **SURVIVED and NO_COVERAGE mean opposite things** and the
headline percentage mixes them. A survivor is code that runs while nothing asserts on the result — a
real hole. NO_COVERAGE is code the mutation runner never reached, which is often a runner limitation
(Robolectric under PITest, for one) rather than a missing test. Split them before quoting.

The fix for a survivor is almost always the same: **assert the concrete expected value, written out
by hand**. A test that recomputes the expectation with the same expression the code uses moves with
the mutation and agrees with it — 100% line and branch coverage, zero verification.

| Stack | Tool | Gate command |
| --- | --- | --- |
| JS/TS | **Stryker** | `pnpm test:mutation` (`stryker run`, `thresholds.break: 60`) |
| Kotlin / JVM | **PITest** | `./gradlew pitestDebug -Ppitest.threshold=60` |
| Python | **mutmut** (or **cosmic-ray**) | `mutmut run` + a score check on `mutmut results` |
| Rust | **cargo-mutants** | `cargo mutants --in-place --error-percent 40` |

**A mutation run is a heavy job** — it forks one JVM/worker per core and sizes nothing for you. Run it
inside the memory cgroup and cap the worker count: see
[Heavy jobs run inside a memory cgroup](#-heavy-jobs-run-inside-a-memory-cgroup-mandatory).

---

## Real-environment verification — what no in-process test can prove

Some properties are invisible to the entire in-process suite no matter how many tests you add,
because the test runtime never restarts a process, never talks to a real server, never runs out of
disk, and never lets the scheduler cancel anything. **jsdom is not a browser, a mocked ORM is not a
database, a fake clock is not time, and an in-memory DB is not the one the user has on disk.**
Those properties need a script that drives the **real artifact on real hardware** — a real browser,
an emulator, a VM, a container, the target machine — and asserts on what is externally observable:
log lines, exit codes, HTTP responses, rows in the database, files on disk.

**Write that script, commit it, and name it here.** It must run by hand with no arguments, print a
per-phase `PASS`/`FAIL`, and exit non-zero on the first failure:
`<scripts/verify-<flow>-on-device.sh>` (flags: `<--no-install>`, `<--keep-state>`).

**The run happens on real hardware or an emulator — never on a stand-in for the thing under test,**
and never on the user's daily device/workstation when the check writes state. Boot the emulator /
disposable VM / throwaway container; that is the target.

### The names, so you can ask for them by name

| Name | What it means |
| --- | --- |
| **E2E / on-device acceptance test** | Drives the real build against the real backend and asserts on observable behaviour — log lines, HTTP status, rows in the DB, files written — never on internals. The phases of the script above. |
| **Contract test** | Checks that the **client's assumptions about the server's responses** actually hold. These are exactly the assumptions no type system on the client side can see: a filter that is a strict `>` and not `>=`, a timestamp column stored with microseconds, a field the docs call optional and the server always sends. |
| **Mutation testing** (on real hardware: by hand) | Revert the fix, re-run the check, confirm it goes red, restore. Stryker / PITest / mutmut automate this for in-process code; against a device or a machine you do it manually. **A check that has never failed has not been tested.** |
| **State-invariant test** | Asserts a relationship **between two stores** that no single unit test owns — e.g. a delta watermark must never outlive the database it describes. Each store is individually correct; the pair is what breaks. |
| **Test pollution / isolation leak** | A test writing to *production* state — the installed app's storage, the dev database, the user's config directory, the real keystore. It passes, and quietly destroys data on the next run. |

### Rules that came out of real bugs, not theory

- **Prove every new check can fail before you trust it green.** Revert the fix, watch the check go
  red, restore it. This applies to unit tests written after the fact *and* to real-environment
  checks. A green you have never seen turn red is not evidence.
- **Never assert on a count you cannot predict.** A check that fails "above five rows" reports PASS
  against a deliberately broken build whenever the data happens to cluster differently — how many
  rows a bad cursor drags back depends on the dataset, not on the bug. Assert the **invariant**
  (the watermark carries milliseconds; the response is empty; the ids match), never a symptom whose
  magnitude varies with the data.
- **A watermark, cache marker or cursor must die with the data it describes.** Clearing one without
  the other is silent, permanent data loss — no crash, no log, no failing test.
- **Anything that touches machine-global state must restore it.** Device storage, the user's config
  dir, the real database, the system keystore, installed packages: save it, and restore it in the
  teardown that runs even when the test fails.
- **Run the real-environment suite the way that actually works on this machine**, not the way the
  docs say. When the canonical task hangs, deadlocks or needs a display this box doesn't have, write
  the command that works into `docs/FINDINGS.md` and use it:

  ```bash
  <the exact command that works here>
  ```

---

## Debugging — keep the loop from running away

What a bug costs is not the fix. It is the number of times you go around
`build → deploy → reach the state → observe` before you know what to fix, multiplied by what one
lap costs. Everything below attacks one of those two factors. **Each rule carries the number it
came from** — a real 15 h session — because a rule with no measured cost behind it gets deleted in
the first cleanup. Where this project hasn't measured its own, the number is marked
`<!-- pendiente de medir -->` until someone does.

### The loop is the cost

- **Measure before you ablate.** Ablation costs one lap per hypothesis and answers yes/no.
  Instrumentation costs one lap total and answers *what is actually happening*. **Measured: 28
  ablations over 1 h 42 min ruled things out and moved nothing; a single batch of probes, 13 min,
  changed the question and the bug fell on the next round.** The rule that batch produced: **if a
  pipeline completes every phase with non-empty output, the output exists** — stop asking "why
  doesn't it appear" and start asking "where does it appear". They are different questions and the
  second one is cheap.
  <!-- instanciar: qué pipeline se sonda aquí — fases de composición/render en UI,
       request → validación → serialización → respuesta en backend, hidratación/layout en web -->
- **Budget the lap, then attack the dominant term.** Time the four phases once and write the real
  numbers into the table below; one of them dominates and the other three are noise. In the measured
  case "reach the state" was 60 s × 30 reproductions — half an hour of pure waiting — and it died to
  a shortcut nobody had bothered to write. **If a bug needs more than three reproductions, write the
  shortcut before the fourth**: a deep link, a dev-only route, an environment snapshot, a seeded
  fixture. Commit it as `<scripts/repro-<bug>.sh>` and name it in the `docs/FINDINGS.md` entry, so
  the next person pays zero.

  | Lap phase | Command here | Measured |
  | --- | --- | --- |
  | build | `<…>` | `<n s>` |
  | deploy / install | `<…>` | `<n s>` |
  | reach the state | `<…>` | `<n s>` |
  | observe | `<…>` | `<n s>` |

### A finding is not a reproduction

- **Whoever reviewed read the code; they did not run it.** Reproduce a review finding yourself
  before sending anyone to fix it, and **if the implementer says they can't reproduce it, believe
  the implementer over the reviewer** — one of them has the thing running. **Measured: 1 h 25 min
  spent chasing a bug that did not exist.** This is the same reason the agentic PR pass is advisory
  and never vetoes on its own (see
  [Agentic PR verification](#agentic-pr-verification-mandatory-on-every-pr)), and the reason
  `receiving-code-review` asks for verification rather than agreement.
- **A test that refuses to go red is data, not a failure.** The fourth failed attempt to pin down
  that non-existent bug is precisely what uncovered the real one, pointing the opposite way.
  Reporting "I cannot make this fail" is a result and it gets reported; covering it with a green
  test throws away the only signal the round produced.
- **Before demanding a red, ask whether the mechanism can produce one.** If another layer of the
  framework masks the effect, no amount of insisting will turn the test red, and the time goes into
  the test instead of into the bug. **Measured: over 1 h on two reds that were structurally
  impossible.** Establish that the failure is observable at that layer first; if it isn't, move the
  assertion to the layer where it is — that is what
  [Real-environment verification](#real-environment-verification--what-no-in-process-test-can-prove)
  is for.

### Tests that cannot fail

The [mutation gate](#mutation-gate--the-60-floor-and-it-only-goes-up) already names the worst case —
an expectation recomputed with the same expression the code uses, which moves with the mutation and
agrees with it. It is not the only one. **Enumerate for this stack the assertions that are inert by
construction**, because none of them show up as a failure, a warning, or a coverage drop:

| Inert by | Looks like | Applies here |
| --- | --- | --- |
| assertions disabled at runtime | the assert keyword compiled out or off by default | `<…>` |
| a promise / coroutine never awaited | the assertion runs after the test already passed | `<…>` |
| self-writing snapshots | first run records whatever happened and calls it expected | `<…>` |
| permissive mocks | the double returns the expected value by default, unasked | `<…>` |
| expectation computed like the code | same expression on both sides of the equals | `<…>` |

<!-- instanciar: borra las filas que este stack no puede producir y nombra el mecanismo concreto -->

**Every assertion is watched failing once**, and expected values are written out by hand. This is
the same rule [Real-environment verification](#real-environment-verification--what-no-in-process-test-can-prove)
states for on-device checks — it applies to in-process tests with no exception.

### The environment is a claim until it is measured

- **Verify the limit reaches the process doing the work** — see the check in
  [Heavy jobs run inside a memory cgroup](#-heavy-jobs-run-inside-a-memory-cgroup-mandatory). A
  wrapper that reports success over an idle process is worse than no wrapper: it buys confidence
  and delivers nothing.
- **Environment claims get measured or they don't get made.** "That heap sounds low" produced a
  recommendation that was simply wrong. Measuring it — three runs per setting, GC pause totals, real
  peaks, not one run each — gave a **0.4% difference, below the run-to-run variance**. **No
  performance tuning lands without a before/after over more than one run**, and a difference smaller
  than the spread between runs is not a difference.

### Locate the rule before you pick a side

- **A rule that lives in one layer and isn't shared by the others fails in the wrong place.** The
  symptom surfaces where the assumption breaks, not where it is written, which is why the fix keeps
  landing in the innocent layer. Find which layer owns the rule first, then decide which side gives.
  The **contract test** row in
  [Real-environment verification](#the-names-so-you-can-ask-for-them-by-name) is how you pin one
  down once you know it exists.
- **Replacing a component can remove capabilities in silence.** When you swap one API for another,
  enumerate what the old one did that the new one does not, and say it out loud in the PR — nothing
  will fail to compile. **An optional parameter that defaults to off is a capability that only
  exists if the caller remembers it**, which over a few months means it does not exist.

---

## Dev workflow (scripts in `package.json` — cross-platform, no `make`) · *preset*

```bash
pnpm install        # install + generate Prisma client
pnpm infra:up       # start infra (postgres, redis, mailpit)   | infra:down | infra:clean
pnpm db:deploy      # apply migrations   | db:migrate (new) | db:seed | db:shell
pnpm build:shared   # compile packages/shared to dist/
pnpm test           # unit for the 3 packages | test:e2e | test:cov (gate) | test:all
pnpm pr-check       # lint + coverage      | lint | type-check
```

First boot: `pnpm install` → `pnpm infra:up` → `pnpm db:deploy` → `pnpm db:seed`.

Two dev modes (pick one per project):

- **Apps on host** (fast to iterate): `infra:up` (only postgres/redis/mailpit in docker) +
  `pnpm --filter @<scope>/api start:dev` and `pnpm --filter @<scope>/web dev`.
- **Full docker** (everything in containers): `docker compose up` brings up infra + api + web; hot
  reload via code bind-mount (each app's Dockerfile `dev` target).

## Docker & deploy (full docker on Coolify) · *preset*

Services that RUN = one container each. `packages/shared` is NOT a container: it's a library, compiled
**inside** the api and web images.

| Service      | Where             | Note                                                  |
| ------------ | ----------------- | ----------------------------------------------------- |
| postgres     | Coolify-managed   | automatic backups                                     |
| redis        | Coolify-managed   | cache/lockout                                         |
| api (NestJS) | own Dockerfile    | **internal**, no public domain                        |
| web (Next)   | own Dockerfile    | public domain; proxies `/api` → api over internal net |
| shared       | —                 | no container, baked into api and web at build time    |

- **One Dockerfile per app** (`apps/api/Dockerfile`, `apps/web/Dockerfile`), multi-stage with `dev`
  (bind-mount + `pnpm dev`, for the local compose) and `prod` (slim image) targets.
- **prod api:** `pnpm install` → `build:shared` → build api → minimal runtime; startup runs
  `prisma migrate deploy` before booting.
- **prod web:** Next `output:'standalone'`; copies `.next/standalone` + `static`.
- **Same-origin API calls:** `next.config` `rewrites()` maps `/api/:path*` → internal api; `lib/api.ts`
  uses `process.env.API_INTERNAL_URL` in RSC and `'/api'` on the client (no CORS, works from mobile).
- **Email:** transport switch — Mailpit in dev, Resend in prod (`MAIL_TRANSPORT`).
- Env per service in Coolify; secrets outside the repo.

## CI & git hooks · *preset*

**Policy — heavy tests run locally on push, CI stays lean.** The full suite is the *local* gate;
GitHub Actions only re-checks the important, cheap things plus security.

- **Pre-push (husky) runs the FULL existing test suite, E2E included** —
  `pnpm lint && pnpm type-check && pnpm test:all && pnpm test:e2e` (coverage gate via
  `pnpm test:cov`; Playwright boots the app via its `webServer` against a disposable test DB).
  Nothing that exists is skipped: if a suite exists, it runs before the push. **The E2E step is
  blocking** — it's the only gate that proves the API contract actually holds when a human clicks,
  so never demote it to advisory or move it to CI to "make the hook faster". Emergency bypass only:
  `--no-verify`, and then you own the breakage.
- **Pre-push also runs the mutation gate** — `pnpm test:mutation` over the core-logic scope with the
  **60% threshold** ([Mutation gate](#mutation-gate--the-60-floor-and-it-only-goes-up)), inside the
  memory cgroup and with the worker count capped. Three checks, three different questions: *do the
  tests pass?* (suite), *does any test go through this code?* (coverage), *does that test verify
  anything?* (mutation). The third is needed because the second is blind to it — a test with no
  assert reports 100% coverage. It is the last step of the hook because it is the slowest; when it
  makes the hook unbearable, narrow the **scope**, never the **threshold**.
- **GitHub Actions — only the most important & efficient checks** (don't re-run the heavy suite CI
  already paid for pre-push):
  - `ci.yml` → `pnpm lint` + `pnpm type-check` (fast; the full test run already happened pre-push).
  - `mutation.yml` (**PRs against the default branch only** — too heavy for every branch push):
    `pnpm test:mutation` over the same scope and the same 60% threshold as the hook, with the HTML
    report uploaded as an artifact (a bare percentage is not actionable; the survivor list is).
    **It ships `continue-on-error: true`.** Promote it to a blocking gate — drop the flag, add it to
    the branch's required checks — once the score has cleared the threshold on two consecutive runs.
    Write the promotion date here when you do it, so "advisory" doesn't quietly become permanent.
  - `security.yml` (**separate workflow, zero overlap**):
    - **Dependency audit — BLOCKING gate**: `pnpm install --frozen-lockfile` (proves the lockfile is
      honest — guards against invented/"slopsquatted" packages) + `pnpm audit --prod
      --audit-level high`. **No `continue-on-error`; add it to the branch's required checks.** Fix a
      failing audit by bumping via `pnpm.overrides`, never by lowering `--audit-level`.
    - **SAST (Semgrep) — advisory**: `semgrep/semgrep` with `p/typescript` `p/react` `p/nodejs`
      `p/secrets` (excludes shadcn primitives + tests). Keep `continue-on-error: true` until findings
      are triaged, then promote to a gate.
- **Other husky hooks**: pre-commit `lint-staged`; commit-msg `commitlint` (Conventional Commits).
  Installed by `prepare: husky` after `pnpm install`.

---

## Agentic PR verification (MANDATORY on every PR)

**Every PR MUST be verified end-to-end before merge, and the verdict MUST be posted as a PR comment**
(`gh pr comment`). Running the pass and posting the verdict is **not optional**. Once a PR exists, a
headless agent **drives the running app end-to-end** and posts the verdict, then **waits for you to
close/merge**. Its job is to catch what diffs and unit tests miss: missing buttons, unimplemented
content, dead flows, screens that don't match the spec. The verdict is informational for gating (it
never merges anything) — but producing it on every PR is required.

- **Local & headless.** Runs on your machine via `claude -p` (headless/print mode), posts with
  `gh pr comment`. No CI minutes, no repo secrets. Fits an unattended loop.
- **Two surfaces, two engines** (one orchestrator picks by which paths the PR touched):
  - **Web** → **Playwright MCP** (headless Chromium) against `localhost`.
  - **Native mobile (Compose / SwiftUI)** → **`maestro mcp`** — Maestro's own MCP server, which
    exposes the same device and automation commands the committed flows use, so whatever the agent
    discovers can be written straight back as a `.maestro/` flow. It navigates the native
    **accessibility tree** over `adb` rather than screenshot coordinates. Run it against an
    **emulator or a dedicated test device**, and pair it with `maestro hierarchy` to see what is
    actually reachable. Alternatives if it is unavailable: **mobile-mcp**, or **appium-mcp**
    (UiAutomator2 / XCUITest drivers). iOS analog via the XCUITest driver.
  - **Any other runnable surface** generalizes the same way — Playwright covers any web app;
    Python / API smoke via `pytest` + `httpx`.
- **Reliability key = semantics.** Agentic navigation is only as reliable as the accessibility layer:
  good ARIA roles on web, `Modifier.testTag(...)` / `contentDescription` / `Modifier.semantics { }` on
  Compose. Without labels the agent falls back to fragile screenshot coordinates. **Audit that the
  flows you verify are labeled** before relying on this.
- **Two layers.** Deterministic tests (Playwright specs on web, Maestro flows + Espresso/Compose on
  mobile) are the
  **hard merge gate** — they already ran and passed pre-push, so the PR arrives with its flows
  proven. The agentic pass is **advisory**: it explores the new surface, **writes the regression
  specs that are missing** (a flow the agent had to discover by hand is a flow with no spec — that's
  a finding, report it), and leaves a readable verdict. Because the agent is
  non-deterministic, it **never vetoes a merge on its own** — its value is coverage and a legible
  report, not gatekeeping.
- **Cases come from the spec.** Draw the scenarios from the spec's `## Cases` / `## Casuísticas` block;
  tag them `[web]` / `[mobile]` when one spec covers both surfaces.
- **Trigger.** It's the **last step of the superpowers pipeline, right after a PR exists**:
  - **"modo desatendido"** — the agent pushes the branch, opens the PR, and fires verification itself.
  - **"normal mode"** — you open the PR; the agent then runs the local `verify-pr.sh` and posts the
    verdict (**mandatory before merge**, not merely on request — running the script + `gh pr comment`
    needs no push, so this respects the never-push default). Runnable by hand anytime.
- **Hard limits** (these do not relax in any mode): the verdict **awaits your close** and the agent
  **never merges** — see **Git & GitHub**. Point it at a **dedicated emulator / test device, never your
  daily phone**. Scope `--allowedTools` to exactly what the run needs; `--dangerously-skip-permissions`
  only in a controlled local env, never as a habit. Confirm flag names with `claude -p --help`.

Pasteable orchestrator (`scripts/verify/verify-pr.sh`) + `.mcp/*.json` configs: see
[`../PROMPT_TEMPLATES_WEB.md`](../PROMPT_TEMPLATES_WEB.md) §9.

---

## Agent orchestration — parallel where it's free, batched where it's yours

Delegating work to agents moves the bottleneck from typing to **scheduling**: what waits on what,
what each agent has to rediscover, and which decisions quietly stop being yours. Same convention as
[Debugging](#debugging--keep-the-loop-from-running-away) — every rule carries the number it came
from, out of the same measured 15 h session.

- **Review is not on the critical path.** Reviewing task N and starting task N+1 are independent
  whenever they touch different files. Serialized, review is **10-15% of the wall clock** and blocks
  everything queued behind it; run in parallel it costs nothing at all. **On receiving an
  implementation report, dispatch its review and the next implementation in the same turn.**
  This is the one sanctioned exception to *"at most 1 agent at a time"* in
  [normal mode](#mode-switch): the cap is one **implementation** agent. A review agent reads and
  reports — it writes nothing, so it cannot race the implementer.
  <!-- instanciar: cuántos agentes en vuelo a la vez, y cuál es el recurso exclusivo del proyecto
       (emulador, base de datos de dev, puerto del dev server, dispositivo físico) —
       como mucho un agente tocándolo -->
- **Keep one shared facts file.** Every fresh agent rediscovers the same things: the real selector,
  which fake already exists, what that helper actually accepts. Keep `docs/FACTS.md` in the
  workspace, have each agent append to it when it finishes, and hand it to the next one in its
  dispatch. What belongs there: **facts verified against the repo or the device**, never opinions or
  plans. It is not `docs/FINDINGS.md` and does not replace it — FINDINGS holds the durable gotcha
  that is *not* deducible from the code, FACTS holds what is perfectly deducible and merely
  expensive to rediscover, and FACTS is allowed to go stale and die with the branch.
- **Plans carry contracts, not literal code.** The agent **trusts** the code you put in the plan; if
  you never compiled it, you have written an error wearing authority. **Measured: 4 wrong code
  blocks, 15-40 min of detour each.** Write exact names, exact signatures, and "mirror the shape of
  `<X>`" — claims the agent can verify against the repo — and reserve literal code for what you have
  actually run. This is what `writing-plans` produces; keep it that way when you edit the plan by
  hand.
- **Batch the discretionary decisions.** The work that shows up along the way — a capability being
  quietly dropped, a missing script, an adjacent bug — added up to **5-6 h of 15**. Every one was
  justified on its own; deciding them as they appear is what takes them away from you. Accumulate
  them and ask **once per batch, with the estimated cost of each**. In **"modo desatendido"** there
  is nobody to ask, so the batch goes into the PR body as a list with its costs — the decision is
  still yours, it just moves to review time.
- **What never gets cut.** With the numbers on the table: review was **1.5 h of 15**, and it found a
  `create()` silently discarding fields, a 404 caused by SQL deduplication, a silent merge that
  corrupted data, a delete-and-recreate with no transaction, and several inert assertions. **Cutting
  review does not give time back; it defers it to production.** If something has to be cut, cut
  reproduction (write the shortcut — see
  [Budget the lap](#the-loop-is-the-cost)) and cut serialization (dispatch the review in parallel).
  Never verification.

### Day one — the numbers that fill the blanks

Three measurements, taken once at the start of a project, turn every `<…>` above into something
enforceable. None of them takes more than an afternoon.

1. **The lap** — time `build → deploy → reach the state → observe` once, on a real bug if there is
   one, and write the seconds into the table in
   [The loop is the cost](#the-loop-is-the-cost). Whichever phase dominates is the one that gets a
   shortcut script; the rest are noise and stay unoptimized.
2. **The exclusive resource** — name the thing only one agent can hold at a time (emulator, dev
   database, dev-server port, a physical device) and write it into the orchestration note above.
   Everything else parallelizes; this is the one that corrupts a run when two agents touch it.
3. **The inert assertions** — break one assertion on purpose and run the suite. Anything still green
   is inert. Then walk the table in [Tests that cannot fail](#tests-that-cannot-fail), delete the
   rows this stack cannot produce, and name the mechanism for the ones it can.

Record all three in this file, not in a session — the point is that the next session inherits them.

---

## Reuse first — search before you write

The default failure mode of an agent (and of a tired human) is to write the thing that already
exists: a second `formatPrice`, a fourth bespoke modal, a `Button` that is 90% the one in the design
system with one colour hardcoded. Nothing breaks — that is what makes it expensive. The copy drifts,
the fix lands in one of them, and the design system stops describing the product.

- **Search before writing. Every time.** Before creating a component, hook, helper, type, DTO,
  fixture or script, look for it by name *and* by behaviour (`grep -ri "format.*price"`, read
  `packages/shared`, `<apps/web/components/ui>`, the design system doc). "I didn't know it existed"
  is a search you didn't run, not an excuse.
- **Extend or parameterize — don't clone.** If something is 80% right, add the prop/parameter/variant
  to it. A copy with three lines changed is two things to maintain and one of them will be forgotten.
- **Rule of three.** Two occurrences can wait. At the third, extract in the same change, not "later":
  the component into the shared UI layer, the logic into `packages/shared`.
- **Reuse across the boundary, not through it.** `web` must not import from `api` (or the reverse) to
  reuse a function. If both sides need it, it moves to `packages/shared`; if it can't move, it wasn't
  shareable.
- **Don't reuse coincidences.** Two things that look alike today but answer to different owners (an
  invoice line and a cart line) are not one thing — coupling them under one abstraction costs more
  than the duplicate. Reuse what shares a *reason to change*, not a shape.
- **Extraction includes the deletion.** Migrate the call sites and remove the old copies in the same
  PR. An abstraction that lands *next to* the copies it was meant to replace made things worse.
- **A deliberate duplicate is one sentence in the PR.** Say why the shared version didn't fit. The
  rule is not "never duplicate", it is "never duplicate by accident".

Dependencies count as existing code: before hand-rolling a date parser, a slug helper or a retry
loop, check whether something already in `package.json` does it — but **don't add a dependency** to
avoid writing ten lines (see *Working rules*).

---

## Working rules

- **Heavy or parallel jobs run inside a memory cgroup** — never launch a suite, build or
  fan-out on a bare estimate; wrap it in
  `systemd-run --user --scope -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- <command>`
  and cap the tool's own concurrency too.
- **Use superpowers skills whenever they apply** — invoke via `Skill` before acting; process skills
  before implementation skills.
- **Don't install packages without asking** — the stack is intentional. Exception: obvious test devDeps.
- **Reuse before you write** — search for the existing component/helper/type before creating one,
  extend it instead of cloning it, and extract at the third copy (shared UI in
  `<apps/web/components/ui>`, shared logic and contracts in `packages/shared`). A deliberate duplicate
  is a sentence in the PR, not a default. See
  [Reuse first — search before you write](#reuse-first--search-before-you-write).
- **TDD by default** for new logic. Don't merge logic without tests.
- **Every user-facing flow ships with a Playwright E2E** that drives the running app against the real
  API. Unit tests green ≠ it works — the recurring failure mode is a feature that renders fine and
  then breaks on the first real click (missing endpoint, wrong payload, 500). Blocking on pre-push.
- **Instrument before you ablate, and budget the lap** — a pipeline that completes with non-empty
  output produced output; ask *where* it went, not why it's missing. More than three reproductions of
  a bug means you owe a shortcut script before the fourth. See
  [Debugging](#debugging--keep-the-loop-from-running-away).
- **A review finding is not a reproduction** — reproduce it before dispatching a fix, and believe the
  person who has it running over the person who read the diff. "I can't make it fail" is a reportable
  result, never something a green test papers over.
- **Dispatch the review of task N with the implementation of N+1** — review is read-only, so it is
  free in parallel and 10-15% of the wall clock in series. Discretionary decisions found along the
  way get batched and priced, not taken on your behalf. See
  [Agent orchestration](#agent-orchestration--parallel-where-its-free-batched-where-its-yours).
- **Don't lower the coverage gate** — exclude with justification instead.
- **No `any`** — `unknown` + type guards or domain types.
- **No hardcoded enum strings** — use the enums from `packages/shared`.
- **DB entities in `schema.prisma`** — single source. Migrations via `pnpm db:migrate` (don't hand-edit SQL).
- **DTOs/enums/Zod schemas in `packages/shared`** — never duplicate (except Prisma enums, sanctioned and
  guarded by an enum-parity test). Recompile `shared` after editing it, or api/web/seed import stale code.
- **Cache/heavy compute in services**, never in controllers or the frontend.
- **Email & storage via their transport/driver** — never provider-coupled; the API serves signed URLs,
  not binaries.
- **Keep this file's Stack/Architecture section current** — when you ship something previously marked
  "planned", update the Stack tables and module list in the same change. A stale `CLAUDE.md` misleads
  the next session.
- **UI work → design context first, then `impeccable` + superpowers** — for any UI/frontend change,
  invoke the `impeccable` skill (and its sub-skills: `shape`, `polish`, `critique`, etc.). First, if
  the project has no design context yet (`PRODUCT.md` / `DESIGN.md` at the root), run the impeccable
  `teach` flow (`$impeccable teach`) — it explores the codebase and then interviews you about the
  project's direction and writes `PRODUCT.md` (strategic) + `DESIGN.md` (visual) (auto-migrating a
  legacy `.impeccable.md` to `PRODUCT.md`). **Never hand-author the design context — `teach` gets it
  from you, not from the AI guessing.** Don't hand-roll UI without impeccable + superpowers.
- **Commits in English**, Conventional Commits. Scope = module/folder.
- **<Add project-specific rules here>**

## Git & GitHub

- **Commits and branches OK** — create commits and new branches whenever it makes sense, without asking first.
- **Never push** *(default)* — no `git push` under any circumstance, and absolutely never
  `git push --force` / `--force-with-lease`. Leave pushing to the user. **Exception:** when
  **"modo desatendido"** is active, you may push the feature branches you create (never `main`/protected
  branches, never force) so PRs are ready for review.
- **Never merge — no permission** — you do NOT have permission to merge anything into any branch, nor to
  merge any pull request. No `git merge`, no fast-forward integration, no `gh pr merge`. This holds in
  every mode, **including "modo desatendido"**. Leave every merge (branches and PRs alike) to the user.
- **GitHub via `gh`** — if the `gh` CLI is available, you may open pull requests, issues, and similar
  (comments, labels, etc.). These don't require pushing on your part beyond what `gh` itself does for an
  already-pushed branch.
- **Branches:** `feat/name`, `fix/description`, `chore/task`.
- **Every PR must include a manual test plan** — when opening a PR, add a **How to test manually**
  section describing the exact steps to exercise the change by hand. For a web page/UI, list the concrete
  routes/URLs to visit (e.g. `/dashboard/settings`), what to click or input, and the expected result.
  Include any setup (seed data, env vars, feature flags, login/role) and, where relevant, edge cases and
  error states to check.
