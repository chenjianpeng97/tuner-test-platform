import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ConfigDrawer } from '@/components/config-drawer'
import { ProfileDropdown } from '@/components/profile-dropdown'

const suggestions = [
  'Given user exists',
  'When user logs in',
  'Then dashboard loads',
  'And audit log is created',
]

export function FeatureEditorPage() {
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
            <h2 className='text-2xl font-bold tracking-tight'>Feature Editor</h2>
            <p className='text-muted-foreground'>Edit and commit Gherkin files.</p>
          </div>
          <div className='flex items-center gap-2'>
            <Input className='w-64' placeholder='Commit message' />
            <Button>Save & Commit</Button>
          </div>
        </div>

        <div className='grid gap-4 lg:grid-cols-[2fr_1fr]'>
          <Card className='min-h-[420px]'>
            <CardHeader>
              <CardTitle>auth.feature</CardTitle>
            </CardHeader>
            <CardContent className='space-y-4'>
              <Textarea
                rows={18}
                className='font-mono text-sm'
                defaultValue={`Feature: Authentication\n  Scenario: Login success\n    Given user exists\n    When user logs in\n    Then user sees dashboard\n\n  Scenario: Login failure\n    Given user exists\n    When user logs in with wrong password\n    Then user sees error`}
              />
              <div className='flex items-center justify-between text-sm text-muted-foreground'>
                <span>Auto-complete: 300ms debounce</span>
                <span>UTF-8 preserved</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Step Suggestions</CardTitle>
            </CardHeader>
            <CardContent className='space-y-3'>
              {suggestions.map((suggestion) => (
                <div
                  key={suggestion}
                  className='flex items-center justify-between rounded-lg border px-3 py-2 text-sm'
                >
                  <span>{suggestion}</span>
                  <Badge variant='secondary'>+ add</Badge>
                </div>
              ))}
              <div className='rounded-lg border border-dashed p-3 text-xs text-muted-foreground'>
                Suggestions update as you type in the editor.
              </div>
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
