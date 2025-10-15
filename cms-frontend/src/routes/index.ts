// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 引入各模块路由
import { menuRoutes } from './cmsRoutes/menu'
import { editorRoutes } from './cmsRoutes/editor'




// 合并所有路由
const routes: RouteRecordRaw[] = [
    ...menuRoutes,
    ...editorRoutes,
]


const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router