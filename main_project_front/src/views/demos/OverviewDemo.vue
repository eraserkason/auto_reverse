<template>
  <section class="overview-demo">
    <header class="overview-demo__head">
      <h2>项目总览</h2>
      <p>今日核心指标与最近活动</p>
    </header>

    <div class="overview-demo__stats">
      <StatCard label="活跃用户" value="12,480" :trend="8" />
      <StatCard label="新增订单" value="536" :trend="5" />
      <StatCard label="成功率" value="98.6%" :trend="1" />
      <StatCard label="待处理工单" value="27" :trend="-12" />
    </div>

    <AppCard title="最新活动" description="按时间倒序展示团队动态">
      <ul class="overview-demo__activities">
        <li v-for="item in activities" :key="item.id" class="overview-demo__activity">
          <p class="overview-demo__activity-title">{{ item.title }}</p>
          <p class="overview-demo__activity-desc">{{ item.desc }}</p>
          <time class="overview-demo__activity-time">{{ item.time }}</time>
        </li>
      </ul>
    </AppCard>
  </section>
</template>

<script setup lang="ts">
import AppCard from '../../components/AppCard.vue'
import StatCard from '../../components/StatCard.vue'

const activities = [
  { id: 1, title: '部署完成', desc: '支付模块 v2.4 已发布到生产环境', time: '10:22' },
  { id: 2, title: '客户反馈', desc: '渠道合作方提交了 3 条可用性建议', time: '09:45' },
  { id: 3, title: '任务关闭', desc: '报表导出性能优化任务已验收', time: '昨天 18:30' },
  { id: 4, title: '监控预警', desc: 'CDN 节点延迟异常已自动恢复', time: '昨天 16:12' }
]
</script>

<style scoped>
.overview-demo {
  display: grid;
  gap: var(--space-4);
}

.overview-demo__head h2 {
  margin: 0;
  color: var(--text-primary);
}

.overview-demo__head p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.overview-demo__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(160px, 1fr));
  gap: var(--space-3);
}

.overview-demo__activities {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--space-3);
}

.overview-demo__activity {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
  background: var(--bg-surface-muted);
}

.overview-demo__activity-title {
  margin: 0;
  font-weight: 600;
  color: var(--text-primary);
}

.overview-demo__activity-desc {
  margin: 6px 0;
  color: var(--text-secondary);
}

.overview-demo__activity-time {
  color: var(--text-muted);
  font-size: 0.84rem;
}

@media (max-width: 960px) {
  .overview-demo__stats {
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }
}

@media (max-width: 560px) {
  .overview-demo__stats {
    grid-template-columns: 1fr;
  }
}
</style>
