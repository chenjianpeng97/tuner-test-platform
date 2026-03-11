/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_MSW_ENABLED?: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
