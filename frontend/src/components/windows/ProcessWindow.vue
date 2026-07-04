<template>
  <div style="display:flex; flex-direction:column; height:100%;">
    <div class="toolbar">
      <button class="btn" @click="refresh">刷新</button>
      <label style="font-size:11px;color:#0a3d7a;">排序：</label>
      <select v-model="sortBy" @change="refresh" style="font-size:11px;">
        <option value="cpu">CPU</option>
        <option value="memory">内存</option>
        <option value="pid">PID</option>
        <option value="name">名称</option>
      </select>
      <input type="text" v-model="filter" placeholder="过滤进程名..." style="max-width:200px;" />
      <span v-if="loading" style="margin-left:auto;color:#888;">加载中...</span>
      <span v-else style="margin-left:auto;color:#888;">共 {{ filteredList.length }} 项</span>
    </div>
    <div style="flex:1; overflow:auto;">
      <table class="dt">
        <thead>
          <tr>
            <th style="width:70px;">PID</th>
            <th>名称</th>
            <th style="width:120px;">用户</th>
            <th style="width:80px;">状态</th>
            <th style="width:80px;">CPU%</th>
            <th style="width:100px;">内存</th>
            <th style="width:140px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filteredList" :key="p.pid">
            <td>{{ p.pid }}</td>
            <td>{{ p.name }}</td>
            <td>{{ p.username }}</td>
            <td>{{ p.status }}</td>
            <td>{{ p.cpu.toFixed(1) }}</td>
            <td>{{ formatBytes(p.memory) }}</td>
            <td>
              <button class="btn" @click="kill(p.pid, false)">结束</button>
              <button class="btn danger" @click="kill(p.pid, true)">强制</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { processApi, formatBytes } from '../../api'

const list = ref([])
const sortBy = ref('cpu')
const filter = ref('')
const loading = ref(false)
let timer = null

const filteredList = computed(() => {
  if (!filter.value) return list.value
  const q = filter.value.toLowerCase()
  return list.value.filter(p => p.name.toLowerCase().includes(q) || String(p.pid).includes(q))
})

async function refresh() {
  loading.value = true
  try {
    list.value = await processApi.list(sortBy.value, 300)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function kill(pid, force) {
  if (!confirm(`确认${force ? '强制' : ''}结束进程 ${pid}？`)) return
  try {
    await processApi.kill(pid, force)
    await refresh()
  } catch (e) {
    alert('操作失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 3000)
})
onUnmounted(() => clearInterval(timer))
</script>
