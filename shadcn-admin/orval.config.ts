import { defineConfig } from 'orval'

/**
 * Orval code-generation config.
 *
 * In Orval 8, MSW request handlers are co-generated with the API client by
 * setting `mock: true` on the same output block.  The generated mock files
 * follow the naming `<tag>.msw.ts` and sit next to the client files in
 * `src/api/generated/`.
 *
 * Regenerate with:
 *   pnpm exec nx run app-web:generate-api
 */
export default defineConfig({
    'api-client': {
        input: {
            target: '../openspec/contracts/app-api.openapi.json',
        },
        output: {
            mode: 'tags-split',
            target: './src/api/generated',
            schemas: './src/api/generated/model',
            client: 'react-query',
            httpClient: 'axios',
            mock: true,
            override: {
                mutator: {
                    path: './src/lib/axios-instance.ts',
                    name: 'axiosInstance',
                },
            },
        },
    },
})
