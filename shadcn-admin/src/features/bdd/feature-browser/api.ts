import { instance } from '@/lib/axios-instance'

export type FeatureTreeScenarioNode = {
  type: 'scenario'
  id: string
  name: string
  rule_name: string | null
  line_number: number | null
  coverage_status: 'covered' | 'failed' | 'uncovered'
}

export type FeatureTreeRuleNode = {
  type: 'rule'
  name: string
  scenarios: FeatureTreeScenarioNode[]
}

export type FeatureTreeNode = {
  type: 'feature'
  id: string
  file_path: string
  feature_name: string
  depth: number
  scenario_count: number
  rules: FeatureTreeRuleNode[]
  scenarios: FeatureTreeScenarioNode[]
  children: FeatureTreeNode[]
}

export type FeatureDetail = {
  id: string
  project_id: string
  file_path: string
  feature_name: string
  content: string
  git_sha: string | null
}

export async function listProjectFeatures(
  projectId: string
): Promise<FeatureTreeNode[]> {
  const response = await instance.get<FeatureTreeNode[]>(
    `/api/v1/projects/${projectId}/features`
  )
  return response.data
}

export async function getFeatureDetail(
  projectId: string,
  featureId: string
): Promise<FeatureDetail> {
  const response = await instance.get<FeatureDetail>(
    `/api/v1/projects/${projectId}/features/${featureId}`
  )
  return response.data
}
