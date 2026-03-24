<template>
  <div class="sidebar-content">
    <div class="sidebar-nav-container">
      <AppNav @navigate="$emit('navigate')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import AppNav from '@/components/AppNav.vue';

defineEmits(['navigate']);
</script>

<style scoped>
.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.sidebar-nav-container {
  flex: 1;
  padding: 0 6px;
}
</style>
