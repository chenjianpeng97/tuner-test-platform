import { instance } from '@/lib/axios-instance'

export type TestPlan = {
  id: string
  project_id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export type TestPlanItem = {
  id: string
  test_plan_id: string
  scenario_id: string
  status: 'not_run' | 'pass' | 'fail' | 'skip' | 'blocked'
  notes: string | null
  updated_at: string
}

export type TestRunResponse = {
  id: string
  project_id: string
  status: string
  scope_type: string
  scope_value: string | null
  triggered_at: string
  completed_at: string | null
}

export type ScenarioExecutionStep = {
  id: string
  step_id: string
  step_order: number
  keyword: string
  text: string
  execution_mode: string
  status: string
  stage_id: string | null
  executor: string | null
  executed_at: string | null
  notes: string | null
  error_message: string | null
  available_stages: string[]
}

export type ScenarioExecution = {
  id: string
  project_id: string
  scenario_id: string
  status: string
  created_at: string
  completed_at: string | null
  steps: ScenarioExecutionStep[]
}

export async function listTestPlans(projectId: string): Promise<TestPlan[]> {
  const response = await instance.get<TestPlan[]>(
    `/api/v1/projects/${projectId}/test-plans`
  )
  return response.data
}

export async function listTestPlanItems(
  projectId: string,
  planId: string
): Promise<TestPlanItem[]> {
  const response = await instance.get<TestPlanItem[]>(
    `/api/v1/projects/${projectId}/test-plans/${planId}/items`
  )
  return response.data
}

export async function updateTestPlanItemStatus(
  projectId: string,
  planId: string,
  itemId: string,
  status: TestPlanItem['status']
): Promise<TestPlanItem> {
  const response = await instance.patch<TestPlanItem>(
    `/api/v1/projects/${projectId}/test-plans/${planId}/items/${itemId}`,
    { status }
  )
  return response.data
}

export async function triggerTestRun(
  projectId: string,
  payload: { scope_type: 'project' | 'feature' | 'tag'; scope_value?: string | null }
): Promise<TestRunResponse> {
  const response = await instance.post<TestRunResponse>(
    `/api/v1/projects/${projectId}/test-runs`,
    payload
  )
  return response.data
}

export async function createScenarioExecution(
  projectId: string,
  payload: { scenario_id: string; test_plan_item_id?: string | null }
): Promise<ScenarioExecution> {
  const response = await instance.post<ScenarioExecution>(
    `/api/v1/projects/${projectId}/scenario-executions`,
    payload
  )
  return response.data
}

export async function getScenarioExecution(
  projectId: string,
  execId: string
): Promise<ScenarioExecution> {
  const response = await instance.get<ScenarioExecution>(
    `/api/v1/projects/${projectId}/scenario-executions/${execId}`
  )
  return response.data
}

export async function runAutoStep(
  projectId: string,
  execId: string,
  recordId: string,
  stageName: string
): Promise<{ status: string }> {
  const response = await instance.post<{ status: string }>(
    `/api/v1/projects/${projectId}/scenario-executions/${execId}/steps/${recordId}/auto`,
    { stage_name: stageName }
  )
  return response.data
}

export async function updateManualStep(
  projectId: string,
  execId: string,
  recordId: string,
  status: 'pass' | 'fail' | 'skip'
): Promise<{ status: string }> {
  const response = await instance.patch<{ status: string }>(
    `/api/v1/projects/${projectId}/scenario-executions/${execId}/steps/${recordId}/manual`,
    { status }
  )
  return response.data
}
