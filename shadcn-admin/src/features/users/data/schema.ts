import { z } from 'zod'

export const userStatusSchema = z.union([
  z.literal('active'),
  z.literal('inactive'),
  z.literal('invited'),
  z.literal('suspended'),
])
export type UserStatus = z.infer<typeof userStatusSchema>

export const userRoleSchema = z.union([
  z.literal('super_admin'),
  z.literal('admin'),
  z.literal('user'),
])
export type UserRole = z.infer<typeof userRoleSchema>

export const userSchema = z.object({
  id: z.string(),
  username: z.string(),
  role: userRoleSchema,
  /** Derived from backend is_active; extended by MSW for invited/suspended */
  status: userStatusSchema,
})
export type User = z.infer<typeof userSchema>

export const userListSchema = z.array(userSchema)
