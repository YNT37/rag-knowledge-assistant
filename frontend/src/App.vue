<script setup lang="ts">
import {RouterLink, RouterView} from "vue-router";
</script>

<template>
  <p>
    <RouterLink to="/">知识问答</RouterLink>
    |
    <RouterLink to="/documents">资料管理</RouterLink>
    |
    <RouterLink to="/documents/detail">资料详情</RouterLink>
  </p>

  <RouterView/>
</template>