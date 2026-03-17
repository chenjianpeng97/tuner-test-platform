import { createFileRoute } from '@tanstack/react-router'
import { FeatureEditorPage } from '@/features/bdd'

export const Route = createFileRoute(
  '/_authenticated/projects/$projectId/features/$featureId/edit'
)({
  component: FeatureEditorPage,
})
