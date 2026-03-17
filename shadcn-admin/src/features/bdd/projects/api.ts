import { instance } from '@/lib/axios-instance'

export type Project = {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export type ProjectCreatePayload = {
  name: string
  description?: string | null
}

export type ProjectUpdatePayload = {
  name?: string | null
  description?: string | null
}

export type GitConfig = {
  project_id: string
  git_repo_url: string
  git_branch: string
  features_root: string
}

export type GitConfigUpdatePayload = {
  git_repo_url: string
  git_branch: string
  git_access_token: string
  features_root: string
}

export type ProjectSyncResponse = {
  added: number
  updated: number
  deleted: number
  total: number
  synced_at: string
}

export async function listProjects(): Promise<Project[]> {
  const response = await instance.get<Project[]>('/api/v1/projects/')
  return response.data
}

export async function createProject(
  payload: ProjectCreatePayload
): Promise<Project> {
  const response = await instance.post<Project>('/api/v1/projects/', payload)
  return response.data
}

export async function getProject(projectId: string): Promise<Project> {
  const response = await instance.get<Project>(`/api/v1/projects/${projectId}`)
  return response.data
}

export async function updateProject(
  projectId: string,
  payload: ProjectUpdatePayload
): Promise<Project> {
  const response = await instance.patch<Project>(
    `/api/v1/projects/${projectId}`,
    payload
  )
  return response.data
}

export async function deleteProject(projectId: string): Promise<void> {
  await instance.delete(`/api/v1/projects/${projectId}`)
}

export async function getGitConfig(projectId: string): Promise<GitConfig> {
  const response = await instance.get<GitConfig>(
    `/api/v1/projects/${projectId}/git-config`
  )
  return response.data
}

export async function updateGitConfig(
  projectId: string,
  payload: GitConfigUpdatePayload
): Promise<GitConfig> {
  const response = await instance.put<GitConfig>(
    `/api/v1/projects/${projectId}/git-config`,
    payload
  )
  return response.data
}

export async function syncProject(
  projectId: string
): Promise<ProjectSyncResponse> {
  const response = await instance.post<ProjectSyncResponse>(
    `/api/v1/projects/${projectId}/sync`
  )
  return response.data
}
