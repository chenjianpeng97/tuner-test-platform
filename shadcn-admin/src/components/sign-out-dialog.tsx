import { useNavigate, useLocation } from '@tanstack/react-router'
import { useLogoutApiV1AccountLogoutDelete } from '@/api/generated/account/account'
import { useAuthStore } from '@/stores/auth-store'
import { ConfirmDialog } from '@/components/confirm-dialog'

interface SignOutDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SignOutDialog({ open, onOpenChange }: SignOutDialogProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { auth } = useAuthStore()
  const logoutMutation = useLogoutApiV1AccountLogoutDelete()

  const handleSignOut = () => {
    logoutMutation.mutate(undefined, {
      onSettled: () => {
        // Clear local auth state regardless of server response
        auth.reset()
        const currentPath = location.href
        navigate({
          to: '/sign-in',
          search: { redirect: currentPath },
          replace: true,
        })
      },
    })
  }

  return (
    <ConfirmDialog
      open={open}
      onOpenChange={onOpenChange}
      title='Sign out'
      desc='Are you sure you want to sign out? You will need to sign in again to access your account.'
      confirmText='Sign out'
      destructive
      handleConfirm={handleSignOut}
      className='sm:max-w-sm'
    />
  )
}
