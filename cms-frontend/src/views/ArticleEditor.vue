<!-- src/views/ArticleEditor.vue -->
<template>
  <div class="editor-container">
    <div class="editor-header">
      <el-button @click="goBack">返回</el-button>
      <el-button type="primary" @click="saveArticle" :loading="loading" :disabled="loading">保存</el-button>
      <span class="path-display">{{ filePathInput || '新建文章' }}</span>
    </div>
    <!-- 路径输入 -->
    <div class="editor-path-input editor-header">
      <label class="path-label">文章路径：</label>
      <el-input
          v-model="filePathInput"
          placeholder="请输入文件路径，如：posts/hello.md"
          :disabled= "!isPathEditable"
          clearable
          style="width: 400px;"
      />
      <span v-if="!isNew && isPathEditable" class="path-tip">（可修改路径）</span>
    </div>
    <div class="bytemd-wrapper">
      <!-- 可选: tab, split, editor, preview -->

      <Editor :value="content"
              placeholder="请输入 Markdown 内容..."
              :plugins="plugins" :mode="'split'" @change="handleChange" @save="handleSave" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {getArticleContent, saveArticle as apiSaveArticle} from '@/api/cms'
import { ElMessage } from 'element-plus'

// Bytemd 相关
// @ts-ignore 忽略ts单行检查
import  { Editor } from '@bytemd/vue-next'

import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'
import breaks from '@bytemd/plugin-breaks'
import frontmatter from '@bytemd/plugin-frontmatter'
import mermaidPlugin from '@bytemd/plugin-mermaid'

import 'bytemd/dist/index.css'
import 'highlight.js/styles/github.css' // 代码高亮主题

const plugins = [
  gfm(),
  highlight(),
  breaks(),
  frontmatter(),
  mermaidPlugin(),
  // 可添加更多插件
]

const router = useRouter()
const route = useRoute()
const content = ref('')
const loading=ref(false)

const filePathInput = ref<string>('')
const isNew = ref<boolean>(false)
const isPathEditable = ref<boolean>(false) // 设为 true 可允许编辑路径
const handleChange = (v: string) => {
  content.value = v
}
onMounted(async () => {

  // 优化：从 fullPath 截取 /editor 之后的内容
  const fullPath = route.fullPath
  const editorPrefix = '/editor'

  let extractedPath = ''
  if (fullPath.startsWith(editorPrefix)) {
    extractedPath = fullPath.slice(editorPrefix.length) || 'new'
    // 解码 URL 编码
    try {
      extractedPath = decodeURIComponent(extractedPath)
    } catch (e) {
      console.warn('URL 解码失败，使用原始路径:', extractedPath)
      // 解码失败也继续，避免崩溃
    }

    if (extractedPath.startsWith('/')) {
      extractedPath = extractedPath.slice(1)
    }
    if (!extractedPath || extractedPath === '/') {
      extractedPath = 'new'
    }
  } else {
    extractedPath = 'new'
  }

  if (extractedPath === 'new') {
    isNew.value = true
    isPathEditable.value= true
  } else {
    filePathInput.value = extractedPath
    isNew.value = false
    isPathEditable.value= false
    try {
      const res = await getArticleContent(filePathInput.value)
      filePathInput.value = res.path
      content.value = res.body
    } catch (err) {
      ElMessage.error('获取文章失败')
    } finally {

    }
  }
})

const goBack = () => {
  router.push('/posts')
}

const handleSave = () => {
  saveArticle()
}

function getTitle(path:string) {
  return path.split('/').pop()
}

const saveArticle = async () => {
  try {
    loading.value=true
    let pathToSave = filePathInput.value
    if (isNew.value && !pathToSave) {
      ElMessage.error('请输入文件路径')
      return
    }
    if (isNew.value && !pathToSave.endsWith('.md')) {
      pathToSave += '.md'
    }

    let article={
      "path": pathToSave,
      "title":getTitle(pathToSave),
      "body":content.value
    }

    await apiSaveArticle(article)
    ElMessage.success('保存成功')
    await router.push('/posts')
  } catch (err) {
    ElMessage.error('保存失败')
  }finally {
    loading.value=false;
  }
}



// 获取 /editor 之后的完整路径（包括查询参数、hash，但通常我们不需要）
const fullPath = route.fullPath
const editorPrefix = '/editor'

let path = ''
if (fullPath.startsWith(editorPrefix)) {
  // 截取 /editor 之后的部分
  path = fullPath.slice(editorPrefix.length) || 'new'
  // 解码 URI（处理中文、空格等）
  path = decodeURIComponent(path)
  // 移除开头的斜杠（如果存在）
  if (path.startsWith('/')) {
    path = path.slice(1)
  }
  // 如果路径为空或只有斜杠，视为新建
  if (!path || path === '/') {
    path = 'new'
  }
} else {
  // 非预期路径，重定向或设为新建
  path = 'new'
}
</script>

<style scoped>
.editor-container {
  padding: 20px;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.path-display {
  margin-left: auto;
  font-size: 14px;
  color: #666;
}

.bytemd-wrapper {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

:deep(.bytemd) {
  height: 600px;
}
</style>