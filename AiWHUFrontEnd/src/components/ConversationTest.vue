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
        <div class="hint">
          实时 WebSocket 对话，支持图片/PDF/TXT 附件
          <span v-if="selectedConvId" class="conv-tag">会话ID: {{ selectedConvId }}</span>
          <!--          <span v-else class="conv-tag new">新建会话</span>-->
        </div>
      </div>

      <div class="bar">
        <div class="row">
          <label>会话ID</label>
          <input v-model="conversationId" placeholder="可空（新建会话）" />
        </div>
        <div class="row">
          <label>Agent ID</label>
          <input v-model="agentId" placeholder="可空" />
        </div>
        <div class="actions">
          <button class="connect" @click="connect" :disabled="connected">连接</button>
          <button class="disconnect" @click="disconnect" :disabled="!connected">断开</button>
          <span class="status">{{ status }}</span>
        </div>
      </div>

      <div class="window">
        <!--        <div class="history-hint">-->
        <!--          <button class="ghost" @click="loadHistory">载入历史</button>-->
        <!--&lt;!&ndash;          <span class="tiny">从 /conversation/init 拉取所有历史消息 (HTTP)</span>&ndash;&gt;-->
        <!--        </div>-->

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
            <div class="content">{{ m.content }}</div>

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
import { ref, nextTick, computed, onMounted } from 'vue'
const httpBase = 'http://localhost:8080/conversation'
const fileApi = 'http://localhost:8080/file/upload'
const wsUrlBase = (location.protocol === 'https:' ? 'wss' : 'ws') + '://' + location.hostname + ':8080/ws/conversation'
let ws = null

const props = defineProps({
  userId: { type: String, required: true }
})

// 顶部表单与状态
const conversationId = ref('')        // 文本框显示/控制；真正选择的会话由 selectedConvId 维护
const agentId = ref('')
const content = ref('')
const reference = ref('')

// 连接状态
const connected = ref(false)
const status = ref('未连接')

// 历史与当前展示
const allMsgs = ref([])               // 所有消息（包含全部会话）
const currentMsgs = ref([])           // 当前选中会话的消息
const selectedConvId = ref(null)      // 当前选中会话ID（number）

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

// 侧栏会话线程（按最后消息时间倒序）
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
    // 更新最后时间与最后一条内容
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

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { hour12: false })
}
function isImage(path) { return !!path && /\.(png|jpe?g|gif|bmp|webp)$/i.test(path) }
function isPdf(path) { return !!path && /\.pdf$/i.test(path) }
function isTxt(path) { return !!path && /\.txt$/i.test(path) }
function fileUrl(path) {
  if (!path) return ''
  const parts = String(path).split('/')
  console.log("uploaded:"+path)
  return parts[parts.length - 1]
}

function ensureUid() {
  if (!props.userId) { alert('未检测到用户，请先登录'); return false }
  return true
}

function connect() {
  if (!ensureUid()) return
  const url = wsUrlBase + '?userId=' + encodeURIComponent(props.userId)
  ws = new WebSocket(url)
  ws.onopen = () => { connected.value = true; status.value = '已连接' }
  ws.onclose = () => { connected.value = false; status.value = '已断开' }
  ws.onerror = (e) => { status.value = '连接错误'; console.error(e) }
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data) // 这是 agent 的回复
      // 如果是新建会话的首条回复，后端会带上 conversation_id
      if (!selectedConvId.value && data.conversation_id) {
        selectedConvId.value = data.conversation_id
        conversationId.value = String(data.conversation_id)
        // 把当前窗口里之前的本地 user 气泡（无 convId）补上 convId
        currentMsgs.value = currentMsgs.value.map(m => ({
          ...m,
          conversation_id: m.conversation_id ?? data.conversation_id
        }))
      }
      // 汇总到总列表
      allMsgs.value.push(data)
      // 如果是当前会话，落入右侧窗口
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

async function loadHistory() {
  if (!ensureUid()) return
  try {
    const res = await fetch(`${httpBase}/init?userId=${encodeURIComponent(props.userId)}`)
    const arr = await res.json()
    // 所有消息按发送时间升序
    allMsgs.value = (arr || []).slice().sort(
        (a, b) => new Date(a.send_time) - new Date(b.send_time)
    )
    // 默认选择最近活跃的会话
    if (threads.value.length) {
      const first = threads.value[0]
      selectThread(first.id)
    } else {
      // 没有历史则清空当前
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
  // 清空当前窗口与选择，等待首条消息创建会话
  selectedConvId.value = null
  conversationId.value = ''
  currentMsgs.value = []
  content.value = ''
  reference.value = ''
  uploadedFileUrl.value = ''
  uploadResult.value = ''
}

function sendMessage() {
  console.log(reference.value)//todo
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
  // 先把用户消息落地到 UI（本地气泡）
  currentMsgs.value.push({ ...msg })
  allMsgs.value.push({ ...msg })

  // 通过 WS 发送给后端；后端保存并返回 agent 回复（含 conversation_id）
  try {
    ws.send(JSON.stringify(msg))
  } catch (e) {
    alert('发送失败，请重试')
  }

  // 清理输入框与附件，仅保留 UI 里的preview
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
    console.log("uploadFilePath:"+filePath)
    if (!connected.value) {
      uploadResult.value = '文件已上传，但未连接 WebSocket，无法发送消息'
      return
    }

// 立即发送（允许只有附件没有文本）
    sendMessage()
    uploadResult.value = '已上传并发送'
  } catch (e) {
    uploadResult.value = '上传失败'
    uploadedFileUrl.value = ''
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  // 进入页面自动加载历史
  loadHistory()
})
</script>

<style scoped>
/* 布局：左侧侧栏 + 右侧主窗 */
.chat {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
}

/* 左侧侧栏 */
.sidebar {
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.12);
  background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
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
  padding: 8px 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.04); color: #e9efff; cursor: pointer;
}

.thread-list {
  display: grid; gap: 8px; max-height: 520px; overflow: auto;
}
.thread {
  padding: 10px; border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.05);
  cursor: pointer;
}
.thread.active {
  border-color: transparent;
  background: linear-gradient(135deg, rgba(99,198,255,0.25), rgba(141,123,255,0.18));
}
.thread .row1 {
  display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 6px;
}
.thread .title {
  font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 65%;
}
.thread .time {
  color: #bcd0ff; font-size: 12px; white-space: nowrap; margin-left: auto;
}
.thread .row2 .preview {
  color: #c7d4ff; font-size: 12px; opacity: 0.9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.empty { color: #9fb0ff; font-size: 14px; padding: 12px; text-align: center; }

/* 右侧主区域：沿用原样式并适配标签 */
.main .header { margin-bottom: 8px; }
.main .hint { color: #a8b6ff; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.conv-tag {
  padding: 2px 8px; border-radius: 999px; font-size: 12px;
  border: 1px solid rgba(255,255,255,0.18); color: #e9efff; background: rgba(255,255,255,0.05);
}
.conv-tag.new { background: rgba(99,198,255,0.15); border-color: rgba(99,198,255,0.35); }

.bar {
  display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px;
  padding: 12px; border-radius: 14px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
}
.row { display: grid; grid-template-columns: 90px 1fr; align-items: center; gap: 8px; }
.row label { color: #c6d2ff; font-size: 12px; }
.row input {
  padding: 9px 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.14);
  background: rgba(10,14,32,0.4); color: #e9efff; outline: none;
}
.actions { display:flex; align-items:center; gap: 8px; }
.connect {
  padding: 9px 14px; border-radius: 10px; border: none; cursor: pointer; font-weight: 800;
  background: linear-gradient(135deg, #63c6ff, #8d7bff); color: #0e1120;
}
.disconnect {
  padding: 9px 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.06); color: #e9efff; cursor: pointer; font-weight: 700;
}
.status { color: #bcd0ff; font-size: 12px; }

.window {
  margin-top: 12px;
  border-radius: 16px; overflow: hidden;
  border: 1px solid rgba(255,255,255,0.12);
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
}
.history-hint {
  display:flex; align-items:center; gap: 10px; padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.1);
}
.tiny { color: #9fb0ff; font-size: 12px; }

.messages {
  max-height: 440px; overflow: auto; padding: 12px; display: grid; gap: 10px;
  background:
      radial-gradient(700px 280px at 80% 0%, rgba(99,198,255,0.08), transparent),
      radial-gradient(600px 260px at 20% 0%, rgba(141,123,255,0.08), transparent);
}
.bubble {
  max-width: 72%; padding: 10px 12px; border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.06); color: #e9efff;
}
.bubble.user { margin-left: auto; background: linear-gradient(135deg, rgba(99,198,255,0.18), rgba(141,123,255,0.12)); }
.bubble.agent { margin-right: auto; background: linear-gradient(135deg, rgba(141,123,255,0.18), rgba(99,198,255,0.12)); }

.meta {
  display:flex; justify-content: space-between; align-items:center; font-size: 12px; color: #bcd0ff; margin-bottom: 6px;
}
.content { white-space: pre-wrap; line-height: 1.5; }

.refs { margin-top: 8px; display:flex; gap: 8px; align-items:center; flex-wrap: wrap; }
.refs img { max-height: 120px; max-width: 220px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.18); }
.ref-pill {
  padding: 6px 10px; border-radius: 999px; font-size: 12px; background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.18); color: #e9efff; text-decoration: none;
}
.ref-pill.pdf { background: rgba(141,123,255,0.18); }
.ref-pill.txt { background: rgba(99,198,255,0.18); }

.composer {
  border-top: 1px solid rgba(255,255,255,0.1);
  padding: 10px; display: grid; gap: 10px;
  background: rgba(0,0,0,0.1);
}
.file { display:flex; align-items:center; gap: 8px; }
.preview { padding: 8px; border-radius: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); }
.preview img { max-height: 140px; max-width: 240px; border-radius: 8px; }

.input { display: grid; grid-template-columns: 1fr auto; gap: 8px; }
.input input {
  padding: 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.14);
  background: rgba(10,14,32,0.4); color: #e9efff; outline: none;
}
.send {
  padding: 12px 16px; border-radius: 12px; border: none; cursor: pointer; font-weight: 800;
  background: linear-gradient(135deg, #63c6ff, #8d7bff); color: #0e1120;
}

/* 响应式：移动端折叠为单列，侧栏挪到顶部 */
@media (max-width: 960px) {
  .chat { grid-template-columns: 1fr; }
  .messages { max-height: 60vh; }
  .bar { grid-template-columns: 1fr; }
  .row { grid-template-columns: 1fr 1fr; }
  .bubble { max-width: 100%; }
}

</style>