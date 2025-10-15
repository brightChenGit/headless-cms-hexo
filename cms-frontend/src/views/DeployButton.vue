<!-- src/components/DeployButton.vue -->
<template>
  <el-button type="primary" @click="openStatusDialog">
    部署
  </el-button>

  <el-dialog
      v-model="dialogVisible"
      title="当前部署状态"
      width="500px"
      @closed="handleDialogClose"
  >
    <el-descriptions :column="1" size="small" v-if="statusData">
      <el-descriptions-item label="状态">
        <el-tag :type="statusTagType" size="small">
          {{ statusText }}
        </el-tag>
      </el-descriptions-item>

      <el-descriptions-item label="创建时间" v-if="statusData.created_at">
        {{ formatDate(statusData.created_at) }}
      </el-descriptions-item>

      <el-descriptions-item label="总体消息">
        {{ statusData.message || '—' }}
      </el-descriptions-item>
    </el-descriptions>

    <el-divider v-if="statusData?.steps?.length" />

    <div v-if="statusData?.steps?.length">
      <h4 style="margin: 12px 0">执行步骤</h4>
      <el-timeline>
        <el-timeline-item
            v-for="(step, index) in statusData.steps"
            :key="index"
            :type="getStepType(step.status)"
            :hollow="step.status === 'pending'"
            :dot="step.status === 'running' ? '🔄' : undefined"
        >
          <strong>{{ step.name }}</strong>
          <div style="margin-top: 4px; color: #666">{{ step.message || '—' }}</div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleDialogClose">取消</el-button>
        <el-button
            type="warning"
            :disabled="!canDeploy"
            :loading="deployLoading"
            @click="handleDeploy"
        >
          {{ canDeploy ? '重新部署' : '部署中，无法操作' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue';
import {ElMessage, ElNotification} from 'element-plus';
import { getDeployStatus,deployHexo as triggerDeploy } from '@/api/cms';
import type { DeployStatusResponse } from '@/types/deployTask';

const dialogVisible = ref(false);
const statusData = ref<DeployStatusResponse | null>(null);
const deployLoading = ref(false);

// 打开弹窗并加载状态
const openStatusDialog = async () => {
  dialogVisible.value = true;
  await fetchStatus();
  startPolling();
};

// 获取最新状态
const fetchStatus = async () => {
  try {
    const res = await getDeployStatus(undefined);
    if (res.data && typeof res.data === 'object') {
      statusData.value = {
        task_id: (res.data as any).task_id ?? null,
        status: (res.data as any).status ?? '',
        message: (res.data as any).message ?? '',
        triggered_by: (res.data as any).triggered_by ?? 'unknown',
        created_at: (res.data as any).created_at ?? null,
        steps: (res.data as any).steps ?? [],
        can_deploy: (res.data as any).can_deploy
      } as DeployStatusResponse;
    }

  } catch (err) {
    console.error('获取部署状态失败', err);
    if (!statusData.value) {
      statusData.value = {
        task_id: null,
        status: '',
        message: '加载失败',
        triggered_by: '',
        steps: [],
        created_at: null,
      };
    }
  }
};

// 轮询控制
const isPolling = ref(false);

// 开始轮询（每 2 秒，成功/失败时自动停止）
const startPolling = () => {
  if (isPolling.value) return; // 防止重复启动

  const poll = async () => {
    isPolling.value = true;

    try {
      await fetchStatus();

      const currentStatus = statusData.value?.status;
      // 如果是终态，停止轮询
      if (currentStatus === 'success' || currentStatus === 'failure') {
        isPolling.value = false;
        return;
      }

      // 否则 2 秒后继续
      if (dialogVisible.value && isPolling.value) {
        setTimeout(poll, 2000);
      }
    } catch (err) {
      console.error('轮询状态失败', err);
      // 出错后也继续轮询（可选：也可停止）
      if (dialogVisible.value) {
        setTimeout(poll, 2000);
      } else {
        isPolling.value = false;
      }
    }
  };

  poll();
};

// 停止轮询（供手动关闭使用）
const stopPolling = () => {
  isPolling.value = false;
};


// 监听状态变化：如果变成 success/failure，可考虑提示用户（可选）
watch(
    () => statusData.value?.status,
    (newStatus) => {
      if (newStatus === 'success' || newStatus === 'failure') {
        // 可选：弹出通知
        ElNotification.success('部署已完成');
      }
    }
);

// 是否允许部署
const canDeploy = computed(() => {
  const s = statusData.value?.status;
  return s === '' || s === 'success' || s === 'failure';
});

// 状态文本 & 标签类型（略，同前）
const statusText = computed(() => {
  const map: Record<string, string> = {
    '': '无部署记录',
    queued: '排队中',
    running: '部署中',
    success: '成功',
    failure: '失败',
  };
  return map[statusData.value?.status || ''] || '未知';
});

const statusTagType = computed(() => {
  const s = statusData.value?.status;
  if (s === 'success') return 'success';
  if (s === 'failure') return 'danger';
  if (s === 'running' || s === 'queued') return 'warning';
  return 'info';
});

const getStepType = (status: string) => {
  if (status === 'success') return 'success';
  if (status === 'failure') return 'danger';
  return 'info';
};

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('zh-CN');
};

// 确认部署
const handleDeploy = async () => {
  if (!canDeploy.value) return;
  deployLoading.value = true;
  try {
    const res = await triggerDeploy();
    ElMessage.success(`部署已启动，任务ID: ${res.task_id}`);
    // 自动刷新状态（新任务）
    await fetchStatus();
  } catch (err: any) {
    ElMessage.error('部署失败：' + (err.response?.data?.detail || '未知错误'));
  } finally {
    deployLoading.value = false;
  }
};

// 关闭弹窗时停止轮询
const handleDialogClose = () => {
  dialogVisible.value = false;
  stopPolling();
};

// 组件卸载时清理（防止内存泄漏）
onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>