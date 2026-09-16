# `claude-md/` migration audit

This document records how every source artifact from the temporary `claude-md/` template directory was adapted for EnvyControl before that directory was removed. It exists to make the migration auditable and to prevent generic web/monorepo rules from being silently lost or copied without adaptation.

## File-by-file migration

| Source template artifact | EnvyControl destination | Adaptation |
| --- | --- | --- |
| `claude-md/CLAUDE.md` | `CLAUDE.md`, `AGENTS.md` | Rewritten around a single Python CLI that mutates Linux system state. `AGENTS.md` is required to remain byte-for-byte identical. |
| `claude-md/README.md` | `README.md`, this audit, agent docs | Meta-template/bootstrap guidance is absorbed into the repository's Development section and canonical agent docs rather than replacing the upstream project README. |
| `claude-md/.markdownlint.jsonc` | `.markdownlint.jsonc` | Retained as root Markdown quality configuration. |
| `claude-md/.github/dependabot.yml` | `.github/dependabot.yml` | Adapted from generic package ecosystems to this repository's Python and GitHub Actions tooling. |
| `claude-md/.github/workflows/ci.yml` | `.github/workflows/ci.yml`, `mutation.yml`, `security.yml` | Expanded into Python test/coverage/type/lint, mutation, and security workflows with host-safe boundaries. |
| `claude-md/docs/PROMPT_TEMPLATES_WEB.md` | `docs/PROMPT_TEMPLATES.md` | Rewritten from web/UI prompts to EnvyControl Python CLI, TDD, distro/initramfs, GPU-mode, debugging, mutation, PR-review, and disposable-VM workflows. |
| `claude-md/docs/starter-kit/CLAUDE.template.md` | `CLAUDE.md`, `AGENTS.md`, `docs/CLI_CONTRACT.md`, `docs/COMMAND_PERMISSIONS.md`, test/CI tooling | Universal governance/TDD/verification concepts retained; pnpm/Playwright/Maestro/web sections replaced with pytest/Hypothesis/mutmut/Linux CLI equivalents. |
| `claude-md/docs/starter-kit/DESIGN-SYSTEM.template.md` | `docs/CLI_CONTRACT.md` | Visual design-system concerns become the CLI's user-facing command, output, exit, compatibility, and safety contract. UI-specific design tooling is explicitly not applicable. |
| `claude-md/docs/starter-kit/ENDPOINT_PERMISSIONS.template.md` | `docs/COMMAND_PERMISSIONS.md` | HTTP endpoint/role matrix becomes an authoritative map of privileged commands, filesystem writes/deletes, service changes, hardware probes, and initramfs effects. |
| `claude-md/docs/starter-kit/FACTS.template.md` | `docs/FACTS.md` | Instantiated as verified project memory with evidence and dated verification state. |
| `claude-md/docs/starter-kit/FINDINGS.template.md` | `docs/FINDINGS.md` | Instantiated for non-obvious debugging discoveries, infrastructure gotchas, and reusable lessons. |
| `claude-md/docs/starter-kit/README.md` | `README.md` Development section plus canonical docs | Starter-kit setup instructions become repo-specific development commands and links; generic bootstrap prose is not kept as a second README. |
| `claude-md/docs/starter-kit/USER-STORIES.template.md` | `docs/USER_STORIES.md` | Rewritten around EnvyControl users, maintainers, distro support, safe switching/reset/cache behavior, and verification needs. |

## Cross-cutting template concepts retained

The migration also implements concepts that were described inside templates even when the template repository did not contain a one-to-one executable file for them:

- mandatory RED -> GREEN -> REFACTOR for behavior changes and regression-first bug fixes;
- characterization tests before touching legacy behavior;
- host-safe normal tests using fakes/`tmp_path` instead of real `/etc`, `/usr`, `/lib`, `/var/cache/envycontrol`, systemd, GPU probes, or initramfs commands;
- pytest branch coverage with an 80% blocking floor and no threshold lowering;
- Hypothesis property tests where invariants are useful;
- mutmut execution inside a 6 GB memory cgroup, with an absolute 60% promotion floor and conservative scoring that never counts timeouts as kills;
- Ruff, mypy, dependency/security scanning, dead-code review, pre-commit and pre-push gates;
- a reusable safe CLI smoke verifier and a PR-verification orchestrator;
- destructive system verification only inside a disposable VM protected by three independent gates and with no force-host bypass;
- agentic PR review and evidence-based completion rather than self-attestation;
- one implementation owner at a time, reuse-first investigation, factual project memory, and explicit documentation of unresolved uncertainty;
- no automatic merge of the PR.

## Deliberately non-applicable concepts

The original templates contain web/mobile-specific concepts such as visual design systems, browser E2E, Playwright, Maestro, endpoint authorization, pnpm workspace commands, and UI-oriented tools. They are not copied as inert boilerplate. Their underlying intent is represented by CLI contract tests, system-boundary permissions, subprocess/filesystem fakes, and disposable-VM system verification instead.

Once this audit and all destination files are present, the `claude-md/` directory is redundant and must be deleted so agents have one canonical rule set rather than conflicting template copies.
