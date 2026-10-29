<script setup lang="ts">
import {ref} from 'vue'
import {RouterLink} from 'vue-router'
import {requestRagResponse} from '@/api/rag-request'
import type {RagSource} from '@/types/rag'

const answer = ref('输入问题后，回答会显示在这里。')
const question = ref('')
const loading = ref(false)
const sources = ref<RagSource[]>([])
const selectedSource = ref<RagSource | null>(null)

function selectSource(source: RagSource): void {
  selectedSource.value = source
}

async function sendQuestion(): Promise<void> {
  const normalized = question.value.trim()
  selectedSource.value = null
  sources.value = []
  if (normalized === '') {
    answer.value = '请输入问题'
    return
  }
  question.value = normalized
  loading.value = true
  answer.value = '正在检索资料并生成回答…'
  try {
    const response = await requestRagResponse(normalized)
    if (typeof response === 'string') {
      answer.value = response
      return
    }
    answer.value = response.answer
    sources.value = response.sources
  } catch (cause) {
    answer.value = `请求或处理响应失败：${cause instanceof Error ? cause.message : String(cause)}`
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="page-heading">
    <div>
      <h2>知识问答</h2>
      <p>回答基于资料库中已登记的 Markdown 文档，并附带可核对的参考片段。</p>
    </div>
    <RouterLink :to="{name: 'documents'}" class="manage-link">管理资料 →</RouterLink>
  </section>

  <div class="question-layout">
    <section class="panel question-panel">
      <form class="ask-form" @submit.prevent="sendQuestion">
        <label for="question">你的问题</label>
        <textarea id="question" v-model="question" rows="4" placeholder="例如：FastAPI 的依赖注入适合解决什么问题？"></textarea>
        <div class="ask-footer">
          <span class="muted">检索范围以资料管理页中的文件为准</span>
          <button class="primary" type="submit" :disabled="loading">{{ loading ? '回答中…' : '发送问题' }}</button>
        </div>
      </form>
      <div class="answer-block">
        <p class="answer-label">回答</p>
        <p class="answer-text">{{ answer }}</p>
      </div>
    </section>

    <aside class="panel reference-panel">
      <div class="panel-body">
        <h3>参考片段</h3>
        <p v-if="sources.length === 0" class="empty-reference">暂无参考片段</p>
        <button
          v-for="item in sources"
          :key="`${item.source}-${item.chunk_id}`"
          class="reference-item"
          :class="{active: selectedSource === item}"
          type="button"
          @click="selectSource(item)"
        >
          <strong>{{ item.source }}</strong>
          <span>片段 {{ item.chunk_id }}</span>
        </button>
        <div v-if="selectedSource" class="reference-content">
          <div class="reference-heading">
            <strong>片段内容</strong>
            <RouterLink :to="{name: 'document-detail', params: {source: selectedSource.source}}">查看原文</RouterLink>
          </div>
          <p>{{ selectedSource.content }}</p>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.manage-link { color: #2563eb; font-size: 14px; font-weight: 700; text-decoration: none; }
.question-layout { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(300px, .75fr); gap: 18px; align-items: start; }
.question-panel { overflow: hidden; }
.ask-form { display: grid; gap: 11px; padding: 24px; }
.ask-form label { font-weight: 800; }
.ask-form textarea { width: 100%; resize: vertical; border: 1px solid #d6dce5; border-radius: 10px; padding: 12px; line-height: 1.6; }
.ask-form textarea:focus { outline: 3px solid #dbeafe; border-color: #2563eb; }
.ask-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.ask-footer span { font-size: 12px; }
.answer-block { min-height: 210px; padding: 23px 24px; border-top: 1px solid #e7eaf0; background: #fafbfc; }
.answer-label { margin: 0 0 12px; color: #7b8799; font-size: 12px; font-weight: 800; letter-spacing: .1em; }
.answer-text { margin: 0; line-height: 1.8; white-space: pre-wrap; }
.reference-panel h3 { margin: 0 0 15px; font-size: 16px; }
.empty-reference { padding: 24px 0; color: #8b95a7; text-align: center; }
.reference-item { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; width: 100%; margin-bottom: 8px; border: 1px solid #e4e7ec; border-radius: 9px; padding: 11px; color: #344054; background: #fff; text-align: left; }
.reference-item:hover, .reference-item.active { border-color: #93b4ff; background: #eff6ff; }
.reference-item strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.reference-item span { color: #8a95a6; font-size: 12px; }
.reference-content { margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e9ef; }
.reference-heading { display: flex; justify-content: space-between; gap: 10px; }
.reference-heading a { color: #2563eb; font-size: 13px; text-decoration: none; }
.reference-content p { max-height: 290px; overflow: auto; margin-bottom: 0; color: #536176; font-size: 13px; line-height: 1.7; white-space: pre-wrap; }
@media (max-width: 860px) {
  .question-layout { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .ask-footer { align-items: stretch; flex-direction: column; }
}
</style>
