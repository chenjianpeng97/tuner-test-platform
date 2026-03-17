import { useMemo, useState } from 'react'
import { Link, useParams } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { AlertCircle, Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ConfigDrawer } from '@/components/config-drawer'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { getFeatureDetail, listProjectFeatures } from './api'

function CoverageBadge({ value }: { value: string }) {
  if (value === 'covered') return <Badge>covered</Badge>
  if (value === 'failed') return <Badge variant='destructive'>failed</Badge>
  return <Badge variant='secondary'>uncovered</Badge>
}

export function FeatureBrowserPage() {
  const { projectId } = useParams({ from: '/_authenticated/projects/$projectId/features/' })
  const [activeFeatureId, setActiveFeatureId] = useState<string | null>(null)
  const {
    data: features,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['projects', projectId, 'features'],
    queryFn: () => listProjectFeatures(projectId),
  })

  const { data: featureDetail } = useQuery({
    queryKey: ['projects', projectId, 'features', activeFeatureId],
    queryFn: () => getFeatureDetail(projectId, activeFeatureId ?? ''),
    enabled: Boolean(activeFeatureId),
  })

  const tree = useMemo(() => features ?? [], [features])
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
            <h2 className='text-2xl font-bold tracking-tight'>Feature Browser</h2>
            <p className='text-muted-foreground'>Browse scenarios and coverage.</p>
          </div>
          <div className='flex items-center gap-2'>
            <Input className='w-64' placeholder='Search features' />
            <Button variant='outline' disabled>
              New Feature
            </Button>
          </div>
        </div>

        {isError && (
          <div className='flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive'>
            <AlertCircle size={16} />
            <span>Failed to load features. Please try again later.</span>
          </div>
        )}

        {isLoading ? (
          <div className='flex flex-1 items-center justify-center py-16'>
            <Loader2 className='size-8 animate-spin text-muted-foreground' />
          </div>
        ) : (
          <div className='grid gap-4 lg:grid-cols-[2fr_1fr]'>
          <Card>
            <CardHeader>
              <CardTitle>Feature Tree</CardTitle>
            </CardHeader>
            <CardContent className='space-y-4'>
              {tree.map((feature) => (
                <div key={feature.id} className='space-y-3 rounded-lg border p-4'>
                  <div className='flex items-center justify-between'>
                    <button
                      type='button'
                      className='text-left'
                      onClick={() => setActiveFeatureId(feature.id)}
                    >
                      <div className='font-medium'>{feature.feature_name}</div>
                      <div className='text-xs text-muted-foreground'>
                        {feature.file_path}
                      </div>
                    </button>
                    <CoverageBadge value='uncovered' />
                  </div>
                  <div className='space-y-2 text-sm'>
                    {feature.scenarios?.map((scenario) => (
                      <div
                        key={scenario.id}
                        className='flex items-center justify-between rounded-md bg-muted/40 px-3 py-2'
                      >
                        <span>{scenario.name}</span>
                        <CoverageBadge value={scenario.coverage_status} />
                      </div>
                    ))}
                    {feature.rules?.map((rule) => (
                      <div key={rule.name} className='space-y-2'>
                        <div className='text-xs font-semibold text-muted-foreground'>
                          Rule: {rule.name}
                        </div>
                        {rule.scenarios.map((scenario) => (
                          <div
                            key={scenario.id}
                            className='flex items-center justify-between rounded-md bg-muted/40 px-3 py-2'
                          >
                            <span>{scenario.name}</span>
                            <CoverageBadge value={scenario.coverage_status} />
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                  {feature.children?.length ? (
                    <div className='space-y-2 border-l-2 border-muted pl-4'>
                      {feature.children.map((child) => (
                        <div key={child.id} className='space-y-2'>
                          <div className='flex items-center justify-between'>
                            <button
                              type='button'
                              className='text-left'
                              onClick={() => setActiveFeatureId(child.id)}
                            >
                              <div className='font-medium'>{child.feature_name}</div>
                              <div className='text-xs text-muted-foreground'>
                                {child.file_path}
                              </div>
                            </button>
                            <CoverageBadge value='uncovered' />
                          </div>
                          <div className='space-y-2 text-sm'>
                            {child.scenarios?.map((scenario) => (
                              <div
                                key={scenario.id}
                                className='flex items-center justify-between rounded-md bg-muted/40 px-3 py-2'
                              >
                                <span>{scenario.name}</span>
                                <CoverageBadge value={scenario.coverage_status} />
                              </div>
                            ))}
                            {child.rules?.map((rule) => (
                              <div key={rule.name} className='space-y-2'>
                                <div className='text-xs font-semibold text-muted-foreground'>
                                  Rule: {rule.name}
                                </div>
                                {rule.scenarios.map((scenario) => (
                                  <div
                                    key={scenario.id}
                                    className='flex items-center justify-between rounded-md bg-muted/40 px-3 py-2'
                                  >
                                    <span>{scenario.name}</span>
                                    <CoverageBadge value={scenario.coverage_status} />
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Preview</CardTitle>
            </CardHeader>
            <CardContent className='space-y-4 text-sm'>
              <div className='space-y-2'>
                <div className='font-medium'>
                  {featureDetail?.file_path ?? 'Select a feature'}
                </div>
                <div className='text-muted-foreground'>
                  {featureDetail ? featureDetail.feature_name : 'No feature selected'}
                </div>
              </div>
              <pre className='whitespace-pre-wrap rounded-lg border bg-muted/30 p-3 text-xs leading-relaxed'>
{featureDetail?.content ?? 'Choose a feature to preview its content.'}
              </pre>
              <Button asChild className='w-full'>
                <Link
                  to='/projects/$projectId/features/$featureId/edit'
                  params={{ projectId, featureId: featureDetail?.id ?? '' }}
                >
                  Open editor
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
        )}
      </Main>
    </>
  )
}
