// src/types/pinia.d.ts 或 src/pinia.d.ts

import 'pinia'

declare module 'pinia' {
    export interface DefineStoreOptionsBase<S, Store> {
        persist?: boolean | {
            key?: string
            storage?: Storage
            paths?: string[]
            // 可选：你还可以扩展更多配置，如 serializer、afterRestore 等
            beforeRestore?: (context: any) => void
            afterRestore?: (context: any) => void
        }
    }
}