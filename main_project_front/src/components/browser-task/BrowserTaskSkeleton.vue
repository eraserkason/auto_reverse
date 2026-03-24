<template>
  <div class="bt-skeleton" aria-busy="true" aria-label="Loading browser task">
    <div class="bt-skeleton__topbar">
      <div class="bt-skeleton__title shimmer"></div>
      <div class="bt-skeleton__actions">
        <div class="bt-skeleton__btn shimmer"></div>
        <div class="bt-skeleton__btn shimmer"></div>
      </div>
    </div>

    <div class="bt-skeleton__chat">
      <div class="bt-skeleton__message bt-skeleton__message--short shimmer"></div>
      <div class="bt-skeleton__message bt-skeleton__message--long shimmer"></div>
      <div class="bt-skeleton__message bt-skeleton__message--medium shimmer"></div>
    </div>

    <div class="bt-skeleton__composer">
      <div class="bt-skeleton__textarea shimmer"></div>
      <div class="bt-skeleton__composer-footer">
        <div class="bt-skeleton__hint shimmer"></div>
        <div class="bt-skeleton__btn shimmer"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bt-skeleton {
  display: grid;
  gap: 16px;
  max-width: min(100%, 1360px);
  margin: 0 auto;
  padding-top: 6px;
}

.shimmer {
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--text-muted) 8%, transparent) 25%,
    color-mix(in srgb, var(--text-muted) 16%, transparent) 50%,
    color-mix(in srgb, var(--text-muted) 8%, transparent) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.6s ease-in-out infinite;
  border-radius: 12px;
}

.bt-skeleton__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
}

.bt-skeleton__title {
  width: min(280px, 50%);
  height: 32px;
  border-radius: 10px;
}

.bt-skeleton__actions {
  display: flex;
  gap: 8px;
}

.bt-skeleton__btn {
  width: 100px;
  height: 34px;
  border-radius: 10px;
}

.bt-skeleton__chat {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 22px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg-strong);
  min-height: 320px;
}

.bt-skeleton__message {
  height: 52px;
  border-radius: 18px;
}

.bt-skeleton__message--short {
  width: min(55%, 360px);
  justify-self: end;
}

.bt-skeleton__message--long {
  width: min(80%, 600px);
}

.bt-skeleton__message--medium {
  width: min(65%, 460px);
}

.bt-skeleton__composer {
  display: grid;
  gap: 8px;
  padding: 12px;
  border-radius: 20px;
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
}

.bt-skeleton__textarea {
  height: 56px;
  border-radius: 14px;
}

.bt-skeleton__composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.bt-skeleton__hint {
  width: 160px;
  height: 18px;
  border-radius: 8px;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .shimmer {
    animation: none;
    background: color-mix(in srgb, var(--text-muted) 10%, transparent);
  }
}
</style>
