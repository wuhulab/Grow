<template>
  <div class="desktop">
    <div class="desktop-content">
      <!-- Shortcuts -->
      <div class="shortcuts">
        <div
          v-for="sc in shortcuts"
          :key="sc.key"
          class="shortcut"
          :class="{ selected: selected === sc.key }"
          @click="selected = sc.key"
          @dblclick="openWindow(sc.key)"
        >
          <div class="icon"><component :is="sc.icon" :size="32" /></div>
          <div class="label">{{ sc.label }}</div>
        </div>
      </div>

      <!-- Spacer (center) -->
      <div></div>

      <!-- Right cards -->
      <div class="right-cards">
        <RingCard :overview="overview" />
        <MonitorCard />
        <InfoNotesCard />
      </div>
    </div>

    <!-- Windows -->
    <WindowFrame
      v-for="w in openWindows"
      :key="w.id"
      :window="w"
      :active="activeWindowId === w.id"
      @focus="focusWindow(w.id)"
      @close="closeWindow(w.id)"
      @minimize="minimizeWindow(w.id)"
      @maximize="toggleMaximize(w.id)"
      @move="(x, y) => moveWindow(w.id, x, y)"
      @resize="(width, height) => resizeWindow(w.id, width, height)"
    >
      <component :is="w.component" />
    </WindowFrame>

    <!-- Dock -->
    <div class="taskbar">
      <div class="start-button" title="Launchpad"><LayoutGrid :size="22" /></div>
      <div class="task-items">
        <div
          v-for="w in openWindows"
          :key="w.id"
          class="task-item"
          :class="{ active: activeWindowId === w.id && !w.minimized }"
          @click="taskClick(w.id)"
        >
          <span class="icon"><component :is="w.icon" :size="20" /></span>
          <span class="title">{{ w.title }}</span>
        </div>
      </div>
      <div class="clock">
        <div>{{ clockTime }}</div>
        <div>{{ clockDate }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, shallowRef, markRaw } from 'vue'
import RingCard from './components/cards/RingCard.vue'
import MonitorCard from './components/cards/MonitorCard.vue'
import InfoNotesCard from './components/cards/InfoNotesCard.vue'
import WindowFrame from './components/WindowFrame.vue'
import DockerWindow from './components/windows/DockerWindow.vue'
import ProcessWindow from './components/windows/ProcessWindow.vue'
import FilesWindow from './components/windows/FilesWindow.vue'
import TerminalWindow from './components/windows/TerminalWindow.vue'
import { systemApi } from './api'
import { Container, Settings, Folder, Terminal, LayoutGrid } from 'lucide-vue-next'

const shortcuts = [
  { key: 'docker', label: 'Docker', icon: markRaw(Container), component: markRaw(DockerWindow), w: 820, h: 520 },
  { key: 'process', label: '进程管理', icon: markRaw(Settings), component: markRaw(ProcessWindow), w: 780, h: 520 },
  { key: 'files', label: '文件管理', icon: markRaw(Folder), component: markRaw(FilesWindow), w: 820, h: 540 },
  { key: 'terminal', label: '终端', icon: markRaw(Terminal), component: markRaw(TerminalWindow), w: 780, h: 460 }
]

const selected = ref(null)
const openWindows = ref([])
const activeWindowId = ref(null)
let windowSeq = 0
let zSeq = 100

function openWindow(key) {
  const def = shortcuts.find(s => s.key === key)
  if (!def) return
  const existing = openWindows.value.find(w => w.key === key)
  if (existing) {
    existing.minimized = false
    focusWindow(existing.id)
    return
  }
  const id = ++windowSeq
  const w = reactive({
    id,
    key,
    title: def.label,
    icon: def.icon,
    component: def.component,
    x: 140 + (openWindows.value.length * 30),
    y: 60 + (openWindows.value.length * 25),
    width: def.w,
    height: def.h,
    z: ++zSeq,
    minimized: false,
    maximized: false,
    prev: null
  })
  openWindows.value.push(w)
  activeWindowId.value = id
}

function focusWindow(id) {
  const w = openWindows.value.find(x => x.id === id)
  if (!w) return
  w.z = ++zSeq
  w.minimized = false
  activeWindowId.value = id
}

function closeWindow(id) {
  openWindows.value = openWindows.value.filter(w => w.id !== id)
  if (activeWindowId.value === id) activeWindowId.value = null
}

function minimizeWindow(id) {
  const w = openWindows.value.find(x => x.id === id)
  if (w) w.minimized = true
}

function toggleMaximize(id) {
  const w = openWindows.value.find(x => x.id === id)
  if (!w) return
  if (w.maximized) {
    Object.assign(w, w.prev)
    w.maximized = false
    w.prev = null
  } else {
    w.prev = { x: w.x, y: w.y, width: w.width, height: w.height }
    w.x = 0
    w.y = 0
    w.width = window.innerWidth
    w.height = window.innerHeight - 90
    w.maximized = true
  }
}

function moveWindow(id, x, y) {
  const w = openWindows.value.find(v => v.id === id)
  if (w) { w.x = x; w.y = y }
}

function resizeWindow(id, width, height) {
  const w = openWindows.value.find(v => v.id === id)
  if (w) { w.width = width; w.height = height }
}

function taskClick(id) {
  const w = openWindows.value.find(x => x.id === id)
  if (!w) return
  if (w.minimized) {
    w.minimized = false
    focusWindow(id)
  } else if (activeWindowId.value === id) {
    w.minimized = true
  } else {
    focusWindow(id)
  }
}

// Overview polling
const overview = ref({
  cpu: 0,
  memory: { percent: 0, total: 0, used: 0 },
  storage: { percent: 0, total: 0, used: 0 },
  load: { percent: 0, load1: 0 }
})
let overviewTimer = null
async function refreshOverview() {
  try { overview.value = await systemApi.overview() } catch (e) { /* ignore */ }
}

// Clock
const clockTime = ref('')
const clockDate = ref('')
let clockTimer = null
function updateClock() {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  clockTime.value = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  clockDate.value = `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())}`
}

onMounted(() => {
  refreshOverview()
  overviewTimer = setInterval(refreshOverview, 2000)
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  clearInterval(overviewTimer)
  clearInterval(clockTimer)
})
</script>
