import { createFileRoute } from '@tanstack/react-router'
import { FeatureBrowserPage } from '@/features/bdd'

export const Route = createFileRoute('/_authenticated/projects/$projectId/features/')({
  component: FeatureBrowserPage,
})
