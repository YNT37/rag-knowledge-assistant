<script setup lang="ts">
import {ref, watch} from 'vue'
import {RouterLink, useRoute} from 'vue-router'
import {getDocument} from '@/api/knowledge'
import type {DocumentDetail} from '@/types/knowledge'

const route = useRoute()
const document = ref<DocumentDetail | null>(null)
const loading = ref(false)
const error = ref('')

async function loadDocument(sourceValue: string | string[]): Promise<void> {
  const source = Array.isArray(sourceValue) ? sourceValue[0] : sourceValue
  if (source === undefined || source === '') {
    error.value = '资料名称无效'
    document.value = null
    return
  }
  loading.value = true
  error.value = ''
  document.value = null
  try {
    document.value = await getDocument(source)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
  } finally {
    loading.value = false
  }
}

watch(() => route.params.source as string | string[], loadDocument, {immediate: true})
</script>

<template>
  <section class="page-heading">
    <div>
      <RouterLink :to="{name: 'documents'}" class="back-link">← 返回资料管理</RouterLink>
      <h2>{{ document?.source ?? '资料详情' }}</h2>
      <p v-if="document">分类：{{ document.category_name }} · {{ document.char_count }} 字符</p>
    </div>
  </section>
  <p v-if="loading" class="muted">正在加载资料…</p>
  <p v-if="error" class="error">{{ error }}</p>
  <article v-if="document" class="panel document-content">
    <pre>{{ document.content }}</pre>
  </article>
</template>

<style scoped>
.back-link { display: inline-block; margin-bottom: 16px; color: #2563eb; font-size: 14px; text-decoration: none; }
.document-content { padding: 26px; }
.document-content pre { margin: 0; overflow-wrap: anywhere; color: #263247; font: 14px/1.8 "SFMono-Regular", Consolas, monospace; white-space: pre-wrap; }
</style>
