<!-- src/views/Posts.vue -->
<template>
  <div class="posts-container">
    <div class="posts-header">
      <el-input
          v-model="searchQuery"
          placeholder="搜索标题或路径..."
          style="width: 300px"
          clearable
          @input="handleSearch"
      />
      <el-button @click="refreshList" :loading="loading" :disabled="loading">刷新</el-button>
      <el-button type="primary" @click="goToEditor('new')">新增文章</el-button>
      <DeployButton />
    </div>

    <el-tree
        :indent="10"
        v-loading="loading"
        :data="displayTree"
        node-key="path"
        default-expand-all
        :expand-on-click-node="false"
        :filter-node-method="filterNode"
        ref="treeRef"
        class="custom-tree"
    >
      <template #default="{ node:_node, data }">
        <div class="tree-node-content">
          <span class="node-title">
            <i v-if="data.type === 'dir'" class="el-icon-folder"></i>
            <i v-else class="el-icon-document"></i>
            {{ data.name }}
          </span>
          <span v-if="data.type === 'file'" class="node-meta">
            <el-tag v-if="data.draft" size="small" type="warning">草稿</el-tag>
            <span v-if="data.date" class="date">{{ data.date }}</span>
          </span>
          <div v-if="data.type === 'file'" class="node-actions">
            <el-button size="small" :loading="buttonLoading" :disabled="buttonLoading" @click.stop="goToEditor(data.path)">编辑</el-button>
            <el-button size="small" :loading="buttonLoading" :disabled="buttonLoading" type="danger" @click.stop="handleDelete(data.path)">删除</el-button>
          </div>
        </div>
      </template>
    </el-tree>

    <div v-if="totalFiles > 0 && !searchQuery" class="pagination-wrapper">
      <el-pagination
          layout="total, prev, pager, next, jumper"
          :total="totalFiles"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="handlePageChange"
          background
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import DeployButton from '@/views/DeployButton.vue';
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPostTree, deleteArticle} from '@/api/cms'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { TreeNode, FileNode } from '@/api/cms'

const router = useRouter()
const treeRef = ref()
const searchQuery = ref('')
const loading = ref(false)
const rawTree = ref<TreeNode[]>([])
const totalFiles = ref(0)

const buttonLoading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = 10
const paginatedFiles = ref<Set<string>>(new Set())

// 提取所有文件（用于分页）
const allFiles = computed(() => {
  const files: FileNode[] = []

  const traverse = (nodes: TreeNode[]) => {
    nodes.forEach(node => {
      if (node.type === 'file') {
        files.push(node)
      } else if (node.type === 'dir' && node.children) {
        traverse(node.children)
      }
    })
  }

  traverse(rawTree.value)
  return files
})

// 更新当前页文件路径集合
const updatePaginatedFiles = () => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  const current = allFiles.value.slice(start, end)
  paginatedFiles.value = new Set(current.map(f => f.path))
}

// 显示的树结构（根据搜索或分页过滤）
const displayTree = computed(() => {
  if (searchQuery.value) {
    return filterTree(rawTree.value, searchQuery.value)
  } else {
    updatePaginatedFiles()
    return filterTreeByPage(rawTree.value)
  }
})

// 搜索过滤树
const filterTree = (nodes: TreeNode[], query: string): TreeNode[] => {
  return nodes.reduce<TreeNode[]>((acc, node) => {
    if (node.type === 'file') {
      if (
          node.name.toLowerCase().includes(query.toLowerCase()) ||
          node.path.toLowerCase().includes(query.toLowerCase()) ||
          (node.title && node.title.toLowerCase().includes(query.toLowerCase()))
      ) {
        acc.push({ ...node })
      }
    } else {
      const filteredChildren = filterTree(node.children || [], query)
      if (filteredChildren.length > 0) {
        acc.push({
          ...node,
          children: filteredChildren
        })
      }
    }
    return acc
  }, [])
}

// 分页过滤树（只显示当前页的文件）
const filterTreeByPage = (nodes: TreeNode[]): TreeNode[] => {
  return nodes.reduce<TreeNode[]>((acc, node) => {
    if (node.type === 'file') {
      if (paginatedFiles.value.has(node.path)) {
        acc.push({ ...node })
      }
    } else {
      const filteredChildren = filterTreeByPage(node.children || [])
      if (filteredChildren.length > 0) {
        acc.push({
          ...node,
          children: filteredChildren
        })
      }
    }
    return acc
  }, [])
}

// 供 el-tree 使用的过滤方法
const filterNode = (value: string, data: TreeNode) => {
  if (!value) return true
  if (data.type === 'file') {
    return (
        data.name.toLowerCase().includes(value.toLowerCase()) ||
        data.path.toLowerCase().includes(value.toLowerCase()) ||
        (data.title && data.title.toLowerCase().includes(value.toLowerCase()))
    )
  }
  return false
}

const handleSearch = () => {
  currentPage.value = 1
  nextTick(() => {
    if (treeRef.value) {
      treeRef.value.filter(searchQuery.value)
    }
  })
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const refreshList = async () => {
  await fetchPostTree()
}

const fetchPostTree = async () => {
  loading.value = true
  try {

    const res = await getPostTree()
    rawTree.value = res.items
    totalFiles.value = res.total
    currentPage.value = 1
  } catch (err) {
    ElMessage.error('获取文章列表失败')
    rawTree.value = []
    totalFiles.value = 0
  } finally {
    loading.value = false
  }
}

const goToEditor = (path: string) => {
  router.push(`/editor/${encodeURIComponent(path)}`)
}

const handleDelete = async (path: string) => {
  try {
    buttonLoading.value = true
    await ElMessageBox.confirm(`确定删除文章 "${path}"？`, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })

    await deleteArticle(path)
    ElMessage.success('删除成功')
    await fetchPostTree()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }finally {
    buttonLoading.value = false
  }
}

onMounted(() => {
  fetchPostTree()
})
</script>

<style scoped>
.posts-container {
  padding: 20px;
}

.posts-header {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
}

.tree-node-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;          /*  替换 width: 100% */
  min-width: 0;     /*  防止文本溢出 */
  padding: 4px 0;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.node-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  margin-left: 10px;
}

.date {
  color: #999;
}

.node-actions {
  display: flex;
  gap: 4px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.custom-tree {
  background: #fafafa;
  padding: 16px;
  border-radius: 4px;
  min-height: 400px;
}

:deep(.el-tree-node__content) {
  height: auto !important;
  /*padding: 8px 0 !important;*/
  padding-top: 8px !important;    /* ✅ 只保留上下 */
  padding-bottom: 8px !important; /* ✅ 不动左右 */
}

:deep(.el-icon-folder),
:deep(.el-icon-document) {
  font-size: 16px;
}
</style>