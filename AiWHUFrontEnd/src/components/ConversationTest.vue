<template>
  <div>
    <h2>Conversation (HTTP) 测试</h2>

    <div class="panel">
      <h3>初始化（获取用户所有会话及消息）</h3>
      <div class="row">
        <div class="label">User ID</div>
        <input v-model="userId" class="field" />
        <button @click="init">初始化</button>
      </div>
      <div class="list">
        <div v-for="m in messages" :key="m.send_time + '_' + m.message_seq" class="msg" :class="m.sender_type">
          <div><strong>[conv {{ m.conversation_id }}] seq:{{ m.message_seq }}</strong></div>
          <div>{{ m.content }}</div>
          <div class="small">from: {{ m.sender_type }} ({{ m.sender_id }}) at {{ m.send_time }} ref: {{ m.reference }}</div>
        </div>
      </div>
    </div>

    <div class="panel">
      <h3>新增消息 / 新增会话（HTTP）</h3>
      <div class="row">
        <div class="label">会话ID (可空新增)</div>
        <input v-model="convId" class="field" />
      </div>
      <div class="row">
        <div class="label">User ID</div>
        <input v-model="reqUserId" class="field" />
      </div>
      <div class="row">
        <div class="label">Agent ID</div>
        <input v-model="reqAgentId" class="field" />
      </div>
      <div class="row">
        <div class="label">消息内容</div>
        <input v-model="reqContent" class="field" />
      </div>
      <div class="row">
        <div class="label">附件路径(reference)</div>
        <input v-model="reqRef" class="field" />
      </div>
      <button @click="addMsg">发送(HTTP)</button>
    </div>

    <div class="panel">
      <h3>删除对话</h3>
      <div class="row">
        <div class="label">User ID</div>
        <input v-model="delUserId" class="field" />
      </div>
      <div class="row">
        <div class="label">Conversation ID</div>
        <input v-model="delConvId" class="field" />
      </div>
      <button @click="delConv">删除</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const base = '/conversation'

const userId = ref('')
const messages = ref([])

const convId = ref('')
const reqUserId = ref('')
const reqAgentId = ref('')
const reqContent = ref('')
const reqRef = ref('')

const delUserId = ref('')
const delConvId = ref('')

async function init() {
  if (!userId.value) return alert('请输入 userId')
  try {
    const res = await fetch(`${base}/init?userId=${encodeURIComponent(userId.value)}`)
    messages.value = await res.json()
  } catch (e) { messages.value = [] }
}

async function addMsg() {
  if (!reqUserId.value) return alert('请输入 user id')
  const body = {
    conversation_id: convId.value ? Number(convId.value) : null,
    user_id: Number(reqUserId.value),
    agent_id: reqAgentId.value ? Number(reqAgentId.value) : null,
    sender_type: 'user',
    sender_id: Number(reqUserId.value),
    content: reqContent.value,
    reference: reqRef.value
  }
  try {
    const res = await fetch(`${base}/add`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    })
    const ok = await res.text()
    alert(ok === 'true' ? '已发送并保存' : '发送失败')
    init()
  } catch (e) { alert('请求异常') }
}

async function delConv() {
  if (!delUserId.value || !delConvId.value) return alert('请输入')
  try {
    const res = await fetch(`${base}/delete?userId=${encodeURIComponent(delUserId.value)}&conversationId=${encodeURIComponent(delConvId.value)}`, { method: 'DELETE' })
    const ok = await res.text()
    alert(ok === 'true' ? '删除成功' : '删除失败')
    init()
  } catch (e) { alert('请求异常') }
}
</script>

<style scoped>
h2 { margin-top:0 }
</style>