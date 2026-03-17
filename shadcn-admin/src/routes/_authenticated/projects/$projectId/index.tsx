import { createFileRoute } from '@tanstack/react-router'
import { ProjectDetailPage } from '@/features/bdd'

export const Route = createFileRoute('/_authenticated/projects/$projectId/')({
  component: ProjectDetailPage,
})
