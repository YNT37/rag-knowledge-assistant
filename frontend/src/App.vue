<script setup lang="ts">
import {ref} from "vue";

const title = "技术资料知识库助手"
const answer = ref("尚未提问")
const question = ref("")

function updateAnswer(): void {
  answer.value = "正在回答"
}

</script>

<template>
  <h1>{{ title }}</h1>
  <p>
    {{ answer }}
  </p>
  <button type="button" @click="updateAnswer">模拟回答</button>
  <input type="text" v-model="question">
  <p>
    {{ question }}
  </p>

</template>

<style scoped></style>
