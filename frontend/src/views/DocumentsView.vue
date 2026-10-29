<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {RouterLink} from 'vue-router'
import {
  createCategory,
  createDocument,
  deleteCategory,
  deleteDocument,
  getCategories,
  getDocuments,
  moveDocument,
  renameCategory,
} from '@/api/knowledge'
import type {CategoryItem, DocumentItem} from '@/types/knowledge'

const categories = ref<CategoryItem[]>([])
const documents = ref<DocumentItem[]>([])
const selectedCategoryId = ref<number | null>(null)
const importCategoryId = ref<number | null>(null)
const categoryName = ref('')
const source = ref('')
const content = ref('')
const loading = ref(false)
const error = ref('')
const message = ref('')

function errorMessage(value: unknown): string {
  return value instanceof Error ? value.message : String(value)
}

async function refresh(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const [categoryResult, documentResult] = await Promise.all([
      getCategories(),
      getDocuments(selectedCategoryId.value),
    ])
    categories.value = categoryResult.data
    documents.value = documentResult.data
    const categoryStillExists = categories.value.some(
      item => item.id === importCategoryId.value,
    )
    if (!categoryStillExists) {
      importCategoryId.value = categories.value.find(item => item.is_default)?.id ?? null
    }
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    loading.value = false
  }
}

async function chooseCategory(categoryId: number | null): Promise<void> {
  selectedCategoryId.value = categoryId
  await refresh()
}

async function addCategory(): Promise<void> {
  error.value = ''
  message.value = ''
  try {
    await createCategory(categoryName.value)
    categoryName.value = ''
    message.value = '分类已创建'
    await refresh()
  } catch (cause) {
    error.value = errorMessage(cause)
  }
}

async function editCategory(category: CategoryItem): Promise<void> {
  const name = window.prompt('输入新的分类名称', category.name)
  if (name === null || name.trim() === category.name) return
  error.value = ''
  message.value = ''
  try {
    await renameCategory(category.id, name)
    message.value = '分类已重命名'
    await refresh()
  } catch (cause) {
    error.value = errorMessage(cause)
  }
}

async function removeCategory(category: CategoryItem): Promise<void> {
  if (!window.confirm(`删除“${category.name}”？其中资料会移入“未分类”。`)) return
  error.value = ''
  message.value = ''
  try {
    await deleteCategory(category.id)
    if (selectedCategoryId.value === category.id) selectedCategoryId.value = null
    message.value = '分类已删除，原资料已移入“未分类”'
    await refresh()
  } catch (cause) {
    error.value = errorMessage(cause)
  }
}

async function importDocument(): Promise<void> {
  error.value = ''
  message.value = ''
  try {
    const result = await createDocument({
      source: source.value,
      content: content.value,
      category_id: importCategoryId.value,
    })
    source.value = ''
    content.value = ''
    message.value = `已导入 ${result.source}`
    await refresh()
  } catch (cause) {
    error.value = errorMessage(cause)
  }
}

async function changeCategory(document: DocumentItem, event: Event): Promise<void> {
  const categoryId = Number((event.target as HTMLSelectElement).value)
  error.value = ''
  message.value = ''
  try {
    await moveDocument(document.source, categoryId)
    message.value = `已更新 ${document.source} 的分类`
    await refresh()
  } catch (cause) {
    error.value = errorMessage(cause)
    await refresh()
  }
}

async function removeDocument(document: DocumentItem): Promise<void> {
  if (!window.confirm(`确定删除 ${document.source}？此操作会同时删除资料文件。`)) return
  error.value = ''
  message.value = ''
  try {
    await deleteDocument(document.source)
    message.value = `已删除 ${document.source}`
    await refresh()
  } catch (cause) {
    error.value = errorMessage(cause)
  }
}

onMounted(refresh)
</script>

<template>
  <section class="page-heading">
    <div>
      <h2>资料管理</h2>
      <p>按分类维护 Markdown 资料，导入后即可参与知识问答。</p>
    </div>
    <span class="muted">{{ documents.length }} 份当前资料</span>
  </section>

  <p v-if="error" class="error">{{ error }}</p>
  <p v-if="message" class="success">{{ message }}</p>

  <div class="workspace">
    <aside class="panel category-panel">
      <div class="panel-body">
        <div class="section-title"><h3>资料目录</h3><span>{{ categories.length }}</span></div>
        <button
          class="category-row"
          :class="{active: selectedCategoryId === null}"
          type="button"
          @click="chooseCategory(null)"
        >
          <span>全部资料</span><strong>{{ categories.reduce((sum, item) => sum + item.document_count, 0) }}</strong>
        </button>
        <div v-for="category in categories" :key="category.id" class="category-item">
          <button
            class="category-row"
            :class="{active: selectedCategoryId === category.id}"
            type="button"
            @click="chooseCategory(category.id)"
          >
            <span>{{ category.name }}</span><strong>{{ category.document_count }}</strong>
          </button>
          <div v-if="!category.is_default" class="category-actions">
            <button class="text-button" type="button" @click="editCategory(category)">改名</button>
            <button class="text-button delete-link" type="button" @click="removeCategory(category)">删除</button>
          </div>
        </div>
        <form class="create-category" @submit.prevent="addCategory">
          <input v-model="categoryName" maxlength="20" placeholder="新分类名称" aria-label="新分类名称">
          <button class="secondary" type="submit" :disabled="categoryName.trim() === ''">添加</button>
        </form>
      </div>
    </aside>

    <div class="content-column">
      <section class="panel">
        <form class="panel-body import-form" @submit.prevent="importDocument">
          <div class="section-title"><h3>导入资料</h3><span>仅支持 .md</span></div>
          <div class="import-grid">
            <div class="field">
              <label for="source">文件名</label>
              <input id="source" v-model="source" maxlength="100" placeholder="例如 fastapi-notes.md">
            </div>
            <div class="field">
              <label for="category">所属分类</label>
              <select id="category" v-model="importCategoryId">
                <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label for="content">Markdown 正文</label>
            <textarea id="content" v-model="content" rows="7" placeholder="# 标题&#10;&#10;在这里粘贴资料内容"></textarea>
          </div>
          <div class="form-footer">
            <span class="muted">{{ content.length }} 字符</span>
            <button class="primary" type="submit" :disabled="source.trim() === '' || content.trim() === ''">导入资料</button>
          </div>
        </form>
      </section>

      <section class="panel document-panel">
        <div class="panel-body">
          <div class="section-title"><h3>资料列表</h3><span v-if="loading">正在加载…</span></div>
          <p v-if="!loading && documents.length === 0" class="empty">当前分类没有资料。</p>
          <article v-for="document in documents" :key="document.id" class="document-row">
            <div>
              <RouterLink :to="{name: 'document-detail', params: {source: document.source}}" class="document-name">
                {{ document.source }}
              </RouterLink>
              <p>{{ document.category_name }}</p>
            </div>
            <div class="document-actions">
              <select :value="document.category_id" aria-label="移动资料分类" @change="changeCategory(document, $event)">
                <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option>
              </select>
              <button class="danger" type="button" @click="removeDocument(document)">删除</button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.workspace { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 18px; align-items: start; }
.category-panel { position: sticky; top: 16px; }
.content-column { display: grid; gap: 18px; }
.section-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.section-title h3 { margin: 0; font-size: 16px; }
.section-title span { color: #8691a3; font-size: 12px; }
.category-item { padding: 3px 0; border-bottom: 1px solid #f0f2f6; }
.category-row { display: flex; justify-content: space-between; width: 100%; border: 0; border-radius: 8px; padding: 10px; color: #475467; background: transparent; text-align: left; }
.category-row:hover, .category-row.active { color: #1d4ed8; background: #eff6ff; }
.category-row strong { font-size: 12px; }
.category-actions { display: flex; justify-content: flex-end; padding: 0 4px 5px; }
.delete-link { color: #b42318; }
.create-category { display: grid; grid-template-columns: 1fr auto; gap: 7px; margin-top: 16px; }
.create-category input { min-width: 0; border: 1px solid #d6dce5; border-radius: 8px; padding: 9px; }
.import-form { display: grid; gap: 14px; }
.import-grid { display: grid; grid-template-columns: 1fr 210px; gap: 12px; }
.form-footer { display: flex; align-items: center; justify-content: space-between; }
.document-panel .panel-body { padding-bottom: 8px; }
.document-row { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 14px 0; border-top: 1px solid #edf0f4; }
.document-name { color: #1d4ed8; font-weight: 700; text-decoration: none; }
.document-row p { margin: 5px 0 0; color: #8792a5; font-size: 12px; }
.document-actions { display: flex; gap: 8px; }
.document-actions select { max-width: 160px; border: 1px solid #d6dce5; border-radius: 8px; padding: 8px; background: #fff; }
.empty { padding: 26px 0; color: #8792a5; text-align: center; }
@media (max-width: 820px) {
  .workspace { grid-template-columns: 1fr; }
  .category-panel { position: static; }
  .import-grid { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .document-row { align-items: flex-start; flex-direction: column; }
  .document-actions { width: 100%; }
  .document-actions select { flex: 1; max-width: none; }
}
</style>
