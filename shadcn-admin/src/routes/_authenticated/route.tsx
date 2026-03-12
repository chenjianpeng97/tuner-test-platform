import { createFileRoute, redirect } from '@tanstack/react-router'
import { getCurrentUserApiV1UsersMeGet } from '@/api/generated/users/users'
import { AuthenticatedLayout } from '@/components/layout/authenticated-layout'
import { useAuthStore } from '@/stores/auth-store'

export const Route = createFileRoute('/_authenticated')({
  component: AuthenticatedLayout,
  beforeLoad: async ({ location }) => {
    const { auth } = useAuthStore.getState()
    if (!auth.user) {
      try {
        const me = await getCurrentUserApiV1UsersMeGet()
        auth.setUser({
          id: me.id_,
          username: me.username,
          role: me.role,
          is_active: me.is_active,
        })
      } catch {
        throw redirect({
          to: '/sign-in',
          search: { redirect: location.href },
        })
      }
    }
  },
})
