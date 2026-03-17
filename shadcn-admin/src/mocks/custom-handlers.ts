/**
 * Custom MSW handlers that override the auto-generated ones with richer,
 * more realistic mock data and proper session cookie simulation.
 *
 * Import order matters: these handlers are placed BEFORE the generated ones
 * in the `handlers` array so they take priority.
 *
 * ⚠️  Do NOT hardcode user data here.
 *    Edit features/fixtures/fixtures.toml, then run:
 *      pnpm exec nx run ux-uat:gen-fixtures
 */
import { http, HttpResponse } from 'msw'
import type { CurrentUserResponse, ListUsersQM } from '@/api/generated/model'
import { ALL_FIXTURE_USERS, FIXTURE_USERS } from './__fixtures__.generated'

// In-memory session state (MSW service worker scope)
let currentSessionUser: CurrentUserResponse | null = null

type MockProject = {
    id: string
    name: string
    description: string | null
    created_at: string
    updated_at: string
}

type MockGitConfig = {
    project_id: string
    git_repo_url: string
    git_branch: string
    git_access_token?: string
    features_root?: string
}

const nowIso = () => new Date().toISOString()

const mockProjects: MockProject[] = [
    {
        id: crypto.randomUUID(),
        name: 'Identity Platform',
        description: 'Core auth & onboarding flows',
        created_at: nowIso(),
        updated_at: nowIso(),
    },
    {
        id: crypto.randomUUID(),
        name: 'Billing API',
        description: 'Payment scenarios & disputes',
        created_at: nowIso(),
        updated_at: nowIso(),
    },
]

const mockGitConfigs = new Map<string, MockGitConfig>([
    [
        mockProjects[0].id,
        {
            project_id: mockProjects[0].id,
            git_repo_url: 'git@github.com:acme/identity-bdd.git',
            git_branch: 'main',
            git_access_token: '***',
            features_root: 'features/',
        },
    ],
])

type MockScenario = {
    id: string
    name: string
    coverage_status: 'covered' | 'failed' | 'uncovered'
}

type MockFeatureNode = {
    id: string
    file_path: string
    feature_name: string
    scenarios: MockScenario[]
    children: MockFeatureNode[]
}

const mockFeatureTree: Record<string, MockFeatureNode[]> = {
    [mockProjects[0].id]: [
        {
            id: crypto.randomUUID(),
            file_path: 'auth.feature',
            feature_name: 'Authentication',
            scenarios: [
                {
                    id: crypto.randomUUID(),
                    name: 'Login success',
                    coverage_status: 'covered',
                },
                {
                    id: crypto.randomUUID(),
                    name: 'Login failure',
                    coverage_status: 'failed',
                },
            ],
            children: [],
        },
    ],
    [mockProjects[1].id]: [],
}

const mockTestPlans: Record<string, Array<{ id: string; name: string }>> = {
    [mockProjects[0].id]: [
        { id: crypto.randomUUID(), name: 'Regression Plan' },
    ],
    [mockProjects[1].id]: [],
}

const mockTestPlanItems: Record<string, Array<{ id: string; scenario_id: string; status: string }>> = {}

const ensurePlanItems = (projectId: string) => {
    if (mockTestPlanItems[projectId]) {
        return
    }
    const plan = mockTestPlans[projectId]?.[0]
    const scenarioIds =
        mockFeatureTree[projectId]?.flatMap((feature) =>
            feature.scenarios.map((scenario) => scenario.id)
        ) ?? []
    mockTestPlanItems[projectId] =
        plan && scenarioIds.length
            ? scenarioIds.map((scenarioId) => ({
                  id: crypto.randomUUID(),
                  scenario_id: scenarioId,
                  status: 'not_run',
              }))
            : []
}

// ─── Custom handlers ──────────────────────────────────────────────────────────
export const customHandlers = [
    // POST /api/v1/account/login
    http.post('*/api/v1/account/login', async ({ request }) => {
        const body = (await request.json()) as { username?: string; password?: string }
        const record = body.username ? FIXTURE_USERS[body.username] : undefined

        if (!record || record.password !== body.password) {
            return HttpResponse.json(
                { message: 'Invalid credentials' },
                { status: 401 }
            )
        }

        currentSessionUser = record.profile
        // The real backend sets an HTTP-only cookie; in MSW we just track state.
        return new HttpResponse(null, { status: 204 })
    }),

    // GET /api/v1/users/me
    http.get('*/api/v1/users/me', () => {
        if (!currentSessionUser) {
            return HttpResponse.json({ message: 'Not authenticated' }, { status: 401 })
        }
        return HttpResponse.json(currentSessionUser, { status: 200 })
    }),

    // DELETE /api/v1/account/logout
    http.delete('*/api/v1/account/logout', () => {
        currentSessionUser = null
        return new HttpResponse(null, { status: 204 })
    }),

    // GET /api/v1/users/  (list)
    http.get('*/api/v1/users/', ({ request }) => {
        const url = new URL(request.url)
        const roleFilter = url.searchParams.get('role')
        const page = parseInt(url.searchParams.get('page') ?? '1', 10)
        const pageSize = parseInt(url.searchParams.get('page_size') ?? '10', 10)

        const filtered = roleFilter
            ? ALL_FIXTURE_USERS.filter((u) => u.role === roleFilter)
            : ALL_FIXTURE_USERS

        const start = (page - 1) * pageSize
        const pagedUsers = filtered.slice(start, start + pageSize)

        const response: ListUsersQM = {
            users: pagedUsers,
            total: filtered.length,
        }

        return HttpResponse.json(response, { status: 200 })
    }),

    // GET /api/v1/projects/
    http.get('*/api/v1/projects/', () => {
        return HttpResponse.json(mockProjects, { status: 200 })
    }),

    // POST /api/v1/projects/
    http.post('*/api/v1/projects/', async ({ request }) => {
        const body = (await request.json()) as { name?: string; description?: string }
        if (!body.name || body.name.trim().length === 0) {
            return HttpResponse.json(
                { message: 'name is required' },
                { status: 422 }
            )
        }
        const now = nowIso()
        const record: MockProject = {
            id: crypto.randomUUID(),
            name: body.name.trim(),
            description: body.description ?? null,
            created_at: now,
            updated_at: now,
        }
        mockProjects.unshift(record)
        return HttpResponse.json(record, { status: 201 })
    }),

    // GET /api/v1/projects/:projectId
    http.get('*/api/v1/projects/:projectId', ({ params }) => {
        const project = mockProjects.find((item) => item.id === params.projectId)
        if (!project) {
            return HttpResponse.json({ message: 'Not found' }, { status: 404 })
        }
        return HttpResponse.json(project, { status: 200 })
    }),

    // PATCH /api/v1/projects/:projectId
    http.patch('*/api/v1/projects/:projectId', async ({ request, params }) => {
        const project = mockProjects.find((item) => item.id === params.projectId)
        if (!project) {
            return HttpResponse.json({ message: 'Not found' }, { status: 404 })
        }
        const body = (await request.json()) as {
            name?: string
            description?: string | null
        }
        if (typeof body.name === 'string' && body.name.trim().length === 0) {
            return HttpResponse.json(
                { message: 'name is required' },
                { status: 422 }
            )
        }
        if (typeof body.name === 'string') {
            project.name = body.name.trim()
        }
        if (body.description !== undefined) {
            project.description = body.description
        }
        project.updated_at = nowIso()
        return HttpResponse.json(project, { status: 200 })
    }),

    // DELETE /api/v1/projects/:projectId
    http.delete('*/api/v1/projects/:projectId', ({ params }) => {
        const index = mockProjects.findIndex((item) => item.id === params.projectId)
        if (index === -1) {
            return HttpResponse.json({ message: 'Not found' }, { status: 404 })
        }
        mockProjects.splice(index, 1)
        mockGitConfigs.delete(params.projectId as string)
        return new HttpResponse(null, { status: 204 })
    }),

    // GET /api/v1/projects/:projectId/git-config
    http.get('*/api/v1/projects/:projectId/git-config', ({ params }) => {
        const config = mockGitConfigs.get(params.projectId as string)
        if (!config) {
            return HttpResponse.json({ message: 'Not found' }, { status: 404 })
        }
        return HttpResponse.json(
            {
                project_id: config.project_id,
                git_repo_url: config.git_repo_url,
                git_branch: config.git_branch,
                features_root: config.features_root ?? 'features/',
            },
            { status: 200 }
        )
    }),

    // PUT /api/v1/projects/:projectId/git-config
    http.put('*/api/v1/projects/:projectId/git-config', async ({ request, params }) => {
        const body = (await request.json()) as {
            git_repo_url?: string
            git_branch?: string
            git_access_token?: string
        }
        if (!body.git_repo_url || !body.git_branch || !body.git_access_token) {
            return HttpResponse.json(
                { message: 'missing fields' },
                { status: 422 }
            )
        }
        const config: MockGitConfig = {
            project_id: params.projectId as string,
            git_repo_url: body.git_repo_url,
            git_branch: body.git_branch,
            git_access_token: body.git_access_token,
            features_root: body.features_root ?? 'features/',
        }
        mockGitConfigs.set(params.projectId as string, config)
        return HttpResponse.json(
            {
                project_id: config.project_id,
                git_repo_url: config.git_repo_url,
                git_branch: config.git_branch,
                features_root: config.features_root ?? 'features/',
            },
            { status: 200 }
        )
    }),

    // POST /api/v1/projects/:projectId/sync
    http.post('*/api/v1/projects/:projectId/sync', ({ params }) => {
        if (!mockProjects.find((item) => item.id === params.projectId)) {
            return HttpResponse.json({ message: 'Not found' }, { status: 404 })
        }
        return HttpResponse.json(
            {
                added: 2,
                updated: 1,
                deleted: 0,
                total: 3,
                synced_at: nowIso(),
            },
            { status: 200 }
        )
    }),

    // GET /api/v1/projects/:projectId/features
    http.get('*/api/v1/projects/:projectId/features', ({ params }) => {
        const projectId = params.projectId as string
        const features = mockFeatureTree[projectId] ?? []
        const toNode = (node: MockFeatureNode, depth = 0) => ({
            type: 'feature',
            id: node.id,
            file_path: node.file_path,
            feature_name: node.feature_name,
            depth,
            scenario_count: node.scenarios.length,
            rules: [],
            scenarios: node.scenarios.map((scenario) => ({
                type: 'scenario',
                id: scenario.id,
                name: scenario.name,
                rule_name: null,
                line_number: null,
                coverage_status: scenario.coverage_status,
            })),
            children: node.children.map((child) => toNode(child, depth + 1)),
        })
        return HttpResponse.json(features.map((feature) => toNode(feature)), { status: 200 })
    }),

    // GET /api/v1/projects/:projectId/features/:featureId
    http.get('*/api/v1/projects/:projectId/features/:featureId', ({ params }) => {
        const projectId = params.projectId as string
        const featureId = params.featureId as string
        const feature = (mockFeatureTree[projectId] ?? []).find(
            (item) => item.id === featureId
        )
        if (!feature) {
            return HttpResponse.json({ message: 'Not found' }, { status: 404 })
        }
        return HttpResponse.json(
            {
                id: feature.id,
                project_id: projectId,
                file_path: feature.file_path,
                feature_name: feature.feature_name,
                content: `Feature: ${feature.feature_name}`,
                git_sha: null,
            },
            { status: 200 }
        )
    }),

    // GET /api/v1/projects/:projectId/test-plans
    http.get('*/api/v1/projects/:projectId/test-plans', ({ params }) => {
        const projectId = params.projectId as string
        const plans = (mockTestPlans[projectId] ?? []).map((plan) => ({
            id: plan.id,
            project_id: projectId,
            name: plan.name,
            description: null,
            created_at: nowIso(),
            updated_at: nowIso(),
        }))
        return HttpResponse.json(plans, { status: 200 })
    }),

    // GET /api/v1/projects/:projectId/test-plans/:planId/items
    http.get(
        '*/api/v1/projects/:projectId/test-plans/:planId/items',
        ({ params }) => {
            const projectId = params.projectId as string
            ensurePlanItems(projectId)
            const items = mockTestPlanItems[projectId].map((item) => ({
                id: item.id,
                test_plan_id: params.planId,
                scenario_id: item.scenario_id,
                status: item.status,
                notes: null,
                updated_at: nowIso(),
            }))
            return HttpResponse.json(items, { status: 200 })
        }
    ),

    // PATCH /api/v1/projects/:projectId/test-plans/:planId/items/:itemId
    http.patch(
        '*/api/v1/projects/:projectId/test-plans/:planId/items/:itemId',
        async ({ request, params }) => {
            const projectId = params.projectId as string
            ensurePlanItems(projectId)
            const body = (await request.json()) as { status?: string }
            const item = mockTestPlanItems[projectId].find(
                (entry) => entry.id === params.itemId
            )
            if (!item) {
                return HttpResponse.json({ message: 'Not found' }, { status: 404 })
            }
            if (body.status) {
                item.status = body.status
            }
            return HttpResponse.json(
                {
                    id: item.id,
                    test_plan_id: params.planId,
                    scenario_id: item.scenario_id,
                    status: item.status,
                    notes: null,
                    updated_at: nowIso(),
                },
                { status: 200 }
            )
        }
    ),

    // POST /api/v1/projects/:projectId/test-runs
    http.post('*/api/v1/projects/:projectId/test-runs', ({ params }) => {
        return HttpResponse.json(
            {
                id: crypto.randomUUID(),
                project_id: params.projectId,
                status: 'pending',
                scope_type: 'project',
                scope_value: null,
                triggered_at: nowIso(),
                completed_at: null,
            },
            { status: 202 }
        )
    }),

    // POST /api/v1/projects/:projectId/scenario-executions
    http.post(
        '*/api/v1/projects/:projectId/scenario-executions',
        async ({ request, params }) => {
            const projectId = params.projectId as string
            const body = (await request.json()) as { scenario_id: string }
            const steps = [
                {
                    id: crypto.randomUUID(),
                    step_id: crypto.randomUUID(),
                    step_order: 1,
                    keyword: 'Given',
                    text: 'user exists',
                    execution_mode: 'auto',
                    status: 'pending',
                    stage_id: null,
                    executor: null,
                    executed_at: null,
                    notes: null,
                    error_message: null,
                    available_stages: ['http'],
                },
                {
                    id: crypto.randomUUID(),
                    step_id: crypto.randomUUID(),
                    step_order: 2,
                    keyword: 'When',
                    text: 'user logs in',
                    execution_mode: 'manual',
                    status: 'pending',
                    stage_id: null,
                    executor: null,
                    executed_at: null,
                    notes: null,
                    error_message: null,
                    available_stages: [],
                },
            ]
            return HttpResponse.json(
                {
                    id: crypto.randomUUID(),
                    project_id: projectId,
                    scenario_id: body.scenario_id,
                    status: 'in_progress',
                    created_at: nowIso(),
                    completed_at: null,
                    steps,
                },
                { status: 201 }
            )
        }
    ),

    // POST /api/v1/projects/:projectId/scenario-executions/:execId/steps/:recordId/auto
    http.post(
        '*/api/v1/projects/:projectId/scenario-executions/:execId/steps/:recordId/auto',
        () => {
            return HttpResponse.json({ status: 'in_progress' }, { status: 200 })
        }
    ),

    // PATCH /api/v1/projects/:projectId/scenario-executions/:execId/steps/:recordId/manual
    http.patch(
        '*/api/v1/projects/:projectId/scenario-executions/:execId/steps/:recordId/manual',
        async ({ request }) => {
            const body = (await request.json()) as { status?: string }
            return HttpResponse.json(
                { status: body.status ?? 'in_progress' },
                { status: 200 }
            )
        }
    ),
]
