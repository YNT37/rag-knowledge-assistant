<script setup lang="ts">
import {ref} from "vue";
import {requestAnswer, type RagSource, requestRagResponse} from "@/rag-request.ts";


const title = "技术资料知识库助手"
const answer = ref("尚未提问")
const question = ref("")
const loading = ref(false);
const button = ref("发送")
const sources = ref<RagSource[]>([])
const selectedSource = ref<RagSource | null>(null)

function selectSource(source: RagSource): void {
  selectedSource.value = source
}

async function sendQuestion(): Promise<void> {
  selectedSource.value = null
  question.value = question.value.trim()
  if (question.value === "") {
    answer.value = "请输入问题"
    sources.value = []
    return
  }

  try {
    sources.value = []
    loading.value = true
    button.value = "发送中"
    answer.value = "正在回答..."
    const response = await requestRagResponse(question.value)
    if (typeof response !== "string") {
      answer.value = response.answer
      sources.value = response.sources

    } else {
      answer.value = response
    }

  } catch (error) {
    answer.value = "请求或处理响应失败，请稍后重试:\n" + error;
  } finally {
    loading.value = false
    button.value = "发送"
  }


}

</script>

<template>
  <h1>{{ title }}</h1>
  <input type="text" v-model="question">
  <p>
    {{ question }}
  </p>
  <button type="button" @click="sendQuestion()" :disabled="loading">{{ button }}</button>
  <p>
    {{ answer }}
  </p>
  <p v-if="sources.length === 0">暂无参考片段</p>
  <p v-for="(item, index) in sources" :key="index" @click="selectSource(item)">
    {{ item.source }}(块{{ item.chunk_id }})
  </p>
  <p v-if="selectedSource !== null">
    {{ selectedSource.content }}
  </p>

</template>

<style scoped></style>
