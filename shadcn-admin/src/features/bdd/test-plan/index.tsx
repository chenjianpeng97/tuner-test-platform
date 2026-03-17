import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ConfigDrawer } from '@/components/config-drawer'
import { ProfileDropdown } from '@/components/profile-dropdown'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

const scenarios = [
  { name: 'Login success', status: 'pass', feature: 'auth.feature' },
  { name: 'Login failure', status: 'fail', feature: 'auth.feature' },
  { name: 'Reset password', status: 'not_run', feature: 'account.feature' },
  { name: 'Update avatar', status: 'blocked', feature: 'profile.feature' },
]

function StatusBadge({ status }: { status: string }) {
  if (status === 'pass') return <Badge>pass</Badge>
  if (status === 'fail') return <Badge variant='destructive'>fail</Badge>
  if (status === 'blocked') return <Badge variant='secondary'>blocked</Badge>
  if (status === 'skip') return <Badge variant='outline'>skip</Badge>
  return <Badge variant='outline'>not_run</Badge>
}

export function TestPlanPage() {
  return (
    <>
      <Header fixed>
        <Search />
        <div className='ms-auto flex items-center space-x-4'>
          <ThemeSwitch />
          <ConfigDrawer />
          <ProfileDropdown />
        </div>
      </Header>

      <Main className='flex flex-1 flex-col gap-6'>
        <div className='flex flex-wrap items-end justify-between gap-4'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Test Plan</h2>
            <p className='text-muted-foreground'>Plan, update, and sync scenarios.</p>
          </div>
          <div className='flex items-center gap-2'>
            <Input className='w-56' placeholder='Filter scenarios' />
            <Button variant='outline'>Sync from TestRun</Button>
            <Button>New Plan</Button>
          </div>
        </div>

        <div className='grid gap-4 lg:grid-cols-[2fr_1fr]'>
          <Card>
            <CardHeader>
              <CardTitle>Plan Items</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Scenario</TableHead>
                    <TableHead>Feature</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className='text-right'>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scenarios.map((scenario) => (
                    <TableRow key={scenario.name}>
                      <TableCell>{scenario.name}</TableCell>
                      <TableCell>{scenario.feature}</TableCell>
                      <TableCell>
                        <StatusBadge status={scenario.status} />
                      </TableCell>
                      <TableCell className='text-right'>
                        <Button variant='outline' size='sm'>
                          Update
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Progress</CardTitle>
            </CardHeader>
            <CardContent className='space-y-4'>
              <div className='rounded-lg border p-3 text-sm'>
                <div className='font-medium'>Total scenarios</div>
                <div className='text-muted-foreground'>24</div>
              </div>
              <div className='grid gap-2 text-sm'>
                <div className='flex items-center justify-between'>
                  <span className='text-muted-foreground'>Pass</span>
                  <span className='font-medium'>12</span>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-muted-foreground'>Fail</span>
                  <span className='font-medium'>2</span>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-muted-foreground'>Blocked</span>
                  <span className='font-medium'>3</span>
                </div>
                <div className='flex items-center justify-between'>
                  <span className='text-muted-foreground'>Not run</span>
                  <span className='font-medium'>7</span>
                </div>
              </div>
              <Button variant='outline'>Add Scenarios</Button>
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
