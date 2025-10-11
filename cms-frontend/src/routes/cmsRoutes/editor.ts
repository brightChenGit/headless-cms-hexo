import type { RouteRecordRaw } from 'vue-router'

export const editorRoutes: RouteRecordRaw[] = [

    {
        path: '/editor/:path*',
        name: 'ArticleEditor',
        component: () => import('@/views/ArticleEditor.vue'),
        meta: {
            title: '文章编辑',
            hidden: true
        }
    }
]