# Teacher Workspace — rules for Claude Code

Source of truth: [docs/DETAIL_DESIGN.md](docs/DETAIL_DESIGN.md) (Vietnamese). Read it before changing
behaviour; section numbers (§) below refer to it. User-facing text (UI, error messages, docs) is Vietnamese.

## Layout

Single Laravel app at the repo root serves both the UI and the API (same origin, no proxy, no CORS).

- `app/`, `routes/api.php`, `config/` — Laravel API under `/api/v1` (no database in MVP).
- `resources/js/` — Vue 3 SPA (vue-router, pinia, axios) built by Vite via `laravel-vite-plugin`.
- `routes/web.php` + `resources/views/app.blade.php` — every non-`/api` path returns the SPA shell.
- `python/` — Excel engine. Coordinates in `python/config/template_profile.json`, subjects in `python/config/subject_config.json`.
- `python/tests/fixtures/` — the teacher's real sample workbooks: `lbg_mau.xlsx` (source, `MẪU` + TUẦN 1–9, TUẦN 7 has a day off) and `tuan8_lop_dich.xlsx` (target class, different timetable).
- `app/Auth/EnvUserProvider.php` — single account from `ADMIN_EMAIL` / `ADMIN_PASSWORD_HASH` (no DB). `php artisan admin:password` prints a hash.
- `app/Services/Timetable/` — `JobStore` (job dirs, meta.json, ownership, expiry, locking) and `PythonEngine` (runs the CLI, maps exit codes to `ApiException`).
- The `api` middleware group has cookies + session + CSRF prepended (`bootstrap/app.php`); all API errors use `{success:false,error:{code,message,details}}`.
- Laravel feature tests call the real Python engine with the fixtures; they need `python/.venv`.
- `resources/css/tokens.css` + `components.css`, `resources/js/components/ui/` — design system (docs/design-system.md).
- `resources/js/stores/sync.js` drives the 4-step wizard (§10.3 statuses); pure logic lives in `resources/js/utils/timetable.js` (tested in `tests/js/`).
- `Dockerfile`, `docker/`, `render.yaml` — single Render Free Docker service (Nginx + PHP-FPM + Python venv `/opt/venv`); deploy guide in `docs/deployment.md`.
- `docs/phase0/` — Phase 0 prototype and its outputs (reference only, not production code).

## Commands

```sh
php artisan test                                   # Laravel tests
python/.venv/bin/python -m pytest -q python        # Python tests
python/.venv/bin/python python/process_timetable.py check
npm test                                           # Vitest (tests/js)
npm run build                                      # Vue SPA compiles
php artisan serve & npm run dev                    # local dev at http://127.0.0.1:8000
```

## Rules

1. Read the whole design doc before coding; implement phase by phase; run all tests after each phase and report results.
2. Do not expand scope. No database, queue, Redis or microservice in the MVP unless asked.
3. Never hardcode Excel coordinates in code — use `template_profile.json`.
4. No AI for distributing lessons. Match by subject in row order (§4.6), never by source row position.
5. Read workbooks with openpyxl; **write by patching sheet XML in place** (§5.3). Never call `openpyxl` `save()` for output: it rewrites merged-cell styles and row heights in every sheet (proven in Phase 0).
6. Never create, delete or rename sheets; never modify sheet `MẪU`; never change styles; never copy styles from the source.
7. Never overwrite the uploaded source/target files; output is always a new file.
8. Allowed writes per week sheet: `A1`, `A3`, `A10`, `A17`, `A23`, `A29`, `E35`, `E3:E34`, `F3:F34`; column `D` only for the HĐTV/HĐTT interchangeable group (§4.10).
9. When unsure (count mismatch, day off, empty lesson, unknown subject): skip that subject for that week and report it — never guess (§4.7, §4.8).
10. Every skipped week/subject must carry an error code and concrete details (§9.7).
11. Python job commands write results to a JSON file in the job dir, logs to stderr, exit 0/1/2 (§8.3). stdout is not a result channel.
12. Never commit secrets (`.env`, `APP_KEY`, password hashes, API keys). Never put uploads/results in a public directory or serve them by URL.
13. Unit + integration tests are required. Do not mark work done without running them.
14. Ask when a requirement is unclear instead of assuming. Keep code readable; no abstraction for a single use.
15. Update README and docs at the end of each phase.
16. UI follows [docs/design-system.md](docs/design-system.md): colours only via semantic `--color-*` tokens from `resources/css/tokens.css` (no hex/rgb, no palette tokens in components); reuse `.btn`/`.card`/`.pill`/`.callout`/`.icon-tile` and `components/ui/` (`PageHeader`, `AppPanel`); icons from `lucide-vue-next`. Desktop browsers only — no phone layouts. `npm test` enforces the colour rules.
