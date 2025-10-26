<template>
  <div class="container">
    <header>
      <h1>AI WHU — Controller 测试面板</h1>
      <nav>
        <button :class="{active: tab==='users'}" @click="tab='users'">Users</button>
        <button :class="{active: tab==='health'}" @click="tab='health'">Health Records</button>
        <button :class="{active: tab==='conv'}" @click="tab='conv'">Conversation (HTTP)</button>
        <button :class="{active: tab==='ws'}" @click="tab='ws'">WebSocket</button>
      </nav>
    </header>

    <main>
      <UserTest v-if="tab==='users'" />
      <HealthTest v-if="tab==='health'" />
      <ConversationTest v-if="tab==='conv'" />
      <ConversationWS v-if="tab==='ws'" />
    </main>

    <footer>
      <small>测试后台接口：/user, /user-health, /conversation — 后端应运行于 http://localhost:8080</small>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UserTest from './components/UserTest.vue'
import HealthTest from './components/HealthTest.vue'
import ConversationTest from './components/ConversationTest.vue'
import ConversationWS from './components/ConversationWS.vue'

const tab = ref('users')
</script>

<style scoped>
.container { max-width: 980px; margin: 1.5rem auto; font-family: Arial, "Helvetica Neue", Helvetica, sans-serif; }
header { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
h1 { margin:0; font-size:1.4rem; }
nav { display:flex; gap:.5rem; }
button { padding:.5rem .9rem; border-radius:6px; border:1px solid #ccc; background:#f6f6f6; cursor:pointer; }
button.active { background: linear-gradient(90deg,#6dd3ff,#8a7bff); color:white; border: none; box-shadow: 0 4px 14px rgba(128,0,255,0.12); }
main { margin-top:1rem; padding:1rem; border-radius:8px; background:#fff; box-shadow:0 4px 16px rgba(0,0,0,0.03); }
footer { margin-top:12px; color:#666; text-align:center; }
</style>