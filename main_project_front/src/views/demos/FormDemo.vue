<template>
  <section class="form-demo">
    <header class="form-demo__head">
      <h2>表单示例</h2>
      <p>包含基础校验和提交成功提示</p>
    </header>

    <AppCard title="新建联系人" description="请填写必填字段后提交">
      <form class="form-demo__form" @submit.prevent="onSubmit">
        <label>
          姓名
          <input v-model.trim="form.name" type="text" placeholder="例如：林晓晨" />
          <span v-if="errors.name" class="form-demo__error">{{ errors.name }}</span>
        </label>

        <label>
          邮箱
          <input v-model.trim="form.email" type="email" placeholder="name@example.com" />
          <span v-if="errors.email" class="form-demo__error">{{ errors.email }}</span>
        </label>

        <label>
          备注
          <textarea v-model.trim="form.note" rows="4" placeholder="输入 10 字以上备注"></textarea>
          <span v-if="errors.note" class="form-demo__error">{{ errors.note }}</span>
        </label>

        <button type="submit">提交</button>

        <p v-if="success" class="form-demo__success">提交成功，数据已通过基础校验。</p>
      </form>
    </AppCard>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import AppCard from '../../components/AppCard.vue'

const form = reactive({
  name: '',
  email: '',
  note: ''
})

const errors = reactive({
  name: '',
  email: '',
  note: ''
})

const success = ref(false)

const isEmail = (val: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)

const onSubmit = () => {
  errors.name = form.name ? '' : '姓名不能为空'
  errors.email = !form.email ? '邮箱不能为空' : isEmail(form.email) ? '' : '邮箱格式不正确'
  errors.note = form.note.length >= 10 ? '' : '备注至少 10 个字'

  const hasError = Object.values(errors).some(Boolean)
  success.value = !hasError

  if (success.value) {
    form.name = ''
    form.email = ''
    form.note = ''
  }
}
</script>

<style scoped>
.form-demo {
  display: grid;
  gap: var(--space-4);
  max-width: 760px;
}

.form-demo__head h2 {
  margin: 0;
  color: var(--text-primary);
}

.form-demo__head p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.form-demo__form {
  display: grid;
  gap: var(--space-3);
}

.form-demo__form label {
  display: grid;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 0.92rem;
}

.form-demo__error {
  color: var(--danger-500);
  font-size: 0.82rem;
}

.form-demo__success {
  margin: 0;
  color: var(--success-500);
  background: #f1f8f4;
  border: 1px solid #cfe4d8;
  border-radius: var(--radius-sm);
  padding: 10px 12px;
}
</style>
