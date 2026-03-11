/**
 * db-factory.ts — Node.js bridge to Python BDD factory for UI integration tests.
 *
 * In mock mode (VITE_MSW_ENABLED=true) MSW intercepts all API calls so seeding
 * is not needed.  Call `ensureIdentity` / `deleteIdentity` only in integration
 * mode (E2E_MODE=integration).
 *
 * Identity names and credentials MUST match `features/factories/identity_registry.py`.
 */

import { execSync } from 'child_process'
import * as path from 'path'

export type UserRole = 'super_admin' | 'admin' | 'user'

export interface SeededUser {
    id_: string
    username: string
    role: UserRole
    is_active: boolean
}

/** Absolute workspace root (where `features/` lives). */
const WORKSPACE_ROOT = path.resolve(__dirname, '../../..')

/**
 * Run a one-liner Python snippet inside the fastapi-clean-example venv.
 * Uses `uv run` so the correct virtual environment is activated automatically.
 */
function runPythonScript(script: string): string {
    return execSync(`uv run python -c "${script}"`, {
        cwd: path.join(WORKSPACE_ROOT, 'fastapi-clean-example'),
        env: { ...process.env, APP_ENV: 'local', PYTHONPATH: WORKSPACE_ROOT },
        encoding: 'utf-8',
    }).trim()
}

/**
 * Ensure the named BDD identity exists in the DB with specified attributes.
 * Mirrors the Behave "Given" step: "the shared identity X exists as role Y and is active/inactive".
 *
 * @returns metadata of the seeded user
 */
export function ensureIdentity(
    name: string,
    opts: { role?: UserRole; is_active?: boolean } = {}
): SeededUser {
    const roleArg = opts.role ? `role=${JSON.stringify(opts.role)}` : ''
    const activeArg = opts.is_active !== undefined ? `is_active=${opts.is_active}` : ''
    const kwargs = [roleArg, activeArg].filter(Boolean).join(', ')

    const script = [
        'import sys, json',
        `sys.path.insert(0, ${JSON.stringify(WORKSPACE_ROOT)})`,
        'from features.factories.seeding import ensure_identity',
        `result = ensure_identity(${JSON.stringify(name)}${kwargs ? ', ' + kwargs : ''})`,
        "print(json.dumps({'id_': result.id_, 'username': result.username, 'role': result.role.value, 'is_active': result.is_active}))",
    ].join('; ')

    const json = runPythonScript(script)
    return JSON.parse(json) as SeededUser
}

/**
 * Delete the named BDD identity from the DB.
 * Use in `afterEach` / `afterAll` cleanup for integration tests.
 */
export function deleteIdentity(name: string): void {
    const script = [
        'import sys',
        `sys.path.insert(0, ${JSON.stringify(WORKSPACE_ROOT)})`,
        'from features.factories.seeding import delete_identity',
        `delete_identity(${JSON.stringify(name)})`,
    ].join('; ')

    runPythonScript(script)
}
