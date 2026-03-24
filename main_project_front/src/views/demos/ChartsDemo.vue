<template>
  <section class="charts-demo">
    <header class="charts-demo__head">
      <h2>趋势图示</h2>
      <p>柱状图展示周访问量，折线图展示转化率变化</p>
    </header>

    <div class="charts-demo__grid">
      <AppCard title="周访问量（柱状）">
        <div class="bars" role="img" aria-label="周访问量柱状图">
          <div v-for="item in barData" :key="item.day" class="bars__item">
            <div class="bars__col" :style="{ height: `${item.value}%` }"></div>
            <span class="bars__label">{{ item.day }}</span>
          </div>
        </div>
      </AppCard>

      <AppCard title="转化率（折线）">
        <svg class="line-chart" viewBox="0 0 360 180" role="img" aria-label="转化率折线图">
          <polyline class="line-chart__line" :points="linePoints" />
          <g v-for="point in points" :key="point.x">
            <circle class="line-chart__dot" :cx="point.x" :cy="point.y" r="4" />
          </g>
        </svg>
        <div class="line-chart__xlabels">
          <span v-for="item in lineData" :key="item.label">{{ item.label }}</span>
        </div>
      </AppCard>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppCard from '../../components/AppCard.vue'

const barData = [
  { day: 'Mon', value: 45 },
  { day: 'Tue', value: 62 },
  { day: 'Wed', value: 50 },
  { day: 'Thu', value: 78 },
  { day: 'Fri', value: 71 },
  { day: 'Sat', value: 58 },
  { day: 'Sun', value: 83 }
]

const lineData = [
  { label: '1月', value: 28 },
  { label: '2月', value: 35 },
  { label: '3月', value: 41 },
  { label: '4月', value: 38 },
  { label: '5月', value: 49 },
  { label: '6月', value: 54 }
]

const points = computed(() => {
  const maxValue = Math.max(...lineData.map((item) => item.value))
  const minValue = Math.min(...lineData.map((item) => item.value))
  const width = 320
  const height = 120

  return lineData.map((item, index) => {
    const x = 20 + (index * width) / (lineData.length - 1)
    const ratio = (item.value - minValue) / (maxValue - minValue || 1)
    const y = 20 + (1 - ratio) * height
    return { x, y }
  })
})

const linePoints = computed(() => points.value.map((point) => `${point.x},${point.y}`).join(' '))
</script>

<style scoped>
.charts-demo {
  display: grid;
  gap: var(--space-4);
}

.charts-demo__head h2 {
  margin: 0;
  color: var(--text-primary);
}

.charts-demo__head p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.charts-demo__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(260px, 1fr));
  gap: var(--space-4);
}

.bars {
  height: 200px;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  align-items: end;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-soft);
  background: var(--bg-surface-muted);
}

.bars__item {
  text-align: center;
}

.bars__col {
  width: 100%;
  border-radius: 8px 8px 3px 3px;
  background: #1b1b1b;
}

.bars__label {
  margin-top: 7px;
  display: block;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.line-chart {
  width: 100%;
  min-height: 180px;
  background: var(--bg-surface-muted);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
}

.line-chart__line {
  fill: none;
  stroke: #1b1b1b;
  stroke-width: 3;
}

.line-chart__dot {
  fill: var(--bg-surface);
  stroke: #1b1b1b;
  stroke-width: 2;
}

.line-chart__xlabels {
  margin-top: var(--space-2);
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  color: var(--text-muted);
  font-size: 0.82rem;
  text-align: center;
}

@media (max-width: 900px) {
  .charts-demo__grid {
    grid-template-columns: 1fr;
  }
}
</style>
