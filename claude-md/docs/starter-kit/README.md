# Starter kit — levantar proyectos rápido (mismo estilo que SobreBox)

Kit para arrancar un proyecto nuevo con el mismo stack, diseño y flujo que este repo,
sin re-decidir nada. La idea: **rellenas 3 documentos génesis**, los pones en el repo
nuevo, y le pasas al agente el prompt de bootstrap. El resto sale solo, épica a épica.

## Los 3 documentos génesis

Todo proyecto en este estilo nace de tres docs (más un CLAUDE.md operativo). Cópialos
de aquí, renómbralos quitando `.template`, y rellénalos:

| Plantilla                   | Va a                              | Qué define                                                      | Quién lo lee                  |
| --------------------------- | --------------------------------- | --------------------------------------------------------------- | ----------------------------- |
| `CLAUDE.template.md`        | `CLAUDE.md` (raíz del repo nuevo) | Plantilla canónica (EN): gobernanza + preset de monorepo        | El **agente**, cada sesión    |
| `DESIGN-SYSTEM.template.md` | `design-system.md` (raíz)         | Identidad visual: paleta, tipografía, componentes, motion, a11y | Agente al hacer UI            |
| `USER-STORIES.template.md`  | `user-stories.md` (raíz)          | Backlog: roles, épicas, user stories, prioridad MVP             | Tú + agente al definir slices |

> Por qué CLAUDE.md y no re-pegar el stack cada vez: lo que vive en `CLAUDE.md` el
> agente lo lee solo en cada sesión. Es la forma de no repetirte. Las plantillas de
> prompts sueltas (`../PROMPT_TEMPLATES_WEB.md`) son para tareas concretas, no para el stack.
>
> `CLAUDE.template.md` es la **plantilla `CLAUDE.md` canónica única** (en inglés): por capas,
> **gobernanza** universal (verbatim: superpowers, modos, TDD/cobertura, calidad, verificación en
> entorno real, depuración, orquestación de agentes, verificación de PR, reuse first, Git & GitHub) +
> un **preset de monorepo pnpm** (stack, estrategia de módulos, deploy) marcado
> "reemplázame". La misma plantilla sirve para **adaptar un repo existente**: conservas la
> gobernanza y cambias/borras el preset.

## Arquetipos

El preset horneado en `CLAUDE.template.md` es **monorepo pnpm + Turborepo + `packages/shared`
compilado** (Nest/Prisma/Next). No es el único:

- **Monorepo (este kit):** un repo, `apps/api` + `apps/web` + `packages/shared`, Prisma.
- **Polyrepo / submódulos:** un repo raíz con `docker-compose.yml` + `makefile` que orquesta
  backend y frontend como **git submodules** versionados aparte, TypeORM en vez de Prisma, sin
  `packages/shared`. Para este caso, conserva la gobernanza de `CLAUDE.template.md` y **reemplaza el
  preset** (estrategia de módulos, estructura, deploy) por el layout real.

Para desarrollo en paralelo con **git worktrees + Docker Compose** (puertos host vs internos,
`COMPOSE_PROJECT_NAME` por worktree, re-init de submódulos), documenta el patrón en un
`docs/PARALLEL_WORKTREES.md` del repo; complementa al skill `superpowers:using-git-worktrees` con la
mecánica específica de Compose.

## Flujo de bootstrap (de cero a primer slice)

```text
1. Crear repo nuevo + git init.
2. Copiar las 3 plantillas, quitar .template, rellenar los <…>.
   - CLAUDE.md: ajustar scope del paquete (@<scope>/shared), nombre, qué épicas hay.
   - design-system.md: paleta + tipografía + componentes clave del producto nuevo.
   - user-stories.md: roles + épicas + US con criterios de aceptación + tabla MVP.
3. Pegar al agente el prompt "arrancar proyecto nuevo" de ../PROMPT_TEMPLATES_WEB.md §2.
   El agente hace Fase 0 (scaffolding monorepo) vía superpowers, con spec que apruebas.
4. Por cada épica: prompt de slice (§3) -> brainstorming -> spec -> plan -> implementa.
```

Regla de oro (de CLAUDE.md): **nada se implementa sin spec aprobado por ti**, y **el
push lo haces tú** (el agente nunca pushea).

## Qué da "velocidad" aquí

- **Decisiones ya tomadas** (chat.md de este repo es la genealogía): Prisma sobre TypeORM,
  Zod sobre class-validator (compartible en `shared`), monorepo pnpm, shared compilado.
  No re-litigar; van pre-rellenadas en `CLAUDE.template.md`.
- **Diseño parametrizado**: cambias 6 colores base + 3 fuentes y el sistema entero se
  re-tematiza (tokens semánticos + shadcn vars derivan de ahí).
- **Backlog estructurado**: épicas con prioridad MVP -> el orden de slices es obvio.
- **Flujo fijo**: superpowers (brainstorming -> spec -> plan -> SDD -> finishing) + TDD +
  gate 80% + Conventional Commits. Igual en todos los proyectos.

## Archivos del kit

- `CLAUDE.template.md` — instrucciones operativas del repo (stack + módulos + reglas).
- `DESIGN-SYSTEM.template.md` — sistema de diseño rellenable.
- `USER-STORIES.template.md` — backlog rellenable.
- `FINDINGS.template.md` — bitácora de *gotchas* no obvios → `docs/FINDINGS.md`. `CLAUDE.template.md`
  § *Start here* obliga a leerla antes de depurar y a escribir en ella cuando algo cuesta tiempo y no
  se deduce del código.
- `FACTS.template.md` — memoria de trabajo compartida entre agentes → `docs/FACTS.md`. Hechos
  **verificados** contra el repo o el dispositivo (selectores reales, qué fake existe, qué acepta un
  helper) que si no cada agente nuevo redescubre. No es FINDINGS: aquí va lo que **sí** se deduce del
  código pero cuesta volver a mirar, y puede caducar con la rama.
- `ENDPOINT_PERMISSIONS.template.md` — tabla autoritativa de permisos por endpoint →
  `docs/ENDPOINT_PERMISSIONS.md`. Se actualiza **en el mismo cambio** que toca un endpoint.
- `../PROMPT_TEMPLATES_WEB.md` — prompts pegables por tarea (arrancar, slice, página, endpoint, email, deploy, bug).
