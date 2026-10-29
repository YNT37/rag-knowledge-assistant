<script setup lang="ts">
import {RouterLink, RouterView} from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">PERSONAL RAG WORKSPACE</p>
        <h1>技术资料知识库</h1>
      </div>
      <nav aria-label="主导航">
        <RouterLink :to="{name: 'question'}">知识问答</RouterLink>
        <RouterLink :to="{name: 'documents'}">资料管理</RouterLink>
      </nav>
    </header>
    <main>
      <RouterView/>
    </main>
  </div>
</template>

<style>
:root {
  color: #172033;
  background: #f3f5f9;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-synthesis: none;
}

* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; min-height: 100vh; }
button, input, select, textarea { font: inherit; }
button { cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .58; }
a { color: inherit; }

.app-shell { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding-bottom: 48px; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 28px 0 22px; }
.topbar h1 { margin: 3px 0 0; font-size: 25px; letter-spacing: -.02em; }
.eyebrow { margin: 0; color: #2563eb; font-size: 11px; font-weight: 800; letter-spacing: .16em; }
.topbar nav { display: flex; gap: 8px; padding: 5px; border: 1px solid #dfe4ed; border-radius: 12px; background: #fff; }
.topbar nav a { padding: 9px 14px; border-radius: 8px; color: #637083; font-size: 14px; text-decoration: none; }
.topbar nav a.router-link-active { color: #fff; background: #172033; }

.page-heading { display: flex; justify-content: space-between; align-items: end; gap: 20px; margin: 10px 0 20px; }
.page-heading h2 { margin: 0 0 6px; font-size: 26px; }
.page-heading p { margin: 0; color: #69758a; }
.panel { border: 1px solid #e0e5ed; border-radius: 16px; background: #fff; box-shadow: 0 8px 30px rgba(24, 32, 51, .05); }
.panel-body { padding: 20px; }
.muted { color: #738096; }
.error, .success { margin: 12px 0; padding: 11px 13px; border-radius: 9px; font-size: 14px; }
.error { color: #b42318; background: #fff0ed; }
.success { color: #067647; background: #ecfdf3; }
.primary, .secondary, .danger, .text-button { border: 0; border-radius: 8px; padding: 9px 13px; }
.primary { color: #fff; background: #2563eb; }
.secondary { color: #344054; background: #edf1f6; }
.danger { color: #b42318; background: #feeceb; }
.text-button { padding: 5px 8px; color: #2563eb; background: transparent; }
.field { display: grid; gap: 7px; }
.field label { color: #475467; font-size: 13px; font-weight: 700; }
.field input, .field select, .field textarea {
  width: 100%; border: 1px solid #d6dce5; border-radius: 9px; padding: 10px 11px; color: #172033; background: #fff;
}
.field textarea { resize: vertical; line-height: 1.6; }
.field input:focus, .field select:focus, .field textarea:focus { outline: 3px solid #dbeafe; border-color: #2563eb; }

@media (max-width: 720px) {
  .app-shell { width: min(100% - 20px, 1180px); }
  .topbar { align-items: flex-start; flex-direction: column; }
  .topbar nav { width: 100%; }
  .topbar nav a { flex: 1; text-align: center; }
  .page-heading { align-items: flex-start; flex-direction: column; }
}
</style>
