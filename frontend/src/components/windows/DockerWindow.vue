<template>
  <div style="display:flex; flex-direction:column; height:100%;">
    <div class="toolbar">
      <button class="btn" @click="refresh">刷新</button>
      <span style="margin-left:8px; color:#0a3d7a;" v-if="status">
        <template v-if="status.available">
          Docker {{ status.server_version }} · 容器 {{ status.containers_running }}/{{ status.containers }} · 镜像 {{ status.images }}
        </template>
        <template v-else>
          Docker 不可用：{{ status.reason }}
        </template>
      </span>
      <span v-if="loading" style="margin-left:auto;color:#888;">加载中...</span>
    </div>
    <div style="flex:1; overflow:auto;">
      <div v-if="status && !status.available" class="empty">
        无法连接到 Docker。请确认 Docker 服务正在运行，并且当前用户具有访问权限。
      </div>
      <table v-else class="dt">
        <thead>
          <tr>
            <th>名称</th>
            <th>镜像</th>
            <th>状态</th>
            <th>端口</th>
            <th style="width:200px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in containers" :key="c.id">
            <td>{{ c.name }}<div style="font-size:10px;color:#888;">{{ c.id }}</div></td>
            <td>{{ c.image }}</td>
            <td><span :style="{ color: c.state === 'running' ? '#2a8f3c' : '#a04040' }">{{ c.state }}</span></td>
            <td style="font-family:monospace;font-size:11px;">{{ c.ports.join(', ') || '-' }}</td>
            <td>
              <button class="btn" v-if="c.state !== 'running'" @click="act(c.id, 'start')">启动</button>
              <button class="btn" v-if="c.state === 'running'" @click="act(c.id, 'stop')">停止</button>
              <button class="btn" v-if="c.state === 'running'" @click="act(c.id, 'restart')">重启</button>
              <button class="btn" @click="showLogs(c.id)">日志</button>
              <button class="btn danger" @click="act(c.id, 'remove')">删除</button>
            </td>
          </tr>
          <tr v-if="!containers.length && status && status.available">
            <td colspan="5"><div class="empty">暂无容器</div></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="logs !== null" style="border-top:1px solid #b0c4de; height:200px; display:flex; flex-direction:column;">
      <div class="toolbar">
        <strong>容器日志</strong>
        <button class="btn" style="margin-left:auto" @click="logs = null">关闭</button>
      </div>
      <pre style="flex:1; overflow:auto; margin:0; padding:8px; font-size:11px; background:#1e1e1e; color:#d4d4d4; font-family:Consolas,monospace;">{{ logs }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { dockerApi } from '../../api'

const status = ref(null)
const containers = ref([])
const logs = ref(null)
const loading = ref(false)
let timer = null

async function refresh() {
  loading.value = true
  try {
    status.value = await dockerApi.status()
    if (status.value.available) {
      containers.value = await dockerApi.containers()
    } else {
      containers.value = []
    }
  } catch (e) {
    status.value = { available: false, reason: e.message }
  } finally {
    loading.value = false
  }
}

async function act(id, action) {
  if (action === 'remove' && !confirm('确认删除该容器？')) return
  try {
    await dockerApi.action(id, action)
    await refresh()
  } catch (e) {
    alert('操作失败：' + (e.response?.data?.detail || e.message))
  }
}

async function showLogs(id) {
  try {
    const r = await dockerApi.logs(id, 300)
    logs.value = r.logs || '(空)'
  } catch (e) {
    alert('获取日志失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 5000)
})
onUnmounted(() => clearInterval(timer))
</script>
