import { useListUsersApiV1UsersGet } from '@/api/generated/users/users'
import type { User } from '../data/schema'

interface UseUserListParams {
    page: number
    pageSize: number
    /** Client-side role filter (not yet supported by backend query params) */
    roles?: string[]
    /** Client-side status filter */
    statuses?: string[]
}

interface UseUserListResult {
    users: User[]
    total: number
    isLoading: boolean
    isError: boolean
}

/**
 * Wraps the generated `useListUsersApiV1UsersGet` hook.
 * Converts page/pageSize → limit/offset for the backend API and
 * maps `UserQueryModel` → `User` (aligned with backend schema).
 */
export function useUserList({
    page,
    pageSize,
}: UseUserListParams): UseUserListResult {
    const limit = pageSize
    const offset = (page - 1) * pageSize

    const { data, isLoading, isError } = useListUsersApiV1UsersGet({
        limit,
        offset,
    })

    const users: User[] = (data?.users ?? []).map((u) => ({
        id: u.id_,
        username: u.username,
        role: u.role,
        /** Derive display status from is_active flag */
        status: u.is_active ? 'active' : 'inactive',
    }))

    return {
        users,
        total: data?.total ?? 0,
        isLoading,
        isError,
    }
}
