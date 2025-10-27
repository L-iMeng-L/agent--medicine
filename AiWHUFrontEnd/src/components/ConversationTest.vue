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
          <div class="small">from: {{ m.sender_type }} ({{ m.sender_id }}) at {{ formatDate(m.send_time) }}<br/>ref:
            <template v-if="isImage(m.reference)">
              <a :href="fileUrl(m.reference)" target="_blank"><img :src="fileUrl(m.reference)" alt="图片附件" style="max-height:40px;max-width:100px;border-radius:3px;vertical-align:middle;margin:2px;" /></a>
            </template>
            <template v-else-if="isPdf(m.reference)">
              <a :href="fileUrl(m.reference)" target="_blank">PDF文件</a>
            </template>
            <template v-else-if="isTxt(m.reference)">
              <a :href="fileUrl(m.reference)" target="_blank">TXT文件</a>
            </template>
            <template v-else>
              {{ m.reference }}
            </template>
          </div>
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
        <input v-model="reqRef" class="field" placeholder="可通过下方上传获得" readonly />
      </div>
      <!-- 文件上传部分 -->
      <div class="row">
        <div class="label">上传文件</div>
        <input type="file" ref="fileInput" />
        <button class="upload-btn" @click="uploadFile">上传</button>
        <span class="small" v-if="uploadResult">{{ uploadResult }}</span>
      </div>
      <div v-if="uploadedFileUrl" class="uploaded-preview">
        <template v-if="isImage(uploadedFileUrl)">
          <span>图片预览：</span>
          <img :src="fileUrl(uploadedFileUrl)" alt="图片" style="max-height:80px;max-width:200px;border-radius:6px;margin:2px;" />
        </template>
        <template v-else-if="isPdf(uploadedFileUrl)">
          <span>PDF预览：</span>
          <a :href="fileUrl(uploadedFileUrl)" target="_blank" style="color:#3a6cff;">点击查看PDF</a>
        </template>
        <template v-else-if="isTxt(uploadedFileUrl)">
          <span>TXT文件：</span>
          <a :href="fileUrl(uploadedFileUrl)" target="_blank" style="color:#3a6cff;">点击下载</a>
        </template>
        <template v-else>
          <span>文件地址：</span>{{ uploadedFileUrl }}
        </template>
      </div>
      <button class="send-btn" @click="addMsg">发送(HTTP)</button>
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
const base = 'http://localhost:8080/conversation'
const fileApi = 'http://localhost:8080/file/upload'

const userId = ref('')
const messages = ref([])

const convId = ref('')
const reqUserId = ref('')
const reqAgentId = ref('')
const reqContent = ref('')
const reqRef = ref('')

const delUserId = ref('')
const delConvId = ref('')

const fileInput = ref(null)
const uploadResult = ref('')
const uploadedFileUrl = ref('')

function formatDate(dateStr) {
  if (!dateStr) return ''
  // 适配数据库/后端输出格式
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { hour12: false })
}

function isImage(path) {
  if (!path) return false
  return /\.(png|jpg|jpeg|gif|bmp)$/i.test(path)
}
function isPdf(path) {
  if (!path) return false
  return /\.pdf$/i.test(path)
}
function isTxt(path) {
  if (!path) return false
  return /\.txt$/i.test(path)
}
function fileUrl(path) {
  // 如果 path 为绝对磁盘路径，需转换为静态资源URL（假设后端映射 /uploads/）
  // 例如 /data/upload/xxx.pdf -> /uploads/xxx.pdf
  if (!path) return ''
  const parts = path.split('/')
  return '/uploads/' + parts[parts.length - 1]
}

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

// 文件上传逻辑
async function uploadFile() {
  uploadResult.value = ''
  const input = fileInput.value
  if (!input || !input.files.length) {
    uploadResult.value = '请选择文件'
    return
  }
  const file = input.files[0]
  const formData = new FormData()
  formData.append('file', file)
  formData.append('userId', reqUserId.value)
  try {
    const res = await fetch(fileApi, {
      method: 'POST',
      body: formData
    })
    const filePath = await res.text()
    reqRef.value = filePath
    uploadedFileUrl.value = filePath
    uploadResult.value = '已上传，路径已自动填入'
  } catch (e) {
    uploadResult.value = '上传失败'
    uploadedFileUrl.value = ''
  }
}
</script>

<style scoped>
h2 { margin-top:0 }
.panel { border:1px solid #e6e9f0; padding:14px 18px; border-radius:9px; background:#f8faff; margin-bottom:18px; box-shadow:0 2px 12px rgba(150,170,255,0.04);}
.row { display:flex; gap:12px; align-items:center; margin-bottom:12px; }
.label { width:120px; color:#222; font-weight:500; }
.field { flex:1; padding:6px 8px; border-radius:6px; border:1px solid #d2d9e7; background:#fff;}
.upload-btn, .send-btn { padding:7px 18px; border-radius:7px; border:none; background:linear-gradient(90deg,#62c1fa,#7b98ff); color:#fff; cursor:pointer; font-weight:600;}
.upload-btn:hover, .send-btn:hover { background:linear-gradient(90deg,#7b98ff,#62c1fa); }
.list { max-height:380px; overflow:auto; border:1px dashed #c6d7fd; padding:10px; border-radius:7px; background:#fff; }
.msg { padding:9px 12px; margin-bottom:8px; border-radius:7px; font-size:15px;}
.msg.user { background:#e8f7ff; border:1px solid #bfe9ff; }
.msg.agent { background:#fff6e6; border:1px solid #ffd89b; }
.small { font-size:13px; color:#666; }
.uploaded-preview { margin-top:8px; background:#f5faff; border-radius:7px; padding:10px 14px; box-shadow:0 2px 8px rgba(170,200,255,0.06);}
</style>