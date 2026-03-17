import { createFileRoute } from '@tanstack/react-router'
import { ProjectsPage } from '@/features/bdd'

export const Route = createFileRoute('/_authenticated/projects/')({
  component: ProjectsPage,
})
