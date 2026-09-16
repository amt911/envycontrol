# Endpoint permissions — <PROJECT>

> **Template.** Copy to `docs/ENDPOINT_PERMISSIONS.md` in the new repo and delete this quote block.
>
> `CLAUDE.template.md` § *Start here* declares this file the **authoritative endpoint-permissions
> reference**: keep it current **in the same change** that adds or modifies an endpoint. A stale
> table here is worse than no table — it's the document a reviewer trusts when deciding whether a
> route is safe to expose.

## Legend

| Access | Meaning |
| --- | --- |
| `public` | No token required. Reachable by anyone who can reach the host. |
| `auth` | Any authenticated user (valid access token). |
| `owner` | Authenticated **and** the resource belongs to the caller (ownership checked in the service, not only in the guard). |
| `role:<name>` | Authenticated and holding that role (`role:admin`, `role:staff`, …). |
| `internal` | Not reachable from the public edge — cron, queue worker, or service-to-service only. |

**Rate limit** = the throttler bucket applied, or `—` for the global default.

## Endpoints

Group by module, one table per module. Keep paths exactly as routed (including the global prefix
and any version segment).

### `<module>`

| Method | Path | Access | Guard / decorator | Notes |
| --- | --- | --- | --- | --- |
| `POST` | `/<prefix>/<resource>` | `auth` | `<JwtAuthGuard>` | <what it does; validation quirks> |
| `GET` | `/<prefix>/<resource>/:id` | `owner` | `<JwtAuthGuard>` + ownership check in service | 404 (not 403) when it isn't yours, so the ID space isn't enumerable |
| `DELETE` | `/<prefix>/<resource>/:id` | `role:admin` | `<RolesGuard('admin')>` | Soft delete — sets `deletedAt`, keeps the tombstone for delta sync |

### `<auth module>`

| Method | Path | Access | Guard / decorator | Notes |
| --- | --- | --- | --- | --- |
| `POST` | `/<prefix>/auth/login` | `public` | `<LocalAuthGuard>` | Throttled; never reveal whether the email exists |
| `POST` | `/<prefix>/auth/refresh` | `public` | — (validates the refresh token itself) | Rotates the refresh token |

## Invariants

- **Default-deny.** A new controller is authenticated unless it is *explicitly* marked public
  (`@Public()` / equivalent). Never make a route public by simply forgetting the guard.
- **Ownership is checked in the service.** A guard proves *who* you are, not *what* is yours.
- **Not-yours is a 404**, not a 403, wherever the ID space would otherwise be enumerable.
- **Every row here has a test.** An access level with no test asserting the rejection path is a
  claim, not a control.
