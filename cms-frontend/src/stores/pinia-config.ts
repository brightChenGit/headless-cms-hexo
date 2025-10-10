import { defineStore } from 'pinia'

export const useConfigStore = defineStore('pinia-config', {
    state: () => ({
        gitUrl: '',
        branch: '',
        apiUrl: '',
        token: ''
    }),

    actions: {
        setConfig(config: { gitUrl: string; branch: string; apiUrl: string; token: string }) {
            this.gitUrl = config.gitUrl
            this.branch = config.branch
            this.apiUrl = config.apiUrl
            this.token = config.token
            // 持久化到 localStorage
            localStorage.setItem('hexo-cms-config', JSON.stringify(config))
        }
    },

    // 启动时从 localStorage 恢复
    persist: {
        key: 'hexo-cms-config',
        storage: localStorage,
        paths: ['gitUrl', 'branch', 'apiUrl', 'token']
    }
})