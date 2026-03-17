import { createFileRoute } from '@tanstack/react-router'
import { TestPlanPage } from '@/features/bdd'

export const Route = createFileRoute('/_authenticated/projects/$projectId/test-plan/')({
  component: TestPlanPage,
})
