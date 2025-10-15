import type { RouteRecordRaw } from 'vue-router'

export const menuRoutes: RouteRecordRaw[] = [

    {
        path: '/',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页',order: 1}
    },
    // 重定向，确保 / 一定进 Home
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    },
    {
        path: '/posts',
        name: 'Posts',
        component: () => import('@/views/Posts.vue'),
        meta: { title: '文章列表',order:2 }
    },{
        path: '/editor/new',
        name: 'create',
        component: () => import('@/views/ArticleEditor.vue'),
        meta: { title: '创建文章',order:3 }
    }
]