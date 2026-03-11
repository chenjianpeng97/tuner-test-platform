import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from '@tanstack/react-router'
import { Loader2, LogIn } from 'lucide-react'
import { toast } from 'sonner'
import { useLoginApiV1AccountLoginPost } from '@/api/generated/account/account'
import { getCurrentUserApiV1UsersMeGet } from '@/api/generated/users/users'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { PasswordInput } from '@/components/password-input'

const formSchema = z.object({
  username: z
    .string()
    .min(1, 'Please enter your username'),
  password: z
    .string()
    .min(1, 'Please enter your password')
    .min(7, 'Password must be at least 7 characters long'),
})

interface UserAuthFormProps extends React.HTMLAttributes<HTMLFormElement> {
  redirectTo?: string
}

export function UserAuthForm({
  className,
  redirectTo,
  ...props
}: UserAuthFormProps) {
  const navigate = useNavigate()
  const { auth } = useAuthStore()
  const loginMutation = useLoginApiV1AccountLoginPost()

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  })

  async function onSubmit(data: z.infer<typeof formSchema>) {
    loginMutation.mutate(
      { data: { username: data.username, password: data.password } },
      {
        onSuccess: async () => {
          try {
            // Session cookie is set by server; fetch identity from /users/me
            const me = await getCurrentUserApiV1UsersMeGet()
            auth.setUser({
              id: me.id_,
              username: me.username,
              role: me.role,
              is_active: me.is_active,
            })
            const targetPath = redirectTo || '/'
            navigate({ to: targetPath, replace: true })
            toast.success(`Welcome back, ${me.username}!`)
          } catch {
            toast.error('Login succeeded but failed to fetch user profile.')
          }
        },
        onError: () => {
          toast.error('Invalid credentials. Please try again.')
        },
      }
    )
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className={cn('grid gap-3', className)}
        {...props}
      >
        <FormField
          control={form.control}
          name='username'
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input
                  placeholder='your-username'
                  autoComplete='username'
                  data-testid='auth-signin-username'
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name='password'
          render={({ field }) => (
            <FormItem className='relative'>
              <FormLabel>Password</FormLabel>
              <FormControl>
                <PasswordInput
                  placeholder='********'
                  autoComplete='current-password'
                  data-testid='auth-signin-password'
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button
          className='mt-2'
          disabled={loginMutation.isPending}
          data-testid='auth-signin-submit'
        >
          {loginMutation.isPending ? <Loader2 className='animate-spin' /> : <LogIn />}
          Sign in
        </Button>
      </form>
    </Form>
  )
}

