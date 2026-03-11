/**
 * MSW browser worker initializer.
 *
 * Custom handlers are registered FIRST so they override the auto-generated
 * faker-based stubs for login, /users/me, logout, and user-list endpoints.
 * Generated handlers catch any remaining routes.
 */
import { setupWorker } from 'msw/browser'
import { getAccountMock } from '@/api/generated/account/account.msw'
import { getGeneralMock } from '@/api/generated/general/general.msw'
import { getUsersMock } from '@/api/generated/users/users.msw'
import { customHandlers } from './custom-handlers'

export const worker = setupWorker(
    // Custom handlers take precedence over generated stubs
    ...customHandlers,
    // Generated stubs cover all remaining endpoints
    ...getAccountMock(),
    ...getGeneralMock(),
    ...getUsersMock(),
)
