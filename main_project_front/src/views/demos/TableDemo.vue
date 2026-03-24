<template>
  <section class="table-demo">
    <header class="table-demo__head">
      <h2>表格示例</h2>
      <p>支持关键词过滤的 mock 列表</p>
    </header>

    <AppCard title="订单列表" description="按姓名、城市或状态检索">
      <div class="table-demo__tools">
        <input
          v-model.trim="keyword"
          type="text"
          placeholder="输入关键词：例如 北京 / 已完成 / 陈"
          aria-label="关键词过滤"
        />
        <p>共 {{ filteredList.length }} 条</p>
      </div>

      <div class="table-demo__table-wrap">
        <table class="table-demo__table">
          <thead>
            <tr>
              <th>ID</th>
              <th>客户</th>
              <th>城市</th>
              <th>金额</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredList" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.customer }}</td>
              <td>{{ item.city }}</td>
              <td>¥{{ item.amount.toLocaleString() }}</td>
              <td>
                <span class="table-demo__status" :class="`is-${item.status}`">{{ statusText[item.status] }}</span>
              </td>
            </tr>
            <tr v-if="filteredList.length === 0">
              <td colspan="5" class="table-demo__empty">没有匹配结果</td>
            </tr>
          </tbody>
        </table>
      </div>
    </AppCard>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import AppCard from '../../components/AppCard.vue'

type Status = 'done' | 'pending' | 'processing'

type Row = {
  id: string
  customer: string
  city: string
  amount: number
  status: Status
}

const keyword = ref('')

const statusText: Record<Status, string> = {
  done: '已完成',
  pending: '待付款',
  processing: '处理中'
}

const rows: Row[] = [
  { id: 'A-1001', customer: '陈若安', city: '上海', amount: 2680, status: 'done' },
  { id: 'A-1002', customer: 'Mia Rossi', city: '广州', amount: 1590, status: 'processing' },
  { id: 'A-1003', customer: '石川遥', city: '北京', amount: 4820, status: 'pending' },
  { id: 'A-1004', customer: '刘奕晨', city: '深圳', amount: 3260, status: 'done' },
  { id: 'A-1005', customer: 'Sofia Diaz', city: '杭州', amount: 2190, status: 'processing' }
]

const filteredList = computed(() => {
  const key = keyword.value.toLowerCase()
  if (!key) return rows

  return rows.filter((item) => {
    const text = `${item.id} ${item.customer} ${item.city} ${statusText[item.status]}`.toLowerCase()
    return text.includes(key)
  })
})
</script>

<style scoped>
.table-demo {
  display: grid;
  gap: var(--space-4);
}

.table-demo__head h2 {
  margin: 0;
  color: var(--text-primary);
}

.table-demo__head p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.table-demo__tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.table-demo__tools input {
  width: min(400px, 100%);
}

.table-demo__tools p {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.table-demo__table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
}

.table-demo__table {
  width: 100%;
  border-collapse: collapse;
  min-width: 620px;
}

.table-demo__table th,
.table-demo__table td {
  padding: 12px;
  border-bottom: 1px solid var(--border-soft);
  text-align: left;
  color: var(--text-secondary);
}

.table-demo__table thead th {
  background: var(--bg-surface-muted);
  color: var(--text-secondary);
  font-size: 0.86rem;
}

.table-demo__status {
  display: inline-block;
  border-radius: 999px;
  font-size: 0.78rem;
  padding: 4px 10px;
  border: 1px solid transparent;
}

.table-demo__status.is-done {
  color: var(--success-500);
  background: #f1f8f4;
  border-color: #cfe4d8;
}

.table-demo__status.is-pending {
  color: var(--warning-500);
  background: #fbf6ed;
  border-color: #e8dbc1;
}

.table-demo__status.is-processing {
  color: var(--text-secondary);
  background: #f2f2f2;
  border-color: #dddddd;
}

.table-demo__empty {
  text-align: center;
  color: var(--text-muted);
}

@media (max-width: 680px) {
  .table-demo__tools {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
