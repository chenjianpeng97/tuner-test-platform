import { createFileRoute } from '@tanstack/react-router'
import { ExecutionPage } from '@/features/bdd'

export const Route = createFileRoute('/_authenticated/projects/$projectId/execution/')({
  component: ExecutionPage,
})
