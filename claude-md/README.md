# claude-md — plantillas de `CLAUDE.md` y flujo de trabajo

Repo **meta / de plantillas**. Cura los `CLAUDE.md` (y docs compañeras) que se sincronizan
al resto de proyectos de Andrés. **Sin runtime, sin build, sin dependencias** — es un repo de
markdown. Editar aquí es editar las guías que otros repos heredan, así que la precisión y la
consistencia interna importan más de lo normal.

> Si buscas cómo trabajar **dentro de este repo**, lee [`CLAUDE.md`](CLAUDE.md). Este README
> es el índice de **qué ofrecen las plantillas** (modos + características) y cómo arrancar un
> proyecto nuevo con ellas.

---

## Archivos clave

| Archivo | Qué es |
| --- | --- |
| [`docs/starter-kit/CLAUDE.template.md`](docs/starter-kit/CLAUDE.template.md) | **Plantilla `CLAUDE.md` canónica única** (EN). Los proyectos la copian y rellenan los `<…>`. Por capas: **gobernanza** universal (verbatim) + un **preset de monorepo pnpm** (stack/módulos/deploy) marcado "reemplázame". Sirve para arrancar nuevo Y adaptar un repo existente. **Fuente de verdad** de la que se adaptan los demás. |
| [`docs/starter-kit/`](docs/starter-kit/) | Junto al `CLAUDE.template.md`, las otras dos plantillas "génesis" (ES): `DESIGN-SYSTEM.template.md` → `design-system.md`, `USER-STORIES.template.md` → `user-stories.md`. Su [`README.md`](docs/starter-kit/README.md) explica el bootstrap de cero a primer slice. Incluye además las plantillas compañeras que la plantilla canónica da por existentes: `FINDINGS.template.md` → `docs/FINDINGS.md` y `ENDPOINT_PERMISSIONS.template.md` → `docs/ENDPOINT_PERMISSIONS.md`. |
| [`docs/PROMPT_TEMPLATES_WEB.md`](docs/PROMPT_TEMPLATES_WEB.md) | Librería de prompts pegables por tarea (bootstrap, slice, página, endpoint, email, deploy, bug, **verificación de PR**). Su §0/§1 enlazan a `CLAUDE.template.md` en vez de re-pegar stack/reglas: una sola fuente de verdad. |

> Las plantillas llevan `<…>` placeholders a propósito: son los huecos a rellenar. No se
> "limpian". Solo los docs no-plantilla (este README, `CLAUDE.md`) van sin placeholders.
>
> **La gobernanza (superpowers, modos, TDD/cobertura, calidad, verificación de PR, Git & GitHub)
> vive una sola vez en `CLAUDE.template.md`.** Lo de abajo es un **resumen** para orientarte; el
> detalle canónico está en esa plantilla.

---

## Modos

Interruptor de comportamiento que se activa diciendo el nombre del modo. Se confirma
brevemente el cambio cuando ocurre.

| Modo | Qué hace | Límites |
| --- | --- | --- |
| **modo ligero** (`lite mode`) | Desactiva superpowers por completo: no se invoca ningún skill, ni siquiera el chequeo de si aplica, hasta decir "modo normal". | — |
| **modo normal** (`normal mode`, default) | Comportamiento estándar de superpowers. Además, al delegar programación: **≤ 1 agente a la vez** y **nunca modelo por encima de Sonnet** (nada de Opus). | Nunca push, nunca merge. |
| **modo desatendido** | Estás ausente y delegas autonomía: trabaja sin esperar confirmaciones y decide por su cuenta en vez de preguntar. **Puede `git push` de las ramas de feature que crea y abrir PRs con `gh`**, para dejar el trabajo listo para revisión. | Los límites duros **siguen**: nunca mergear (`git merge` / fast-forward / `gh pr merge`), nunca push a `main`/protegidas, nunca `--force`. Entrega ramas pusheadas + PRs; los mergeas tú. |

Vuelve a los defaults con **"modo normal"**.

---

## Características de las plantillas

Resumen de lo que un `CLAUDE.md` generado trae de serie. **El detalle canónico (verbatim) vive en
[`docs/starter-kit/CLAUDE.template.md`](docs/starter-kit/CLAUDE.template.md)** — esto es solo el índice:

- **Trabajos pesados dentro de un cgroup de memoria (OBLIGATORIO)** — suite completa, cobertura,
  mutation testing, build de producción, Playwright o cualquier fan-out va envuelto en
  `systemd-run --user --scope -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- <cmd>`, con el
  límite de concurrencia de la herramienta **además** del cgroup, nunca en su lugar. Un techo estimado
  no es un techo: una tanda de mutation testing pidió ~50 GB en una máquina de 31 GB y la tumbó, y de
  paso devolvió un score inflado (139 de 142 mutantes "timeout" = contados como matados).
- **graphify cada sesión** — grafo de conocimiento persistente (`graphify-out/`) para responder
  sobre arquitectura sin re-leer el repo.
- **superpowers siempre que aplique** — process skills antes que implementation skills. Flujo:
  `brainstorming → spec → writing-plans → plan → subagent-driven-development → finishing`. **Nada se
  implementa sin spec aprobado.** Skills refinan el *cómo*; nunca sobrescriben el `CLAUDE.md`.
- **TDD obligatorio para lógica nueva** (Red → Green → Refactor) + **hard rules** (nunca declarar
  hecho sin output de tests; endpoint/DTO/hook/schema nuevo lleva test; bug fix lleva regresión;
  nunca borrar/`.skip`/`.only` un test).
- **Gate de cobertura 80%** (crítico ≥ 90%); no se baja, se excluye infra con justificación.
- **E2E (Playwright) obligatorio y bloqueante** — todo flujo de usuario lleva un spec que conduce la
  app corriendo **contra la API real** (nada de mockear la red), y corre en el `pre-push`. Es el único
  gate que detecta lo implementado-pero-roto al primer clic: endpoint inexistente, payload mal,
  500 silencioso.
- **Calidad más allá de la cobertura** — mutation testing (Stryker/mutmut), property-based
  (fast-check/Hypothesis), validación runtime (Zod/Pydantic), tipos estrictos + SAST, E2E/smoke,
  auditoría de dependencias.
- **Stack pluggable, no acoplado a proveedor** — email por `MailTransport` y storage por
  `STORAGE_DRIVER` (`local`/`supabase`/`s3`), con S3 self-hosted (RustFS/MinIO) para paridad en dev.
- **Verificación agéntica de PRs** — agente headless (`claude -p`) que **conduce la app de punta a
  punta** y deja un veredicto en el PR (advisory, nunca mergea): Playwright MCP (web) + mobile-mcp
  (Compose). Orquestador pegable en [`docs/PROMPT_TEMPLATES_WEB.md`](docs/PROMPT_TEMPLATES_WEB.md) §9.
- **UI → contexto de diseño con `teach`, luego `impeccable`** — si no hay `PRODUCT.md` / `DESIGN.md`,
  `$impeccable teach` te entrevista y los escribe; nunca se escriben a mano.
- **Docs compañeras obligatorias** — `docs/FINDINGS.md` (gotchas no obvios, se lee antes de depurar y
  se escribe cuando algo cuesta tiempo) y `docs/ENDPOINT_PERMISSIONS.md` (permisos por endpoint,
  actualizado en el mismo cambio que toca el endpoint). Plantillas en
  [`docs/starter-kit/`](docs/starter-kit/).

---

## Reglas de Git & GitHub

Universales para todos los proyectos que heredan la plantilla (resumen; texto canónico en el bloque
**Git & GitHub** de [`CLAUDE.template.md`](docs/starter-kit/CLAUDE.template.md)):

- **Commits y ramas: libremente**, sin preguntar.
- **Nunca `git push`** *(default)* — tampoco `--force`. **Excepción:** en **modo desatendido**, ramas
  de feature (nunca `main`/protegidas, nunca force).
- **Nunca mergear — sin permiso** — ni `git merge`, ni fast-forward, ni `gh pr merge`, en **ningún
  modo** (incluido desatendido). Todo merge lo hace el desarrollador.
- **GitHub vía `gh`** sobre ramas ya pusheadas. **Todo PR lleva un plan de test manual**; la
  verificación agéntica lo complementa con un veredicto automático.

---

## Bootstrap de un proyecto nuevo

1. Copia las plantillas de [`docs/starter-kit/`](docs/starter-kit/) a la raíz del repo nuevo:
   `CLAUDE.template.md` → `CLAUDE.md`, `DESIGN-SYSTEM.template.md` → `design-system.md`,
   `USER-STORIES.template.md` → `user-stories.md`. Rellena los `<…>`.
2. Sigue el flujo de [`docs/starter-kit/README.md`](docs/starter-kit/README.md) (de cero a
   primer slice).
3. Usa los prompts de [`docs/PROMPT_TEMPLATES_WEB.md`](docs/PROMPT_TEMPLATES_WEB.md) por tarea.

Para **adaptar un proyecto ya existente**, parte de la misma
[`docs/starter-kit/CLAUDE.template.md`](docs/starter-kit/CLAUDE.template.md): conserva los bloques de
gobernanza, y **reemplaza o borra el preset de monorepo** (stack, estrategia de módulos, deploy) por
el stack real del repo. Rellena los `<…>`.
