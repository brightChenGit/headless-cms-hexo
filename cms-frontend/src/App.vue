<!-- src/App.vue -->
<template>
  <div id="app">
    <nav class="navbar">
      <router-link
          v-for="route in visibleRoutes"
          :key="route.name"
          :to="{ name: route.name }"
          class="nav-link"
          active-class="active"
      >
        {{ route.meta?.title || route.name }}
      </router-link>
    </nav>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
// import { RouteRecordRaw } from 'vue-router'
// import { useRoute } from 'vue-router'
// 导入路由配置，用于动态生成菜单
import { computed } from 'vue'

import route from './routes'
// // 从路由中提取菜单项（排除重定向等）
// const routes = route.getRoutes().filter(r => r.meta?.title)
// 计算属性：过滤出需要显示在菜单中的路由
const visibleRoutes = computed(() => {
  return route.getRoutes().filter(route => {
    // 确保有 name、有 component、meta 存在且 hidden !== true
    return route.name && route.components && route.meta && !route.meta.hidden
  }).sort((a, b) => {
        // 默认 order 为 999（放在最后）
        const orderA = (a.meta?.order as number) || 999
        const orderB = (b.meta?.order as number) || 999
        return orderA - orderB
      })
})
</script>

<style>
#app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.navbar {
  display: flex;
  gap: 20px;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
  margin-bottom: 20px;
}

.nav-link {
  padding: 8px 16px;
  text-decoration: none;
  color: #333;
  border-radius: 4px;
}

.nav-link:hover,
.nav-link.active {
  background-color: #007bff;
  color: white;
}

.main-content {
  min-height: 400px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>