import { useMemo, useState } from 'react'
import { Link } from '@tanstack/react-router'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { ConfigDrawer } from '@/components/config-drawer'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { createProject, listProjects } from './api'

export function ProjectsPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
      setIsCreateOpen(false)
      setName('')
      setDescription('')
      toast.success('Project created.')
    },
    onError: () => {
      toast.error('Failed to create project.')
    },
  })

  const projects = useMemo(() => data ?? [], [data])

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
            <h2 className='text-2xl font-bold tracking-tight'>Projects</h2>
            <p className='text-muted-foreground'>Manage BDD workspaces and Git sync.</p>
          </div>
          <div className='flex items-center gap-2'>
            <Input className='w-64' placeholder='Search projects' />
            <Button onClick={() => setIsCreateOpen(true)}>Create Project</Button>
          </div>
        </div>

        {isError && (
          <div className='flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive'>
            <AlertCircle size={16} />
            <span>Failed to load projects. Please try again later.</span>
          </div>
        )}

        {isLoading ? (
          <div className='flex flex-1 items-center justify-center py-16'>
            <Loader2 className='size-8 animate-spin text-muted-foreground' />
          </div>
        ) : (
          <div className='grid gap-4 md:grid-cols-2 xl:grid-cols-3'>
            {projects.map((project) => {
              const updatedAt = project.updated_at
                ? formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })
                : '—'

              return (
                <Card key={project.id} className='flex h-full flex-col'>
                  <CardHeader className='space-y-2'>
                    <div className='flex items-center justify-between'>
                      <CardTitle className='text-lg'>{project.name}</CardTitle>
                    </div>
                    <p className='text-sm text-muted-foreground'>
                      {project.description || 'No description'}
                    </p>
                  </CardHeader>
                  <CardContent className='flex flex-1 flex-col gap-4'>
                    <div className='flex items-center justify-between text-sm'>
                      <span className='text-muted-foreground'>Updated</span>
                      <span className='font-medium'>{updatedAt}</span>
                    </div>
                    <div className='mt-auto flex items-center justify-end'>
                      <Button asChild>
                        <Link to='/projects/$projectId' params={{ projectId: project.id }}>
                          Open
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </Main>

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Project</DialogTitle>
          </DialogHeader>
          <div className='grid gap-4'>
            <div className='grid gap-2'>
              <Label htmlFor='project-name'>Project name</Label>
              <Input
                id='project-name'
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder='BDD workspace name'
              />
            </div>
            <div className='grid gap-2'>
              <Label htmlFor='project-description'>Description</Label>
              <Textarea
                id='project-description'
                rows={4}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder='Optional summary'
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant='outline' onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() =>
                createMutation.mutate({
                  name: name.trim(),
                  description: description.trim() ? description.trim() : null,
                })
              }
              disabled={!name.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? 'Creating…' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
