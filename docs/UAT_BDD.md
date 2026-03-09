# UAT BDD Flow

## Local Development

The local HTTP UAT flow assumes the backend service is started manually and that the UAT target does not own long-running processes.

1. Prepare the backend database and run migrations.

   `APP_ENV=local pnpm nx run app-api:bootstrap-local`

2. Start the backend service in a separate terminal.

   `APP_ENV=local pnpm nx run app-api:serve`

3. Optionally verify the service is reachable.

   `curl http://127.0.0.1:8000/api/v1/health`

4. Validate feature discovery and step binding without sending live requests.

   `pnpm nx run app-api:test-uat-dry-run`

5. Run the full HTTP UAT suite.

   `pnpm nx run app-api:test-uat`

6. Run the repository-level feature structure checks.

   `pnpm nx run ux-uat:check-features`

## CI Sequence

The first CI version should run the same flow in a single serial job.

1. Install workspace and backend dependencies.
2. Use the tracked backend CI config under `fastapi-clean-example/config/ci/` and generate the dotenv for `APP_ENV=ci`.
3. Start PostgreSQL.
4. Apply Alembic migrations.
5. Start the FastAPI service.
6. Poll `GET /api/v1/health` until it returns `200 OK`.
7. Run `pnpm nx run ux-uat:check-features`.
8. Run `pnpm nx run app-api:test-uat`.
9. Publish the JUnit XML files from `dist/test-results/app-api/uat/`.

## Notes

- `app-api:test-uat` always runs `behave --stage http`.
- `app-api:test-uat` writes JUnit XML output under `dist/test-results/app-api/uat/`.
- GitHub Actions should use `APP_ENV=ci`, not the gitignored `local` config.
- If the backend is exposed at a different host or port, set `BDD_BASE_URL` before running the UAT target.