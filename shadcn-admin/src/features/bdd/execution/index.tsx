import { useMemo, useState } from 'react'
import { useParams } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
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
import { listProjectFeatures } from '../feature-browser/api'
import {
  createScenarioExecution,
  listTestPlanItems,
  listTestPlans,
  runAutoStep,
  triggerTestRun,
  updateManualStep,
  updateTestPlanItemStatus,
} from './api'

function StatusBadge({ status }: { status: string }) {
  if (status === 'pass') return <Badge>pass</Badge>
  if (status === 'fail') return <Badge variant='destructive'>fail</Badge>
  if (status === 'skip') return <Badge variant='outline'>skip</Badge>
  return <Badge variant='secondary'>pending</Badge>
}

export function ExecutionPage() {
  const { projectId } = useParams({ from: '/_authenticated/projects/$projectId/execution/' })
  const queryClient = useQueryClient()
  const [activePlanId, setActivePlanId] = useState<string | null>(null)
  const [activeExecution, setActiveExecution] = useState<{
    id: string
    scenarioId: string
  } | null>(null)

  const { data: plans, isLoading: isPlansLoading, isError: isPlansError } = useQuery({
    queryKey: ['projects', projectId, 'test-plans'],
    queryFn: () => listTestPlans(projectId),
  })

  const selectedPlanId = activePlanId ?? plans?.[0]?.id ?? null

  const { data: planItems } = useQuery({
    queryKey: ['projects', projectId, 'test-plans', selectedPlanId, 'items'],
    queryFn: () => listTestPlanItems(projectId, selectedPlanId ?? ''),
    enabled: Boolean(selectedPlanId),
  })

  const { data: featureTree } = useQuery({
    queryKey: ['projects', projectId, 'features'],
    queryFn: () => listProjectFeatures(projectId),
  })

  const scenarioNameMap = useMemo(() => {
    const map = new Map<string, string>()
    const walk = (nodes: typeof featureTree) => {
      nodes?.forEach((node) => {
        node.scenarios.forEach((scenario) => {
          map.set(scenario.id, scenario.name)
        })
        node.rules.forEach((rule) => {
          rule.scenarios.forEach((scenario) => {
            map.set(scenario.id, scenario.name)
          })
        })
        walk(node.children)
      })
    }
    walk(featureTree ?? [])
    return map
  }, [featureTree])

  const createExecutionMutation = useMutation({
    mutationFn: (payload: { scenario_id: string; test_plan_item_id?: string }) =>
      createScenarioExecution(projectId, payload),
    onSuccess: (execution) => {
      setActiveExecution({ id: execution.id, scenarioId: execution.scenario_id })
      setActiveExecutionDetails({
        id: execution.id,
        status: execution.status,
        steps: execution.steps.map((step) => ({
          id: step.id,
          keyword: step.keyword,
          text: step.text,
          status: step.status,
          execution_mode: step.execution_mode,
          available_stages: step.available_stages,
        })),
      })
      toast.success('Scenario execution created.')
    },
    onError: () => {
      toast.error('Failed to start scenario execution.')
    },
  })

  const updateItemMutation = useMutation({
    mutationFn: ({
      itemId,
      status,
    }: {
      itemId: string
      status: 'not_run' | 'pass' | 'fail' | 'skip' | 'blocked'
    }) =>
      updateTestPlanItemStatus(projectId, selectedPlanId ?? '', itemId, status),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'test-plans', selectedPlanId, 'items'],
      })
    },
    onError: () => {
      toast.error('Failed to update item.')
    },
  })

  const triggerRunMutation = useMutation({
    mutationFn: () =>
      triggerTestRun(projectId, { scope_type: 'project', scope_value: null }),
    onSuccess: () => {
      toast.success('Test run triggered.')
    },
    onError: () => {
      toast.error('Failed to trigger test run.')
    },
  })

  const runAutoMutation = useMutation({
    mutationFn: ({
      recordId,
      stageName,
      execId,
    }: {
      recordId: string
      stageName: string
      execId: string
    }) => runAutoStep(projectId, execId, recordId, stageName),
    onSuccess: () => {
      toast.success('Auto step executed.')
      refreshExecution()
    },
    onError: () => {
      toast.error('Failed to run auto step.')
    },
  })

  const manualStepMutation = useMutation({
    mutationFn: ({
      recordId,
      status,
      execId,
    }: {
      recordId: string
      status: 'pass' | 'fail' | 'skip'
      execId: string
    }) => updateManualStep(projectId, execId, recordId, status),
    onSuccess: () => {
      toast.success('Step status updated.')
      refreshExecution()
    },
    onError: () => {
      toast.error('Failed to update step.')
    },
  })

  const [activeExecutionDetails, setActiveExecutionDetails] = useState<{
    id: string
    status: string
    steps: Array<{
      id: string
      keyword: string
      text: string
      status: string
      execution_mode: string
      available_stages: string[]
    }>
  } | null>(null)

  const refreshExecution = async () => {
    if (!activeExecution) return
    try {
      const { getScenarioExecution } = await import('./api')
      const data = await getScenarioExecution(projectId, activeExecution.id)
      setActiveExecutionDetails({
        id: data.id,
        status: data.status,
        steps: data.steps.map((step) => ({
          id: step.id,
          keyword: step.keyword,
          text: step.text,
          status: step.status,
          execution_mode: step.execution_mode,
          available_stages: step.available_stages,
        })),
      })
    } catch {
      toast.error('Failed to refresh execution.')
    }
  }

  const steps = activeExecutionDetails?.steps ?? []
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
            <h2 className='text-2xl font-bold tracking-tight'>Execution</h2>
            <p className='text-muted-foreground'>Run test plans and hybrid steps.</p>
          </div>
          <div className='flex items-center gap-2'>
            <Input className='w-56' placeholder='Filter scenarios' />
            <Button onClick={() => triggerRunMutation.mutate()} disabled={triggerRunMutation.isPending}>
              {triggerRunMutation.isPending ? 'Running…' : 'Run Test Plan'}
            </Button>
          </div>
        </div>

        {isPlansError && (
          <div className='flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive'>
            <AlertCircle size={16} />
            <span>Failed to load test plans. Please try again later.</span>
          </div>
        )}

        {isPlansLoading ? (
          <div className='flex flex-1 items-center justify-center py-16'>
            <Loader2 className='size-8 animate-spin text-muted-foreground' />
          </div>
        ) : (
          <div className='grid gap-4 lg:grid-cols-[2fr_1fr]'>
          <Card>
            <CardHeader>
              <CardTitle>Plan Scenarios</CardTitle>
            </CardHeader>
            <CardContent className='space-y-3'>
              {planItems?.map((item) => (
                <button
                  key={item.id}
                  type='button'
                  className='flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm'
                  onClick={() =>
                    createExecutionMutation.mutate({
                      scenario_id: item.scenario_id,
                      test_plan_item_id: item.id,
                    })
                  }
                >
                  <div>
                    <div className='font-medium'>
                      {scenarioNameMap.get(item.scenario_id) ?? 'Unknown scenario'}
                    </div>
                    <div className='text-xs text-muted-foreground'>
                      Status: {item.status}
                    </div>
                  </div>
                  <StatusBadge status={item.status} />
                </button>
              ))}
              {!planItems?.length && (
                <div className='rounded-lg border border-dashed p-3 text-xs text-muted-foreground'>
                  No test plan items yet.
                </div>
              )}
              <div className='flex items-center gap-2'>
                <Button variant='outline' size='sm'>
                  Mark pass/fail/skip
                </Button>
                <Button variant='outline' size='sm'>
                  Run selected
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Step Execution</CardTitle>
            </CardHeader>
            <CardContent className='space-y-3 text-sm'>
              <div className='rounded-lg border p-3'>
                <div className='font-medium'>
                  Scenario:{' '}
                  {activeExecution
                    ? scenarioNameMap.get(activeExecution.scenarioId) ?? 'Selected'
                    : 'Not selected'}
                </div>
                <div className='text-muted-foreground'>
                  Status: {activeExecutionDetails?.status ?? 'idle'}
                </div>
              </div>
              {steps.map((step) => (
                <div key={step.id} className='space-y-2 rounded-lg border p-3'>
                  <div className='flex items-center justify-between'>
                    <div>
                      <div className='font-medium'>
                        {step.keyword} {step.text}
                      </div>
                      <div className='text-xs text-muted-foreground'>
                        Mode: {step.execution_mode}
                      </div>
                    </div>
                    <StatusBadge status={step.status} />
                  </div>
                  <div className='flex flex-wrap items-center gap-2'>
                    {step.available_stages.length ? (
                      <Badge variant='outline'>
                        Stage: {step.available_stages[0]}
                      </Badge>
                    ) : (
                      <Badge variant='secondary'>Manual</Badge>
                    )}
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={!activeExecution || step.available_stages.length === 0}
                      onClick={() => {
                        if (!activeExecution) return
                        const stage = step.available_stages[0]
                        if (!stage) return
                        runAutoMutation.mutate({
                          execId: activeExecution.id,
                          recordId: step.id,
                          stageName: stage,
                        })
                      }}
                    >
                      Run step
                    </Button>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={!activeExecution}
                      onClick={() => {
                        if (!activeExecution) return
                        manualStepMutation.mutate({
                          execId: activeExecution.id,
                          recordId: step.id,
                          status: 'pass',
                        })
                      }}
                    >
                      Mark pass
                    </Button>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={!activeExecution}
                      onClick={() => {
                        if (!activeExecution) return
                        manualStepMutation.mutate({
                          execId: activeExecution.id,
                          recordId: step.id,
                          status: 'fail',
                        })
                      }}
                    >
                      Mark fail
                    </Button>
                    <Button
                      variant='outline'
                      size='sm'
                      disabled={!activeExecution}
                      onClick={() => {
                        if (!activeExecution) return
                        manualStepMutation.mutate({
                          execId: activeExecution.id,
                          recordId: step.id,
                          status: 'skip',
                        })
                      }}
                    >
                      Skip
                    </Button>
                  </div>
                </div>
              ))}
              {!steps.length && (
                <div className='rounded-lg border border-dashed p-3 text-xs text-muted-foreground'>
                  Select a scenario to load steps.
                </div>
              )}
              <div className='rounded-lg border border-dashed p-3 text-xs text-muted-foreground'>
                Auto steps can run in selected stage; manual steps allow pass/fail/skip.
              </div>
              <Button variant='outline' size='sm' onClick={refreshExecution}>
                Refresh execution
              </Button>
            </CardContent>
          </Card>
        </div>
        )}
      </Main>
    </>
  )
}
