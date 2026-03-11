/**
 * Custom MSW handlers that override the auto-generated ones with richer,
 * more realistic mock data and proper session cookie simulation.
 *
 * Import order matters: these handlers are placed BEFORE the generated ones
 * in the `handlers` array so they take priority.
 *
 * ⚠️  Do NOT hardcode user data here.
 *    Edit features/fixtures/fixtures.toml, then run:
 *      pnpm exec nx run ux-uat:gen-fixtures
 */
import { http, HttpResponse } from 'msw'
import type { CurrentUserResponse, ListUsersQM } from '@/api/generated/model'
import { ALL_FIXTURE_USERS, FIXTURE_USERS } from './__fixtures__.generated'

// In-memory session state (MSW service worker scope)
let currentSessionUser: CurrentUserResponse | null = null

// ─── Custom handlers ──────────────────────────────────────────────────────────
export const customHandlers = [
    // POST /api/v1/account/login
    http.post('*/api/v1/account/login', async ({ request }) => {
        const body = (await request.json()) as { username?: string; password?: string }
        const record = body.username ? FIXTURE_USERS[body.username] : undefined

        if (!record || record.password !== body.password) {
            return HttpResponse.json(
                { message: 'Invalid credentials' },
                { status: 401 }
            )
        }

        currentSessionUser = record.profile
        // The real backend sets an HTTP-only cookie; in MSW we just track state.
        return new HttpResponse(null, { status: 204 })
    }),

    // GET /api/v1/users/me
    http.get('*/api/v1/users/me', () => {
        if (!currentSessionUser) {
            return HttpResponse.json({ message: 'Not authenticated' }, { status: 401 })
        }
        return HttpResponse.json(currentSessionUser, { status: 200 })
    }),

    // DELETE /api/v1/account/logout
    http.delete('*/api/v1/account/logout', () => {
        currentSessionUser = null
        return new HttpResponse(null, { status: 204 })
    }),

    // GET /api/v1/users/  (list)
    http.get('*/api/v1/users/', ({ request }) => {
        const url = new URL(request.url)
        const roleFilter = url.searchParams.get('role')
        const page = parseInt(url.searchParams.get('page') ?? '1', 10)
        const pageSize = parseInt(url.searchParams.get('page_size') ?? '10', 10)

        const filtered = roleFilter
            ? ALL_FIXTURE_USERS.filter((u) => u.role === roleFilter)
            : ALL_FIXTURE_USERS

        const start = (page - 1) * pageSize
        const pagedUsers = filtered.slice(start, start + pageSize)

        const response: ListUsersQM = {
            users: pagedUsers,
            total: filtered.length,
        }

        return HttpResponse.json(response, { status: 200 })
    }),
]
