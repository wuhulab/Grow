<template>
  <div class="win7-card" style="display:flex; flex-direction:column;">
    <div class="card-title">
      <span>实时监控</span>
      <div class="tabs">
        <button :class="{ active: mode === 'net' }" @click="mode = 'net'">流量</button>
        <button :class="{ active: mode === 'disk' }" @click="mode = 'disk'">磁盘IO</button>
      </div>
    </div>
    <div class="chart-area">
      <v-chart class="chart" :option="option" autoresize />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { systemApi, formatSpeed } from '../../api'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const mode = ref('net')
const MAX_POINTS = 30

const netSeries = ref({ up: [], down: [], times: [] })
const diskSeries = ref({ read: [], write: [], times: [] })

let timer = null
async function tick() {
  try {
    if (mode.value === 'net') {
      const d = await systemApi.network()
      const t = new Date(d.timestamp).toLocaleTimeString().slice(0, 8)
      netSeries.value.times.push(t)
      netSeries.value.up.push(d.upload)
      netSeries.value.down.push(d.download)
      if (netSeries.value.times.length > MAX_POINTS) {
        netSeries.value.times.shift(); netSeries.value.up.shift(); netSeries.value.down.shift()
      }
    } else {
      const d = await systemApi.diskio()
      const t = new Date(d.timestamp).toLocaleTimeString().slice(0, 8)
      diskSeries.value.times.push(t)
      diskSeries.value.read.push(d.read)
      diskSeries.value.write.push(d.write)
      if (diskSeries.value.times.length > MAX_POINTS) {
        diskSeries.value.times.shift(); diskSeries.value.read.shift(); diskSeries.value.write.shift()
      }
    }
  } catch (e) { /* ignore */ }
}

onMounted(() => { tick(); timer = setInterval(tick, 2000) })
onUnmounted(() => clearInterval(timer))

const option = computed(() => {
  const isNet = mode.value === 'net'
  const s = isNet ? netSeries.value : diskSeries.value
  const a = isNet ? s.up : s.read
  const b = isNet ? s.down : s.write
  const nameA = isNet ? '上传' : '读取'
  const nameB = isNet ? '下载' : '写入'
  return {
    grid: { left: 50, right: 12, top: 24, bottom: 22 },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        return params.map(p => `${p.marker}${p.seriesName}: ${formatSpeed(p.value)}`).join('<br/>')
      }
    },
    legend: { top: 0, right: 8, textStyle: { fontSize: 10 }, itemHeight: 8, itemWidth: 12 },
    xAxis: {
      type: 'category',
      data: s.times,
      axisLabel: { fontSize: 9, color: '#0a3d7a' },
      axisLine: { lineStyle: { color: '#9bb5d8' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 9,
        color: '#0a3d7a',
        formatter: v => formatSpeed(v)
      },
      splitLine: { lineStyle: { color: 'rgba(155,181,216,0.4)' } }
    },
    series: [
      {
        name: nameA, type: 'line', smooth: true, showSymbol: false,
        data: a, areaStyle: { opacity: 0.3, color: '#409eff' },
        lineStyle: { width: 1.5, color: '#409eff' }, itemStyle: { color: '#409eff' }
      },
      {
        name: nameB, type: 'line', smooth: true, showSymbol: false,
        data: b, areaStyle: { opacity: 0.3, color: '#67c23a' },
        lineStyle: { width: 1.5, color: '#67c23a' }, itemStyle: { color: '#67c23a' }
      }
    ]
  }
})
</script>

<style scoped>
.chart { width: 100%; height: 100%; min-height: 80px; }
</style>
