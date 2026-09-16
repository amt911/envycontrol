# Prompt templates — arrancar / extender un proyecto en este estilo

Plantillas pegables para que un agente (Claude Code) construya **otro** proyecto con
el mismo stack, las mismas convenciones y el mismo flujo que SobreBox, o para añadir
páginas/features a este. Copia el bloque que necesites, rellena los `<…>` y pégalo.

> Orden mental: **stack + convenciones** (§0/§1, que ahora solo enlazan a
> `starter-kit/CLAUDE.template.md`) → **prompts** (§2–§9, qué pedir en cada tarea).
>
> **Para levantar un proyecto nuevo rápido**, no pegues stack/reglas a mano: usa el
> kit en [`starter-kit/`](starter-kit/README.md) — plantillas rellenables de los 3 docs
> génesis (`CLAUDE.md`, `design-system.md`, `user-stories.md`) que viven en el repo y el
> agente lee solas. Este archivo es la librería de prompts por tarea.

---

## 0. Stack canónico — vive en `CLAUDE.template.md`

El stack y la arquitectura **ya no se re-pegan aquí**: son las secciones **Module strategy** +
**Stack** + **Monorepo structure** de
[`starter-kit/CLAUDE.template.md`](starter-kit/CLAUDE.template.md). Lo ideal es que vivan como el
`CLAUDE.md` del repo (el agente lo lee solo cada sesión; por eso el starter-kit lo copia a la raíz).
Si un repo aún no tiene `CLAUDE.md`, pega esas secciones como contexto puntual.

> Redis/BullMQ, Passport/JWT y S3 están marcados *(si aplica)* en la plantilla — no los des por
> hechos si el proyecto no los usa. Email por `MailTransport` y storage por `STORAGE_DRIVER`
> (`local`/`supabase`/`s3`, con RustFS/MinIO en dev) son pluggable, nunca acoplados a un proveedor.

---

## 1. Convenciones de trabajo — viven en `CLAUDE.template.md`

Las reglas (superpowers + flujo, TDD + hard rules, cobertura 80%, reglas de código, tests, Git) son
las secciones **Tests and quality**, **Quality beyond coverage**, **Real-environment verification**,
**Working rules** y **Git & GitHub**
de [`starter-kit/CLAUDE.template.md`](starter-kit/CLAUDE.template.md). Mismo criterio que §0: viven en
el `CLAUDE.md` del repo; pégalas solo como contexto puntual si aún no existe.

---

## 2. Prompt — arrancar un proyecto nuevo desde cero

> Forma rápida: copia las plantillas de `starter-kit/` a la raíz del repo nuevo
> (`CLAUDE.md`, `design-system.md`, `user-stories.md`), rellénalas, y pega este prompt.
> El agente ya lee el stack/convenciones del `CLAUDE.md` del repo — no hace falta pegar nada más.

```text
Vamos a arrancar <NOMBRE_PROYECTO>: <una frase de qué hace y para quién>.

Ya están en el repo: CLAUDE.md (stack, módulos, reglas), design-system.md y
user-stories.md (backlog con prioridad MVP). Léelos. Si falta CLAUDE.md, cópialo de
docs/starter-kit/CLAUDE.template.md (ajusta el preset de monorepo a este stack).

Usa superpowers. Empieza por brainstorming para definir el alcance del PRIMER slice
(no todo el producto). Decomponer en épicas si es grande; brainstormear solo la primera.

Fase 0 (scaffolding) que quiero antes de cualquier feature:
- Monorepo pnpm + Turborepo con apps/api, apps/web, packages/shared.
- packages/shared compilando a dist/ con un enum y un schema Zod de ejemplo + su test.
- apps/api: NestJS 10 + Prisma 6 + Postgres, ZodValidationPipe, /health, PrismaModule @Global.
- apps/web: Next 15 App Router + shadcn + Tailwind v4 + TanStack Query provider.
- docker-compose con postgres, redis, mailpit. .env.example + scripts pnpm
  (infra:up/down, db:deploy/migrate/seed, build:shared, test, test:cov, test:e2e, pr-check,
  lint, type-check).
- Playwright configurado desde el día 1: playwright.config.ts con webServer (arranca api+web)
  y BD de test desechable, más un smoke spec que pruebe que la app arranca y un flujo real
  responde 2xx. No mockear la red en E2E.
- husky: pre-commit lint-staged, commit-msg commitlint, pre-push
  lint + type-check + test:all + test:e2e (el paso E2E es bloqueante).
- CI en GitHub Actions: lean (lint + type-check) + workflow de seguridad aparte
  (audit de dependencias bloqueante + SAST advisory). La suite pesada ya corrió en pre-push.
- Un CLAUDE.md que documente stack, estrategia de módulos y reglas (como el de SobreBox).

No escribas código hasta que yo apruebe el spec del scaffolding. Pásame el diseño primero.
```

---

## 3. Prompt — nuevo slice / feature (épica)

```text
Quiero el slice "<NOMBRE_SLICE>" de la épica <ÉPICA>.

Objetivo de usuario: <user story: como X quiero Y para Z>.
Alcance v1 (YAGNI): <qué entra>. Fuera de alcance (placeholders honestos): <qué se difiere>.
Datos: <entidades nuevas/cambios en schema.prisma, si los hay>.

Usa superpowers: brainstorming -> spec (lo reviso) -> writing-plans -> plan (lo reviso) ->
subagent-driven-development (implementer+reviewer frescos por tarea, review final con opus) ->
finishing-a-development-branch.

Recuerda: contratos (DTOs/enums/Zod) en packages/shared; lógica con TDD; gate 80%;
endpoints documentados en docs/ENDPOINT_PERMISSIONS.md en el mismo cambio; gotchas no
obvios en docs/FINDINGS.md. No pushees: cuando esté, lo pusheo yo y abrimos PR con gh.

El slice NO está terminado sin un spec E2E (Playwright) que conduzca el flujo en la app
corriendo contra la API real: la petición sale, responde 2xx, la UI refleja el cambio y
persiste tras recargar. Nada de mockear la red en E2E, y el spec falla si hay errores de
consola o 4xx/5xx inesperados. Localizadores por rol/label accesible.
```

---

## 4. Prompt — nueva página (frontend)

```text
Quiero la página <RUTA, ej. /coleccion/[slug]> : <qué muestra y qué hace el usuario>.

- App Router. RSC por defecto; "use client" solo donde haya estado/interacción.
- Server state con TanStack Query (hook + fetcher tipado en lib/api.ts que valida la
  respuesta con un schema de packages/shared). Client state con Zustand si hace falta.
- UI con shadcn (components/ui), Tailwind v4, tokens del design-system. No editar ui/ a mano.
- Estados: loading (skeleton), empty, error boundary. Responsive y accesible.
- Si necesita datos nuevos del backend, primero el endpoint + su DTO en shared (otra tarea).

TDD para hooks/lógica de la página (Vitest + Testing Library). Cambios visuales puros sin test.
Además, spec E2E (Playwright) del flujo principal de la página contra la API real: sin él la
página no cuenta como terminada (los unit tests no detectan que el botón llame a un endpoint
que no existe o devuelva 500).
Pásame el diseño antes de implementar si la página tiene lógica no trivial.
```

---

## 5. Prompt — nuevo endpoint (backend)

```text
Quiero el endpoint <MÉTODO /ruta> : <qué hace>.

- DTO de entrada y salida + schema Zod en packages/shared (recompilar shared).
- Validación con ZodValidationPipe. Permisos: <público / auth / rol>; documéntalo en
  docs/ENDPOINT_PERMISSIONS.md en el mismo cambio.
- Lógica en el service (no en el controller). Cache/cálculo pesado en su service dedicado.
- Si toca BD: cambio en schema.prisma + `pnpm db:migrate` (no editar SQL a mano).
- TDD: unit *.spec.ts del service + e2e supertest del endpoint. Gate 80% (crítico >=90%).
```

---

## 6. Prompt — email (transport switch)

```text
Quiero enviar el email "<para qué, ej. verificación / reset>".

- Usa la interface MailTransport existente; NO acoples a un proveedor.
- Dev: Mailpit/SMTP (sink local, ver en su UI). Prod: Resend. Selección por env MAIL_TRANSPORT.
- La plantilla y el envío van en un mail service; el caller solo pide "manda este email".
- Links del email usan la URL pública del front (env, no hardcodear localhost).
- Test: unit del service con el transport mockeado.
```

---

## 7. Prompt — deploy full-docker en Coolify

```text
Quiero desplegar en Coolify, full docker. Servicios que corren = un contenedor cada uno:
postgres (managed por Coolify), redis (managed), api (Dockerfile propio), web (Dockerfile propio).
packages/shared NO es contenedor: es librería, se compila DENTRO de las imágenes de api y web.

- Un Dockerfile por app (apps/api/Dockerfile, apps/web/Dockerfile), multi-stage con
  targets `dev` (bind-mount + pnpm dev, para compose local) y `prod` (imagen slim).
- prod api: pnpm install -> build:shared -> build api -> imagen runtime mínima;
  arranque corre `prisma migrate deploy` antes de levantar.
- prod web: Next output:'standalone'; copia .next/standalone + static.
- api interna (sin dominio público); web con dominio + proxy /api -> api por red interna.
- Local: docker-compose.yml con infra + api(dev) + web(dev), hot reload.
- Env por servicio en Coolify; secretos fuera del repo.

Usa superpowers (brainstorming -> spec -> plan). Pásame el diseño antes de tocar nada.
```

---

## 8. Prompt — arreglar un bug

```text
Bug: <síntoma exacto, pasos para reproducir, comportamiento esperado vs real, logs/error textual>.

Usa systematic-debugging: reproducir primero, encontrar la causa raíz (no parchear el
síntoma), test que falle que capture el bug, arreglar, ver verde. Si el arreglo es no
obvio, añade nota a docs/FINDINGS.md.
```

---

## 9. Verificación agéntica de PRs (web + móvil, local) — orquestador pegable

> Se dispara como **último paso del pipeline**, justo cuando el PR ya existe. Local con
> `claude -p` (headless), publica el veredicto con `gh pr comment`, **espera tu cierre y
> nunca mergea**. Dos motores bajo un orquestador: **Playwright MCP** (web) y **`maestro mcp`**
> (Compose nativo; `mobile-mcp` como alternativa si no está disponible). Ver las secciones
> "Verificación agéntica de PRs" y "Native Android (Jetpack Compose) — Maestro" del `CLAUDE.md`.
> Sustituye `@<scope>` y los `<…>` por lo tuyo. Úsalo contra un **emulador / device de test
> dedicado, nunca tu móvil de diario**.

`scripts/verify/verify-pr.sh` — detecta qué superficie tocó el PR y levanta lo que toque:

```bash
#!/usr/bin/env bash
set -euo pipefail
SURFACE="${1:-auto}"                                   # web | android | auto
PR="${2:-$(gh pr view --json number -q .number)}"
mkdir -p .verify

run_web() {
  pnpm infra:up && pnpm db:deploy && pnpm db:seed
  pnpm --filter @<scope>/api start:prod & API=$!
  pnpm --filter @<scope>/web start        & WEB=$!
  npx wait-on http://localhost:3000 http://localhost:3001/health -t 120000

  PR="$PR" claude -p "$(cat scripts/verify/prompt-web.md)" \
    --mcp-config .mcp/playwright.json \
    --allowedTools "mcp__playwright,Read,Grep,Glob,Write,Bash(gh pr comment:*),Bash(gh pr diff:*)" \
    --max-turns 40 --model claude-sonnet-5 \
    --output-format json | tee .verify/web.json
  kill $API $WEB 2>/dev/null || true
}

run_android() {
  # 1) Emulador headless
  "$ANDROID_HOME/emulator/emulator" -avd <avd_test> \
    -no-window -no-snapshot -no-boot-anim -gpu swiftshader_indirect & EMU=$!
  adb wait-for-device
  until [[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == 1 ]]; do sleep 2; done

  # 2) Backend en el host (el emulador lo alcanza por 10.0.2.2)
  pnpm infra:up && pnpm db:deploy && pnpm db:seed
  pnpm --filter @<scope>/api start:prod & API=$!
  npx wait-on http://localhost:3001/health -t 120000

  # 3) Build + install del APK del PR (flavor staging apuntando a 10.0.2.2)
  ./gradlew :app:<installTask, ej. installStagingDebug>

  PR="$PR" claude -p "$(cat scripts/verify/prompt-android.md)" \
    --mcp-config .mcp/mobile.json \
    --allowedTools "mcp__mobile-mcp,Read,Grep,Glob,Write,Bash(adb:*),Bash(gh pr comment:*),Bash(gh pr diff:*)" \
    --max-turns 50 --model claude-sonnet-5 \
    --output-format json | tee .verify/android.json
  kill $EMU $API 2>/dev/null || true
}

CHANGED="$(gh pr diff "$PR" --name-only || true)"
{ [[ "$SURFACE" == web ]]     || { [[ "$SURFACE" == auto ]] && grep -q '^apps/web/'     <<<"$CHANGED"; }; } && run_web
{ [[ "$SURFACE" == android ]] || { [[ "$SURFACE" == auto ]] && grep -q '^apps/android/' <<<"$CHANGED"; }; } && run_android
```

Los dos `.mcp/*.json`:

```json
// .mcp/playwright.json
{ "mcpServers": { "playwright": {
  "command": "npx",
  "args": ["-y", "@playwright/mcp@latest", "--headless", "--isolated", "--browser", "chromium"]
}}}
```

```json
// .mcp/mobile.json
{ "mcpServers": { "mobile-mcp": {
  "command": "npx", "args": ["-y", "@mobilenext/mobile-mcp@latest"],
  "env": { "MOBILEMCP_DISABLE_TELEMETRY": "1" }
}}}
```

Los dos prompts (`scripts/verify/prompt-web.md` y `prompt-android.md`) comparten el mismo
cuerpo `verify-pr.md`: leer el diff del PR (`gh pr diff`) y el bloque `## Casuísticas` de la
spec, conducir la app por cada caso, detectar huecos (botones que faltan, contenido sin
implementar, flujos muertos, pantallas off-spec), y terminar con
`gh pr comment $PR --body-file .verify/report.md`. **prompt-android.md** difiere en tres cosas:

- usa las tools de **`maestro mcp`** (lanza la app por `appId`, navega por el árbol de accesibilidad);
  antes de escribir nada, `maestro hierarchy --compact` para ver qué expone la pantalla de verdad;
- la URL de la API es `http://10.0.2.2:3001` (host visto desde el emulador);
- si un flujo solo está cubierto por unit, deja la regresión como **flow `.maestro/` commiteado**
  (y un test Espresso/Compose si la lógica lo pide), nunca un spec Playwright.

**Desatendido de verdad — permisos.** Para que `claude -p` no se pare pidiendo confirmación,
la vía segura es el `--allowedTools` acotado de arriba (con los patrones `Bash(...)` exactos
que necesita). Si aun así se detiene, existe `--dangerously-skip-permissions`, que salta todas
las confirmaciones — **solo en tu entorno local controlado, nunca por costumbre**. Confirma los
nombres de flags con `claude -p --help` por si tu versión cambió alguno.

**Dónde engancharlo.** NO en el pre-push de Lefthook/husky: arrancar emulador + navegador es
demasiado lento para un hook. Su sitio es el **último paso del pipeline de superpowers**, justo
después de `gh pr create` (en "modo desatendido" el agente abre el PR y dispara
`scripts/verify/verify-pr.sh auto`; en "modo normal" lo lanzas tú o se lo pides al agente).

**Dos capas (lo que hace fiable el veredicto).** Las casuísticas salen del bloque
`## Casuísticas` de la spec (`[web]` / `[android]` si un spec cubre ambas). La capa
determinista (specs Playwright en web, Espresso/Compose en Android) es el **gate duro de
merge**; la agéntica es **advisory** y, sobre todo, **genera los tests que faltan**. El
no-determinismo del agente es real: su valor es explorar lo nuevo y dejarte veredicto legible +
cobertura de regresión, **no vetar un merge por sí solo**.

---

## 10. Prompt — rollout del gate de mutación (60%), rama a rama

> Pegable **tal cual** en cualquier repo. Aplica lo que dice
> `CLAUDE.template.md` § *Mutation gate — the 60% floor, and it only goes up*: umbral **60%**
> sobre el scope de lógica de negocio, bloqueante en `pre-push`, reportado en CI (advisory al
> nacer). El prompt **mide antes de escribir el número** — un umbral inventado es una puerta
> que no se ha probado nunca.

```text
Objetivo: dejar este repo con el gate de mutación al 60% — escrito en su CLAUDE.md y cableado
de verdad en el hook de pre-push y en CI.

Paso 0 — aislamiento. Trabaja en un worktree nuevo (rama chore/mutation-gate-60) para no tocar
mi checkout. No pushees y no mergees nada: te quedas en commits locales.

Paso 1 — clasifica el repo antes de tocar nada, y dilo en voz alta:
  A) tiene lógica ejecutable + suite de tests  -> se cabla el gate;
  B) tiene lógica pero no suite todavía        -> se escribe la regla y se marca "pendiente,
     bloqueado por: no hay suite"; NO metas un paso al hook que hoy rompería el push;
  C) no aplica (repo de docs, PKGBUILD/empaquetado, decompilación byte-matching, fuentes
     generadas) -> una línea en CLAUDE.md diciendo por qué no aplica, y paras ahí.

Paso 2 — mide el baseline REAL antes de escribir ningún número. Elige herramienta por stack
(Stryker en JS/TS, PITest en Kotlin/JVM, mutmut en Python, cargo-mutants en Rust) y acota el
scope a la lógica de negocio (domain/, services/, módulos de cálculo puro), NO al árbol entero:
los repositorios, DAOs y la capa de vista diluyen el score hasta volverlo inútil como puerta.
La corrida va SIEMPRE dentro del cgroup de memoria y con los workers capados
(systemd-run --user --scope -p MemoryHigh=5G -p MemoryMax=6G -p MemorySwapMax=0 -- <cmd>).
Reporta el score partido en KILLED / SURVIVED / NO_COVERAGE: el porcentaje de portada los
mezcla y no significa nada.

Paso 3 — fija el umbral como trinquete: score real redondeado hacia abajo, nunca por debajo de
60. Si el score de hoy ya está por encima de 60, el umbral es ese, no 60. Si está por debajo,
el gate entra ADVISORY (informa, no falla) con el score y la fecha escritos al lado, y dejas
anotado que la deuda es llegar a 60.

Paso 4 — cabla:
  - pre-push: paso de mutación como ÚLTIMO paso (es el más lento), bloqueante, con el umbral
    del paso 3 y mensaje de error que diga qué significa un mutante vivo (código cubierto pero
    sin verificar) y dónde está el informe. Bypass documentado: --no-verify.
  - CI: workflow separado (mutation.yml), solo en PRs contra la rama por defecto — es
    demasiado caro para cada push de rama. Sube el informe HTML como artifact. Nace con
    continue-on-error: true; se promueve a bloqueante cuando el score haya superado el umbral
    en dos runs seguidos.

Paso 5 — CLAUDE.md del repo: añade la regla en la sección de tests/calidad y en la de CI &
hooks, con el número real, el scope y el estado (bloqueante o advisory + fecha). Si el repo ya
tiene una sección "Quality beyond coverage", la regla va ahí; no dupliques.

Paso 6 — resto de ramas vivas. Lístalas con:
    git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:short)' refs/heads
Descarta las ya mergeadas en la
rama por defecto y las que lleven >6 meses sin commits, y dime cuáles descartas. Sobre cada
rama viva restante, aplica el MISMO cambio (cherry-pick del commit de docs y, si la rama toca
el hook o el workflow, resuelve el conflicto a favor del gate). Una rama por commit; nada de
un commit gigante.

Paso 7 — verifica antes de cantar victoria: enseña la salida real del gate fallando (baja el
umbral a mano un momento, comprueba que el hook tumba el push, y restáuralo) — una puerta que
nunca ha fallado no está probada. Luego commit por rama, sin push y sin merge, y me dices qué
quedó bloqueante, qué quedó advisory y qué repo/rama quedó fuera y por qué.

Reglas duras: no bajes el umbral para que pase un push (es exactamente lo que la puerta
impide); no amplíes el scope para inflar el número; no metas la mutación en el mismo workflow
que el CI barato.
```

---

## 11. Prompt — rollout de la regla "Reuse first", repo a repo

> Pegable **tal cual** en cualquier repo. Aplica lo que dice `CLAUDE.template.md`
> § *Reuse first — search before you write*. El prompt **mide la duplicación real antes de
> escribir la regla**: una regla que no nombra las rutas de ese repo es decoración, y el agente
> siguiente la ignora.

```text
Objetivo: dejar este repo con la regla de reutilización escrita en su CLAUDE.md, apuntando a los
sitios REALES donde vive lo reutilizable aquí — no a un ejemplo genérico.

Paso 0 — aislamiento. Trabaja en un worktree nuevo (rama docs/reuse-first) para no tocar mi
checkout. No pushees y no mergees nada: te quedas en commits locales.

Paso 1 — di en voz alta dónde vive lo reutilizable en ESTE repo antes de escribir nada:
paquete compartido (packages/shared), capa de UI (components/ui, theme/ de Compose), utilidades
(lib/, utils/), funciones sourceadas (lib/*.sh), macros/headers, fixtures de test. Si no existe
ningún sitio para lo compartido, ese es el hallazgo: dilo y propón cuál sería, no lo inventes
dentro de la regla.

Paso 2 — inventario de duplicación real, antes de la prosa. Busca las tres formas que aparecen
siempre: (a) componentes casi iguales, (b) helpers repetidos con otro nombre, (c) constantes,
strings y tipos duplicados entre módulos. Vale ripgrep por comportamiento, no solo por nombre
(rg -n "format.*price|slugify|retry"), y jscpd si el repo es JS/TS. Reporta el top 5 con rutas y
número de copias. Las corridas pesadas van dentro del cgroup de memoria.

Paso 3 — escribe la regla en CLAUDE.md, en la sección de reglas de trabajo del repo (Working
rules / Reglas de trabajo), con: buscar antes de escribir, extender en vez de clonar, regla de
tres, y las RUTAS del paso 1. Si el repo ya tiene una sección de calidad o de convenciones donde
encaja mejor, va ahí; no dupliques la regla en dos sitios.

Paso 4 — no refactorices el inventario entero en el mismo PR. La regla primero. Como mucho, el
duplicado nº1 del paso 2 si es barato — y entonces completo: extraer, migrar TODOS los call
sites y borrar las copias en el mismo commit. Una abstracción que aterriza al lado de las copias
que iba a sustituir ha empeorado el repo.

Paso 5 — verifica antes de cantar victoria: cada ruta que cita la regla tiene que existir
(compruébalo con ls), y los enlaces internos del CLAUDE.md tienen que seguir resolviendo.
Una regla que apunta a una carpeta que no existe es peor que no tener regla.

Paso 6 — resto de ramas vivas. Lístalas con:
    git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:short)' refs/heads
Descarta las ya mergeadas en la rama por defecto y las que lleven >6 meses sin commits, y dime
cuáles descartas. Sobre cada rama viva restante, aplica el MISMO cambio (cherry-pick del commit
de docs). Una rama por commit.

Reglas duras: no crees una abstracción para dos casos (la regla de tres es el umbral); no unifiques
coincidencias — dos cosas que hoy se parecen pero cambian por razones distintas siguen siendo dos;
no añadas una dependencia para ahorrarte diez líneas; y no borres una copia sin migrar antes sus
call sites.
```

---

## 12. Prompt — rollout de "Depuración" + "Orquestación de agentes", repo a repo

> Pegable **tal cual**. Aplica `CLAUDE.template.md` § *Debugging — keep the loop from running away*
> y § *Agent orchestration*. Igual que el §11, **el prompt mide antes de escribir**: las dos
> secciones están llenas de huecos que solo valen algo con los números de ESTE repo. Una regla sin
> coste medido detrás se borra en la primera limpieza.

```text
Objetivo: dejar este repo con las secciones de depuración y de orquestación de agentes en su
CLAUDE.md, instanciadas con lo que es cierto AQUÍ — no con el ejemplo de la plantilla.

Paso 0 — aislamiento. Worktree nuevo (rama chore/debugging-and-agent-orchestration) para no tocar
mi checkout. No pushees y no mergees nada: commits locales y me lo dejas para revisar.

Paso 0.5 — busca antes de escribir, y aquí eso incluye las RAMAS. Antes de redactar nada:
    git branch --format='%(refname:short)' | grep -Ei 'reuse|mutation|docs/'
    grep -niE 'reuse before you write|reutiliza antes|mutation|cgroup|lite mode' CLAUDE.md
Un rollout anterior puede vivir en una rama sin mergear (docs/reuse-first, chore/mutation-gate-60) o
como un bullet dentro de "Working rules" en vez de como sección — buscar solo el título de la sección
da un falso negativo y acabas escribiendo una segunda copia, peor y en conflicto con la primera. Si
la regla ya existe en cualquiera de las dos formas: NO la reescribas. Dime en qué rama está y sigue.

Paso 1 — el ciclo, con segundos reales. Cronometra una vuelta de
build -> desplegar/instalar -> llegar al estado -> observar, con los comandos de este repo.
Si alguna fase no existe (una librería no se despliega), dilo y bórrala de la tabla en vez de
inventarle un número. Rellena la tabla del ciclo con los segundos medidos. La fase dominante es la
única que se optimiza; las otras tres son ruido.

Paso 2 — el recurso exclusivo. Nombra qué cosa aquí solo puede tener un agente a la vez:
emulador, base de datos de dev, puerto del dev server, dispositivo físico, un lock de gradle/cargo.
Si no hay ninguno, dilo — entonces todo paraleliza y el hueco se rellena con "ninguno".

Paso 3 — aserciones inertes. Rompe UNA aserción a propósito y corre la suite: lo que siga en verde
es inerte. Después repasa la tabla de "Tests that cannot fail", borra las filas que este stack no
puede producir y nombra el mecanismo concreto de las que sí (asserts desactivados en runtime,
promesas/corrutinas sin esperar, snapshots que se autoescriben, mocks permisivos por defecto,
expectativa calculada con la misma expresión que el código). Corridas pesadas, dentro del cgroup.

Paso 4 — escribe las dos secciones en el CLAUDE.md del repo, con los resultados de los pasos 1-3
en los huecos. Los números que NO hayas medido se quedan como <!-- pendiente de medir -->: no
copies los de la plantilla, son de otro proyecto. Si el repo no tiene código ejecutable
(empaquetado, fuentes, decompilación byte a byte), no metas las secciones: escribe la exención en
una línea con su motivo, igual que hace el gate de mutación. Una exención escrita no se re-discute
cada trimestre; una no escrita, sí.

Paso 5 — el atajo de reproducción. Si el paso 1 dice que "llegar al estado" domina, escribe el
script (scripts/repro-<bug>.sh o el equivalente del stack), déjalo ejecutable y nómbralo en
docs/FINDINGS.md. Si no domina, no lo escribas: sería código muerto desde el día uno.

Paso 6 — docs/FACTS.md. Créalo desde FACTS.template.md si el repo despacha agentes, y siémbralo con
lo que ya hayas verificado en los pasos 1-3 (comandos que funcionan aquí, selectores reales, qué
fake existe). Cada línea lleva cómo se verificó. Si nunca se despachan agentes en este repo, no lo
crees.

Paso 7 — verifica antes de cantar victoria: los enlaces internos del CLAUDE.md resuelven, las rutas
citadas existen (ls), y ningún <…> de plantilla se ha quedado suelto donde debería haber un valor.
Enséñame la salida de los comandos que hayas cronometrado, no un resumen.

Paso 8 — resto de ramas vivas, igual que el §11: lístalas, descarta mergeadas y >6 meses, y
cherry-pickea el commit de docs sobre cada rama viva restante. Una rama por commit.

Reglas duras: no inventes un número medido; no copies los tiempos de la plantilla; la excepción de
paralelismo es solo para el agente de revisión (que no escribe) — el tope de agentes de
implementación sigue siendo 1; y las decisiones discrecionales que aparezcan por el camino se
acumulan y se preguntan de una tanda, con su coste, en vez de tomarlas tú.
```

---

## Notas de uso

- Lo ideal: el stack + reglas viven en el `CLAUDE.md` del repo (el agente lo lee solo). §0/§1
  solo apuntan a las secciones de `CLAUDE.template.md`; pégalas como contexto puntual únicamente si
  el repo aún no tiene `CLAUDE.md`. Luego usa los prompts 2–9 según la tarea.
- Cambia `@<scope>/shared` por el scope real del paquete (aquí `@sobrebox/shared`).
- Todos los prompts asumen: **no implementar sin spec aprobado** y **nunca pushear** (lo
  haces tú). Son la espina del flujo; el resto es relleno por tarea.
