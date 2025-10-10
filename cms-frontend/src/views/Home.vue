<template>
  <div class="home-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>系统配置</span>
        </div>
      </template>

      <el-form
          :model="form"
          label-width="120px"
          :rules="rules"
          ref="formRef"
          status-icon
      >
        <el-form-item label="Git 仓库地址" prop="gitUrl">
          <el-input
              v-model="form.gitUrl"
              placeholder="可选，留空则使用默认或本地仓库"
          />
        </el-form-item>

        <el-form-item label="Git 分支" prop="branch">
          <el-input
              v-model="form.branch"
              placeholder="可选，默认 main 或 master"
          />
        </el-form-item>

        <el-form-item label="后端 API 地址" prop="apiUrl">
          <el-input
              v-model="form.apiUrl"
              placeholder="如：http://localhost:8000 或 https://yourdomain.com/api"
          />
        </el-form-item>

        <el-form-item label="访问 Token" prop="token">
          <el-input
              v-model="form.token"
              type="password"
              placeholder="用于后端认证的固定 Token"
              show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
              type="primary"
              @click="saveConfig"
              :loading="loading"
              :disabled="loading"
          >
            保存配置
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert
        v-if="saved"
        title="配置已保存"
        type="success"
        show-icon
        :closable="false"
        style="margin-top: 20px;"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useConfigStore } from '@/stores/pinia-config'
import type { FormInstance, FormRules } from 'element-plus'

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive({
  gitUrl: '',
  branch: '',
  apiUrl: '',
  token: ''
})

//  自定义校验器：可选 URL
const validateOptionalUrl = (
    _rule: any,
    value: string,
    callback: (error?: Error) => void
) => {
  if (!value || value.trim() === '') {
    callback() // 空值合法
  } else {
    try {
      new URL(value)
      callback()
    } catch {
      callback(new Error('请输入合法的 URL 地址'))
    }
  }
}

//  自定义校验器：可选长度
const validateOptionalLength = (
    min: number,
    max: number,
    message: string
) => {
  return (
      _rule: any,
      value: string,
      callback: (error?: Error) => void
  ) => {
    if (!value || value.trim() === '') {
      callback() // 空值合法
    } else if (value.length < min || value.length > max) {
      callback(new Error(message))
    } else {
      callback()
    }
  }
}

// 表单验证规则
const rules = reactive<FormRules>({
  gitUrl: [
    {
      validator: validateOptionalUrl,
      trigger: ['blur', 'change']
    }
  ],
  branch: [
    {
      validator: validateOptionalLength(1, 50, '分支名称长度应在 1 到 50 个字符之间'),
      trigger: 'blur'
    }
  ],
  apiUrl: [
    {
      required: true,
      message: '请输入后端 API 地址',
      trigger: 'blur'
    },
    {
      validator: validateOptionalUrl,
      trigger: ['blur', 'change']
    }
  ],
  token: [
    {
      required: true,
      message: '请输入访问 Token',
      trigger: 'blur'
    },
    {
      validator: (_rule, value, callback) => {
        if (!value || value.trim() === '') {
          callback(new Error('Token 不能为空'))
        } else if (value.length < 5) {
          callback(new Error('Token 至少 5 位'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

// 加载状态 & 保存成功状态
const loading = ref(false)
const saved = ref(false)

// Pinia Store
const configStore = useConfigStore()

// 初始化表单数据（从 store 加载）
onMounted(() => {
  form.gitUrl = configStore.gitUrl || ''
  form.branch = configStore.branch || ''
  form.apiUrl = configStore.apiUrl || ''
  form.token = configStore.token || ''
})

// 保存配置
const saveConfig = async () => {
  if (!formRef.value) return

  try {
    // 第一步：验证表单
    await formRef.value.validate()

    // 验证通过，开始保存
    loading.value = true

    try {
      // 保存到 Pinia（会自动持久化到 localStorage）
      configStore.setConfig({
        gitUrl: form.gitUrl.trim(),
        branch: form.branch.trim(),
        apiUrl: form.apiUrl.trim(),
        token: form.token.trim()
      })

      saved.value = true
      ElMessage.success('配置保存成功！')

      // 5秒后隐藏提示
      setTimeout(() => {
        saved.value = false
      }, 5000)
    } catch (error) {
      ElMessage.error('保存失败，请重试')
      console.error(error)
    } finally {
      loading.value = false
    }
  } catch (error) {
    // 表单验证失败
    ElMessage.warning('请检查表单内容')
    console.warn('表单验证失败:', error)
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
}
</script>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
}

.config-card {
  border-radius: 8px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.el-form {
  margin-top: 20px;
}

.el-form-item {
  margin-bottom: 24px;
}
</style>