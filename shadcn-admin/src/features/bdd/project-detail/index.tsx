import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { AxiosError } from 'axios'
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
import {
  getGitConfig,
  getProject,
  syncProject,
  updateGitConfig,
  updateProject,
} from '../projects/api'

export function ProjectDetailPage() {
  const { projectId } = useParams({ from: '/_authenticated/projects/$projectId/' })
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [gitRepoUrl, setGitRepoUrl] = useState('')
  const [gitBranch, setGitBranch] = useState('main')
  const [gitToken, setGitToken] = useState('')
  const [featuresRoot, setFeaturesRoot] = useState('features/')

  const {
    data: project,
    isLoading: isProjectLoading,
    isError: isProjectError,
  } = useQuery({
    queryKey: ['projects', projectId],
    queryFn: () => getProject(projectId),
  })

  const {
    data: gitConfig,
    isLoading: isGitLoading,
    isError: isGitError,
  } = useQuery({
    queryKey: ['projects', projectId, 'git-config'],
    queryFn: async () => {
      try {
        return await getGitConfig(projectId)
      } catch (error) {
        const axiosError = error as AxiosError
        if (axiosError.response?.status === 404) {
          return null
        }
        throw error
      }
    },
  })

  useEffect(() => {
    if (!project) {
      return
    }
    setName(project.name)
    setDescription(project.description ?? '')
  }, [project])

  useEffect(() => {
    if (!gitConfig) {
      return
    }
    setGitRepoUrl(gitConfig.git_repo_url)
    setGitBranch(gitConfig.git_branch)
    setFeaturesRoot(gitConfig.features_root || 'features/')
  }, [gitConfig])

  const updateProjectMutation = useMutation({
    mutationFn: (payload: { name: string; description: string | null }) =>
      updateProject(projectId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['projects', projectId] })
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success('Project updated.')
    },
    onError: () => {
      toast.error('Failed to update project.')
    },
  })

  const updateGitMutation = useMutation({
    mutationFn: (payload: {
      git_repo_url: string
      git_branch: string
      git_access_token: string
    }) => updateGitConfig(projectId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'git-config'],
      })
      setGitToken('')
      toast.success('Git config updated.')
    },
    onError: () => {
      toast.error('Failed to update Git config.')
    },
  })

  const syncMutation = useMutation({
    mutationFn: () => syncProject(projectId),
    onSuccess: () => {
      toast.success('Sync triggered.')
    },
    onError: () => {
      toast.error('Failed to trigger sync.')
    },
  })

  const showGitError = useMemo(() => isGitError, [isGitError])
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
        <div className='flex flex-wrap items-center justify-between gap-4'>
          <div>
            <h2 className='text-2xl font-bold tracking-tight'>Project Settings</h2>
            <p className='text-muted-foreground'>Update metadata and Git integration.</p>
          </div>
          <div className='flex items-center gap-2'>
            <Button asChild variant='outline'>
              <Link to='/projects/$projectId/features' params={{ projectId }}>
                Feature Browser
              </Link>
            </Button>
            <Button asChild>
              <Link to='/projects/$projectId/execution' params={{ projectId }}>
                Execution
              </Link>
            </Button>
          </div>
        </div>

        {isProjectError && (
          <div className='flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive'>
            <AlertCircle size={16} />
            <span>Failed to load project. Please try again later.</span>
          </div>
        )}

        {isProjectLoading ? (
          <div className='flex flex-1 items-center justify-center py-16'>
            <Loader2 className='size-8 animate-spin text-muted-foreground' />
          </div>
        ) : (
        <div className='grid gap-6 lg:grid-cols-[2fr_1fr]'>
          <Card>
            <CardHeader>
              <CardTitle>Project Info</CardTitle>
            </CardHeader>
            <CardContent className='grid gap-4'>
              <div className='grid gap-2'>
                <label className='text-sm font-medium'>Project name</label>
                <Input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
              </div>
              <div className='grid gap-2'>
                <label className='text-sm font-medium'>Description</label>
                <Textarea
                  rows={4}
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                />
              </div>
              <div className='flex items-center gap-2'>
                <Button
                  onClick={() =>
                    updateProjectMutation.mutate({
                      name: name.trim(),
                      description: description.trim() ? description.trim() : null,
                    })
                  }
                  disabled={!name.trim() || updateProjectMutation.isPending}
                >
                  {updateProjectMutation.isPending ? 'Saving…' : 'Save changes'}
                </Button>
                <Button
                  variant='outline'
                  onClick={() => {
                    if (!project) {
                      return
                    }
                    setName(project.name)
                    setDescription(project.description ?? '')
                  }}
                  disabled={!project}
                >
                  Discard
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Git Integration</CardTitle>
            </CardHeader>
            <CardContent className='grid gap-4'>
              {showGitError && (
                <div className='rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-xs text-destructive'>
                  Failed to load git config.
                </div>
              )}
              <div className='grid gap-2'>
                <label className='text-sm font-medium'>Repository URL</label>
                <Input
                  value={gitRepoUrl}
                  onChange={(event) => setGitRepoUrl(event.target.value)}
                  placeholder='git@github.com:org/repo.git'
                  disabled={isGitLoading}
                />
              </div>
              <div className='grid gap-2'>
                <label className='text-sm font-medium'>Branch</label>
                <Input
                  value={gitBranch}
                  onChange={(event) => setGitBranch(event.target.value)}
                  placeholder='main'
                  disabled={isGitLoading}
                />
              </div>
              <div className='grid gap-2'>
                <label className='text-sm font-medium'>Access token</label>
                <Input
                  type='password'
                  value={gitToken}
                  onChange={(event) => setGitToken(event.target.value)}
                  placeholder='Required to update'
                />
              </div>
              <div className='grid gap-2'>
                <label className='text-sm font-medium'>Features path</label>
                <Input
                  value={featuresRoot}
                  onChange={(event) => setFeaturesRoot(event.target.value)}
                  placeholder='features/'
                  disabled={isGitLoading}
                />
              </div>
              <div className='flex items-center justify-between rounded-lg border p-3 text-sm'>
                <div>
                  <div className='font-medium'>Last sync</div>
                  <div className='text-muted-foreground'>
                    {gitConfig ? 'Configured' : 'Not configured'}
                  </div>
                </div>
                <Badge>{gitConfig ? 'ready' : 'pending'}</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <Button
                  variant='outline'
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                >
                  {syncMutation.isPending ? 'Syncing…' : 'Sync now'}
                </Button>
                <Button
                  onClick={() =>
                    updateGitMutation.mutate({
                      git_repo_url: gitRepoUrl.trim(),
                      git_branch: gitBranch.trim() || 'main',
                      git_access_token: gitToken.trim(),
                      features_root: featuresRoot.trim() || 'features/',
                    })
                  }
                  disabled={
                    !gitRepoUrl.trim() ||
                    !gitBranch.trim() ||
                    !gitToken.trim() ||
                    updateGitMutation.isPending
                  }
                >
                  {updateGitMutation.isPending ? 'Saving…' : 'Save config'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
        )}
      </Main>
    </>
  )
}
