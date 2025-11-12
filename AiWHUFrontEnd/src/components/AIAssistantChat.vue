<template>
  <div class="chat">
    <!-- 左侧：历史记录侧栏 -->
    <aside class="sidebar glass">
      <div class="sidebar-head">
        <h3>历史记录</h3>
        <div class="ops">
          <button class="ghost sm" @click="loadHistory">刷新</button>
          <button class="primary sm" @click="newConversation">新建对话</button>
        </div>
      </div>

      <div class="thread-list">
        <div
            v-for="t in threads"
            :key="t.id"
            class="thread"
            :class="{ active: t.id === selectedConvId }"
            @click="selectThread(t.id)"
        >
          <div class="row1">
            <div class="title">{{ t.title }}</div>
            <div class="time">{{ formatDate(t.lastTime) }}</div>
          </div>
          <div class="row2">
            <div class="preview" :title="t.lastContent">{{ t.lastContent }}</div>
          </div>
        </div>

        <div v-if="!threads.length" class="empty">暂无历史记录</div>
      </div>
    </aside>

    <!-- 右侧：聊天主窗口 -->
    <section class="main">
      <div class="header">
        <h2>AI 健康咨询</h2>
<!--        <div class="hint">-->
<!--          实时 WebSocket 对话，支持图片/PDF/TXT 附件-->
<!--          <span v-if="selectedConvId" class="conv-tag">会话ID: {{ selectedConvId }}</span>-->
<!--        </div>-->
      </div>

      <div class="bar">
        <div class="row">
          <label style="color: #7a98e7">会话ID</label>
          <input v-model="conversationId" placeholder="可空（新建会话）" readonly style="background: #161b2e; color: #bcc3e9;" />
        </div>
        <div class="row">
          <label style="color: #7a98e7">Agent ID</label>
          <select v-model="agentId" @change="onAgentIdChange" style="background: #161b2e; color: #e9efff; border-radius: 10px; border: 1px solid #363b4e;">
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
          </select>
        </div>
        <div class="actions">
          <!-- 自动连接，无需按钮 -->
          <span class="status">{{ status }}</span>
        </div>
      </div>

      <div class="window">
        <div ref="scrollBox" class="messages">
          <div
              v-for="m in currentMsgs"
              :key="(m.send_time || '') + '_' + (m.message_seq || Math.random())"
              class="bubble"
              :class="m.sender_type"
          >
            <div class="meta">
              <span class="conv">[conv {{ m.conversation_id ?? '-' }}] seq: {{ m.message_seq ?? '-' }}</span>
              <span class="time">{{ formatDate(m.send_time) }}</span>
            </div>
            <div class="content" v-html="renderedMarkdown(m.content)"></div>

            <div v-if="m.reference" class="refs">
              <template v-if="isImage(m.reference)">
                <a :href="fileUrl(m.reference)" target="_blank">
                  <img :src="fileUrl(m.reference)" alt="图片附件" />
                </a>
              </template>
              <template v-else-if="isPdf(m.reference)">
                <a :href="fileUrl(m.reference)" target="_blank" class="ref-pill pdf">PDF 文件</a>
              </template>
              <template v-else-if="isTxt(m.reference)">
                <a :href="fileUrl(m.reference)" target="_blank" class="ref-pill txt">TXT 文件</a>
              </template>
              <template v-else>
                <span class="ref-pill">{{ m.reference }}</span>
              </template>
            </div>
          </div>
        </div>

        <div class="composer">
          <div class="file">
            <input type="file" ref="fileInput" @change="onFilePick" />
            <button class="ghost" @click="uploadFile" :disabled="uploading">上传</button>
            <span class="tiny">{{ uploadResult || (uploading ? '上传中...' : '') }}</span>
          </div>

          <div class="preview" v-if="uploadedFileUrl">
            <template v-if="isImage(uploadedFileUrl)">
              <img :src="fileUrl(uploadedFileUrl)" alt="预览" />
            </template>
            <template v-else-if="isPdf(uploadedFileUrl)">
              <a :href="fileUrl(uploadedFileUrl)" target="_blank">已上传 PDF，点击查看</a>
            </template>
            <template v-else-if="isTxt(uploadedFileUrl)">
              <a :href="fileUrl(uploadedFileUrl)" target="_blank">已上传 TXT，点击下载</a>
            </template>
            <template v-else>
              <span>{{ uploadedFileUrl }}</span>
            </template>
          </div>

          <div class="input">
            <input
                v-model="content"
                placeholder="输入你的问题，例如：请根据我的 BMI 给出饮食建议"
                @keyup.enter="sendMessage"
            />
            <button class="send" @click="sendMessage" :disabled="!connected || uploading">发送</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted, watch } from 'vue'
import { marked } from 'marked'
const httpBase = 'http://localhost:8080/conversation'
const fileApi = 'http://localhost:8080/file/upload'
const wsUrlBase = (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.hostname + ':8080/ws/conversation'
let ws = null

const props = defineProps({
  userId: { type: String, required: true }
})

// 顶部表单与状态
const conversationId = ref('')
const agentId = ref('1') // 默认设置为1
const content = ref('')
const reference = ref('')

// 连接状态
const connected = ref(false)
const status = ref('未连接')

// 历史与当前展示
const allMsgs = ref([])
const currentMsgs = ref([])
const selectedConvId = ref(null)

// 上传
const fileInput = ref(null)
const uploadResult = ref('')
const uploadedFileUrl = ref('')
const uploading = ref(false)

const scrollBox = ref(null)
function scrollToBottom() {
  nextTick(() => {
    if (scrollBox.value) scrollBox.value.scrollTop = scrollBox.value.scrollHeight
  })
}

const threads = computed(() => {
  const byConv = new Map()
  for (const m of allMsgs.value) {
    if (m.conversation_id == null) continue
    const exist = byConv.get(m.conversation_id) || {
      id: m.conversation_id,
      lastTime: m.last_message_time || m.send_time,
      lastContent: m.content || '',
      title: m.remark || `会话 #${m.conversation_id}`
    }
    const curTime = new Date(exist.lastTime || 0).getTime()
    const mTime = new Date(m.last_message_time || m.send_time || 0).getTime()
    if (mTime >= curTime) {
      exist.lastTime = m.last_message_time || m.send_time
      exist.lastContent = m.content || ''
      exist.title = m.remark || exist.title
    }
    byConv.set(m.conversation_id, exist)
  }
  return Array.from(byConv.values()).sort(
      (a, b) => new Date(b.lastTime).getTime() - new Date(a.lastTime).getTime()
  )
})
function renderedMarkdown(text) {
  // 防止 XSS，按需设置marked选项
  return marked.parse(text ?? '', { breaks: true })
}
function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { hour12: false })
}
function isImage(path) { return !!path && /\.(png|jpe?g|gif|bmp|webp)$/i.test(path) }
function isPdf(path) { return !!path && /\.pdf$/i.test(path) }
function isTxt(path) { return !!path && /\.txt$/i.test(path) }
function fileUrl(path) {
  if (!path) return ''
  console.log("path:"+path)
  const parts = String(path).split('/')
  const filename = parts[parts.length - 1]
  // 强制使用后端端口（配置成你的实际端口和域名）
  return 'http://localhost:8080/uploads/' + filename
}

function ensureUid() {
  if (!props.userId) { alert('未检测到用户，请先登录'); return false }
  return true
}

function connect() {
  if (!ensureUid()) return
  const url = wsUrlBase + '?userId=' + encodeURIComponent(props.userId) + '&agentId=' + encodeURIComponent(agentId.value)
  ws = new WebSocket(url)
  ws.onopen = () => { connected.value = true; status.value = '已连接' }
  ws.onclose = () => { connected.value = false; status.value = '已断开' }
  ws.onerror = (e) => { status.value = '连接错误'; console.error(e) }
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data)
      if (!selectedConvId.value && data.conversation_id) {
        selectedConvId.value = data.conversation_id
        conversationId.value = String(data.conversation_id)
        currentMsgs.value = currentMsgs.value.map(m => ({
          ...m,
          conversation_id: m.conversation_id ?? data.conversation_id
        }))
      }
      allMsgs.value.push(data)
      if (!selectedConvId.value || selectedConvId.value === data.conversation_id) {
        currentMsgs.value.push(data)
      }
      scrollToBottom()
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

// 自动连接：页面加载和agentId变更时都连接
onMounted(() => {
  loadHistory()
  connect()
})
watch(agentId, (newId, oldId) => {
  disconnect()
  connect()
})

function onAgentIdChange() {
  // 下拉框变更逻辑已由watch(agentId)自动触发，无需额外逻辑
}

async function loadHistory() {
  if (!ensureUid()) return
  try {
    const res = await fetch(`${httpBase}/init?userId=${encodeURIComponent(props.userId)}`)
    const arr = await res.json()
    allMsgs.value = (arr || []).slice().sort(
        (a, b) => new Date(a.send_time) - new Date(b.send_time)
    )
    if (threads.value.length) {
      const first = threads.value[0]
      selectThread(first.id)
    } else {
      selectedConvId.value = null
      conversationId.value = ''
      currentMsgs.value = []
    }
  } catch (e) {
    allMsgs.value = []
    selectedConvId.value = null
    currentMsgs.value = []
  }
}

function selectThread(id) {
  selectedConvId.value = id
  conversationId.value = String(id)
  currentMsgs.value = allMsgs.value
      .filter(m => m.conversation_id === id)
      .sort((a, b) => new Date(a.send_time) - new Date(b.send_time))
  scrollToBottom()
}

function newConversation() {
  selectedConvId.value = null
  conversationId.value = ''
  currentMsgs.value = []
  content.value = ''
  reference.value = ''
  uploadedFileUrl.value = ''
  uploadResult.value = ''
}

function sendMessage() {
  if (!connected.value) return alert('未连接')
  if (!content.value && !reference.value) return

  const nowIso = new Date().toISOString()
  const msg = {
    conversation_id: conversationId.value ? Number(conversationId.value) : null,
    user_id: Number(props.userId),
    agent_id: agentId.value ? Number(agentId.value) : null,
    sender_type: 'user',
    sender_id: Number(props.userId),
    send_time: nowIso,
    message_seq: null,
    content: content.value,
    reference: reference.value
  }
  currentMsgs.value.push({ ...msg })
  allMsgs.value.push({ ...msg })

  try {
    ws.send(JSON.stringify(msg))
  } catch (e) {
    alert('发送失败，请重试')
  }

  content.value = ''
  reference.value = ''
  uploadedFileUrl.value = ''
  uploadResult.value = ''
  scrollToBottom()
}

function onFilePick() {
  uploadResult.value = ''
}

async function uploadFile() {
  uploadResult.value = ''
  const input = fileInput.value
  if (!input || !input.files || !input.files.length) {
    uploadResult.value = '请选择文件'
    return
  }
  if (!ensureUid()) {
    uploadResult.value = '请先登录'
    return
  }
  const file = input.files[0]
  const formData = new FormData()
  formData.append('file', file)
  formData.append('userId', props.userId)

  uploading.value = true
  try {
    const res = await fetch(fileApi, { method: 'POST', body: formData })
    const filePath = await res.text()
    uploadedFileUrl.value = filePath
    reference.value = filePath
    if (!connected.value) {
      uploadResult.value = '文件已上传，但未连接 WebSocket，无法发送消息'
      return
    }
    sendMessage()
    uploadResult.value = '已上传并发送'
  } catch (e) {
    uploadResult.value = '上传失败'
    uploadedFileUrl.value = ''
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.chat {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}
.sidebar {
  padding: 12px;
  border-radius: 16px;
  border: 1.5px solid rgba(99,198,255,0.25);
  background: linear-gradient(180deg, rgba(99,198,255,0.16), rgba(255,255,255,0.06));
  height: fit-content;
  align-self: start;
}
.sidebar-head {
  display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 10px;
}
.sidebar-head h3 { margin: 0; }
.ops { display: flex; gap: 8px; flex-wrap: wrap; }
button.sm { padding: 6px 10px; border-radius: 10px; font-size: 12px; }
button.primary {
  padding: 10px 16px; border-radius: 12px; border: none; cursor: pointer; font-weight: 800;
  background: linear-gradient(135deg, #63c6ff, #8d7bff); color: #0e1120;
}
button.ghost {
  padding: 8px 12px; border-radius: 10px; font-weight: bold;
  border: 2px solid #63c6ff;
  background: linear-gradient(135deg, rgba(99,198,255,0.35), rgba(141,123,255,0.28));
  color: #63c6ff; cursor: pointer; box-shadow: 0 1px 4px rgba(99,198,255,0.12);
}
.thread-list {
  display: grid; gap: 8px; max-height: 520px; overflow: auto;
}
.thread {
  padding: 10px; border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.18);
  background: rgba(99,198,255,0.13);
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(99,198,255,0.10);
}
.thread.active {
  border-color: #63c6ff;
  background: linear-gradient(135deg, rgba(99,198,255,0.85), rgba(141,123,255,0.40));
  color: #fff;
  box-shadow: 0 4px 14px rgba(99,198,255,0.26);
}
.thread .row1 {
  display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 6px;
}
.thread .title {
  font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 65%;
}
.thread .time {
  color: #000000; font-size: 12px; white-space: nowrap; margin-left: auto;
}
.thread .row2 .preview {
  color: #000000; font-size: 12px; opacity: 0.91; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.empty { color: #9fb0ff; font-size: 14px; padding: 12px; text-align: center; }

.main .header { margin-bottom: 8px; }
.main .hint { color: #a8b6ff; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.conv-tag {
  padding: 2px 8px; border-radius: 999px; font-size: 12px;
  border: 1.5px solid #63c6ff; color: #e3f3ff; background: rgba(99,198,255,0.11);
}
.conv-tag.new { background: rgba(99,198,255,0.23); border-color: #63c6ff; }

.bar {
  display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px;
  padding: 12px; border-radius: 14px;
  background: rgba(99,198,255,0.13); border: 1.5px solid #63c6ff;
}
.row { display: grid; grid-template-columns: 90px 1fr; align-items: center; gap: 8px; }
.row label { color: #c6d2ff; font-size: 12px; }
.row input, .row select {
  padding: 9px 10px; border-radius: 10px; border: 1.5px solid #63c6ff;
  background: #161b2e; color: #e9efff; outline: none;
}
.actions { display:flex; align-items:center; gap: 8px; }
.status { color: #63c6ff; font-size: 12px; font-weight: bold; }

.window {
  margin-top: 12px;
  border-radius: 16px; overflow: hidden;
  border: 1.5px solid #63c6ff;
  background: linear-gradient(180deg, rgba(99,198,255,0.11), rgba(255,255,255,0.02));
}

.tiny { color: #9fb0ff; font-size: 12px; }

.messages {
  max-height: 440px; overflow: auto; padding: 12px; display: grid; gap: 10px;
  background:
      radial-gradient(700px 280px at 80% 0%, rgba(99,198,255,0.13), transparent),
      radial-gradient(600px 260px at 20% 0%, rgba(141,123,255,0.09), transparent);
}
.bubble {
  max-width: 72%; padding: 10px 12px; border-radius: 14px;
  border: 1.5px solid #63c6ff;
  background: rgba(99,198,255,0.17); color: #e9efff;
  box-shadow: 0 1px 7px rgba(99,198,255,0.16);
}
.bubble.user { margin-left: auto; background: linear-gradient(135deg, rgba(99,198,255,0.29), rgba(141,123,255,0.22)); }
.bubble.agent { margin-right: auto; background: linear-gradient(135deg, rgba(141,123,255,0.27), rgba(99,198,255,0.24)); }

.meta {
  display:flex; justify-content: space-between; align-items:center; font-size: 12px; color: #e3f3ff; margin-bottom: 6px;
}
.content {
  white-space: pre-wrap;
  line-height: 1.7;
  /* 采用 #D5F3F4 到 #F0DAD2 浅色渐变背景（左青右粉）+黑色字体 */
  //background: linear-gradient(94deg, #D5F3F4 0%, #F0DAD2 100%);
  //border-radius: 8px;
  padding: 14px 22px;
  font-size: 16px;
  //box-shadow: 0 2px 12px rgba(99,198,255,0.07);
  color: #111; /* 黑色字体 */
  font-family:'Microsoft YaHei', 'Segoe UI', 'Helvetica Neue', Arial, 'PingFang SC', sans-serif;
  word-break: break-word;
  letter-spacing: 1px;
  overflow-x: auto;
}

/* 链接突出但为深色 */
.content a {
  color: #234C86;
  text-decoration: underline;
}
.conv{
  font-size: 11px;
  margin-right: 10px;
//box-shadow: 0 2px 12px rgba(99,198,255,0.07);
  color: #111; /* 黑色字体 */
  font-family: 'Times New Roman', 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  word-break: break-word;
}
.time{
  font-size: 11px;
//box-shadow: 0 2px 12px rgba(99,198,255,0.07);
  color: #111; /* 黑色字体 */
  font-family: 'Times New Roman', 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  word-break: break-word;
}

.refs { margin-top: 8px; display:flex; gap: 8px; align-items:center; flex-wrap: wrap; }
.refs img { max-height: 120px; max-width: 220px; border-radius: 10px; border: 2px solid #63c6ff; }
.ref-pill {
  padding: 6px 10px; border-radius: 999px; font-size: 12px; background: rgba(99,198,255,0.22);
  border: 1.5px solid #63c6ff; color: #63c6ff; text-decoration: none; font-weight:bold;
}
.ref-pill.pdf { background: rgba(141,123,255,0.24); }
.ref-pill.txt { background: rgba(99,198,255,0.25); }

.composer {
  border-top: 1.5px solid #63c6ff;
  padding: 10px; display: grid; gap: 10px;
  background: rgba(99,198,255,0.12);
}
.file { display:flex; align-items:center; gap: 8px; }
.preview { padding: 8px; border-radius: 10px;  }
.preview img { max-height: 140px; max-width: 240px; border-radius: 8px; border: 2px solid #63c6ff; }

.input { display: grid; grid-template-columns: 1fr auto; gap: 8px; }
.input input {
  padding: 12px; border-radius: 12px; border: 1.5px solid #63c6ff;
  background: #161b2e; color: #e9efff; outline: none;
}
.send {
  padding: 12px 16px; border-radius: 12px; border: none; cursor: pointer; font-weight: 800;
  background: linear-gradient(135deg, #63c6ff, #8d7bff); color: #0e1120;
}

/* 响应式 */
@media (max-width: 960px) {
  .chat { grid-template-columns: 1fr; }
  .messages { max-height: 60vh; }
  .bar { grid-template-columns: 1fr; }
  .row { grid-template-columns: 1fr 1fr; }
  .bubble { max-width: 100%; }
}
</style>