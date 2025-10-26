<template>
  <div>
    <h2>Conversation (WebSocket) 测试</h2>

    <div class="panel">
      <div class="row">
        <div class="label">User ID</div>
        <input v-model="userId" class="field" placeholder="作为 query param 连接" />
        <button @click="connect" :disabled="connected">Connect</button>
        <button @click="disconnect" :disabled="!connected">Disconnect</button>
        <span class="small">{{ status }}</span>
      </div>

      <div class="row">
        <div class="label">会话ID (可空)</div>
        <input v-model="conversationId" class="field" />
      </div>

      <div class="row">
        <div class="label">Agent ID</div>
        <input v-model="agentId" class="field" />
      </div>

      <div class="row">
        <div class="label">消息</div>
        <input v-model="content" class="field" />
      </div>

      <div class="row">
        <div class="label">附件路径</div>
        <input v-model="reference" class="field" placeholder="/uploads/xxx.png or http..." />
      </div>

      <button @click="sendMessage" :disabled="!connected">发送（WebSocket）</button>
    </div>

    <div class="panel">
      <h3>消息流</h3>
      <div class="list">
        <div v-for="m in msgs" :key="m.send_time + '_' + m.message_seq" class="msg" :class="m.sender_type">
          <div><strong>[conv {{ m.conversation_id }}] seq:{{ m.message_seq }}</strong></div>
          <div>{{ m.content }}</div>
          <div class="small">from: {{ m.sender_type }} ({{ m.sender_id }}) at {{ m.send_time }} ref: {{ m.reference }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const wsUrlBase = (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.hostname + ':8080/ws/conversation'
let ws = null

const userId = ref('')
const conversationId = ref('')
const agentId = ref('')
const content = ref('')
const reference = ref('')

const connected = ref(false)
const status = ref('未连接')
const msgs = ref([])

function connect() {
  if (!userId.value) return alert('请输入 userId')
  const url = wsUrlBase + '?userId=' + encodeURIComponent(userId.value)
  ws = new WebSocket(url)
  ws.onopen = () => { connected.value = true; status.value = '已连接' }
  ws.onclose = () => { connected.value = false; status.value = '已断开' }
  ws.onerror = (e) => { status.value = '连接错误'; console.error(e) }
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data)
      // push to UI
      msgs.value.push(data)
    } catch (e) {
      console.warn('非JSON消息', ev.data)
    }
  }
}

function disconnect() {
  if (ws) ws.close()
  ws = null
  connected.value = false
  status.value = '已断开'
}

function sendMessage() {
  if (!connected.value) return alert('未连接')
  const msg = {
    conversation_id: conversationId.value ? Number(conversationId.value) : null,
    user_id: Number(userId.value),
    agent_id: agentId.value ? Number(agentId.value) : null,
    sender_type: 'user',
    sender_id: Number(userId.value),
    send_time: new Date().toISOString(),
    message_seq: null,
    content: content.value,
    reference: reference.value
  }
  ws.send(JSON.stringify(msg))
  // 本地也展示用户发送
  msgs.value.push({...msg, sender_type:'user'})
  // 清空输入
  content.value = ''
  reference.value = ''
}
</script>

<style scoped>
h2 { margin-top:0 }
</style>