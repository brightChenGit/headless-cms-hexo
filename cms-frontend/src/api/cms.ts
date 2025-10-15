// src/api/cms.ts
import axios from 'axios'
import type { AxiosInstance } from 'axios'
import { useConfigStore } from '@/stores/pinia-config'

//  创建一个可复用的、带拦截器的 axios 实例（懒初始化）
let apiInstance: AxiosInstance | null = null

const getApiInstance = (): AxiosInstance => {
    if (!apiInstance) {

        const configStore = useConfigStore()
        apiInstance = axios.create({
            timeout: 10000,
            // baseURL 留空，由拦截器动态设置
        })

        //  请求拦截器：动态设置 baseURL + 自动添加 Authorization
        apiInstance.interceptors.request.use(
            (config) => {
                // 动态设置 baseURL（每次请求都获取最新值）
                config.baseURL = configStore.apiUrl

                // 自动添加 Bearer Token（如果存在）
                if (configStore.token) {
                    config.headers.Authorization = `Bearer ${configStore.token}`
                }

                return config
            },
            (error) => {
                return Promise.reject(error)
            }
        )

        //  响应拦截器（可选）：统一错误处理
        apiInstance.interceptors.response.use(
            (response) => response,
            (error) => {
                // 可统一处理 401、网络错误等
                if (error.response?.status === 401) {
                    // token 失效，可跳转登录或清空 token
                    console.warn('Unauthorized, token may be expired')
                }
                return Promise.reject(error)
            }
        )
    }

    return apiInstance
}

// ========================
// 👇 类型定义（保持不变）
// ========================

export interface FileNode {
    type: 'file'
    name: string
    path: string
    title?: string
    date?: string
    draft?: boolean
}

export interface DirNode {
    type: 'dir'
    name: string
    path: string
    children: TreeNode[]
}

export type TreeNode = FileNode | DirNode

export interface ListResponse {
    total: number
    items: TreeNode[]
}


export interface articleMoel {
    path: string
    filename: string
    title: string
    date: string
    draft: string
    body: string
}

// ========================
// 👇 API 方法（使用 getApiInstance()）
// ========================

// 获取文章树
export const getPostTree = async (): Promise<ListResponse> => {
    const configStore = useConfigStore() //  获取 store 实例

    const payload: Record<string, any> = {}

    //  自动携带 gitUrl（仅当非空）
    if (configStore.gitUrl && configStore.gitUrl.trim() !== '') {
        payload.url = configStore.gitUrl.trim() //  后端字段名是 git，不是 gitUrl
    }
    if (configStore.branch && configStore.branch.trim() !== '') {
        payload.branch = configStore.branch.trim() //  后端字段名是 git，不是 gitUrl
    }
    const res = await getApiInstance().post('/api/list', {payload})
    return res.data
}

// 删除文章
export const deleteArticle = async (path: string): Promise<void> => {
    await getApiInstance().post('/api/delete', { path })
}

// 保存文章
export const saveArticle = async (content: object): Promise<void> => {
    await getApiInstance().post('/api/saveArticle',  content )
}

// 可选：新增获取文章内容接口
export const getArticleContent = async (path: string): Promise<articleMoel> => {
    const res = await getApiInstance().post('/api/getArticle', { path })
    return res.data
}


export const pushArticle = async (): Promise<{ content: string }> => {
    const res = await getApiInstance().post('/api/updateGit', {})
    return res.data
}

export const deployHexo = async (): Promise<any> => {
    const res=await getApiInstance().post('/webhookHexo/deploy', {})
    return res.data
}

// 获取部署任务状态
export const getDeployStatus = (task_id: string | undefined) => {
    if (task_id === undefined) {
        return getApiInstance().get<{ status: 'running' | 'success' | 'failure'; steps: any[]; message?: string }>(
            `/webhookHexo/status`
        );
    }

    return getApiInstance().get<{ status: 'running' | 'success' | 'failure'; steps: any[]; message?: string }>(
        `/webhookHexo/status?task_id=${encodeURIComponent(task_id)}`
    );
};