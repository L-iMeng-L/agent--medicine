<template>
  <div class="auth">
    <div class="grid">
      <div class="left">
        <div class="intro">
          <h1><span>欢迎来到</span><br/>AI WHU Health</h1>
          <p>登录以开始你的智能健康管理之旅。数据安全保密，操作简洁高效。</p>
          <ul class="points">
            <li>AI 健康咨询（WebSocket 实时）</li>
            <li>健康档案管理与 BMI 计算</li>
            <li>附件上传与智能参考</li>
          </ul>
        </div>
      </div>

      <div class="right glass">
        <h2 class="heading" v-if="!loggedIn">登录 / 注册</h2>
        <h2 class="heading" v-else>账户中心</h2>

        <!-- 未登录表单：仅 username / password；UID 由后端返回并自动保存 -->
        <div v-if="!loggedIn" class="form">
          <div class="row">
            <label>用户名</label>
            <input v-model="username" placeholder="username" />
          </div>
          <div class="row">
            <label>密码</label>
            <input v-model="password" type="password" placeholder="password" />
          </div>

          <div class="actions">
            <button class="primary" @click="doLogin">登录并进入</button>
            <button class="secondary" @click="doRegister">注册并进入</button>
          </div>
          <div class="result">{{ resultText }}</div>
<!--          <div class="hint">说明：登录/注册成功后会自动从后端获取并保存 UID，全程无需手动输入。</div>-->
        </div>

        <!-- 已登录视图：展示信息 + 退出 -->
        <div v-else class="account">
          <div class="profile">
            <div class="avatar">{{ (username || 'U').slice(0,2).toUpperCase() }}</div>
            <div class="info">
              <div class="u">{{ username }}</div>
              <div class="id">UID: {{ uid }}</div>
            </div>
          </div>
          <div class="actions">
            <button class="danger" @click="$emit('logout')">退出登录</button>
          </div>
        </div>
      </div>
    </div>

<!--    <div class="madefor">-->
<!--      <span>后端服务：http://localhost:8080</span>-->
<!--      <span>API：/user, /user-health, /conversation, /ws/conversation, /file/upload</span>-->
<!--    </div>-->
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  loggedIn: { type: Boolean, default: false },
  username: { type: String, default: '' },
  uid: { type: String, default: '' }
})
const emit = defineEmits(['login-success', 'logout'])

const apiBase = 'http://localhost:8080/user'

// 本地表单状态（未登录时使用）
const username = ref(props.username || '')
const password = ref('')
const uid = ref(props.uid || '')
const resultText = ref('')

watch(() => props.username, v => { if (!username.value) username.value = v || '' })
watch(() => props.uid, v => { if (!uid.value) uid.value = v || '' })

function validateBasic() {
  if (!username.value.trim()) { resultText.value = '请输入用户名'; return false }
  if (!password.value.trim()) { resultText.value = '请输入密码'; return false }
  return true
}

async function parseIdResponse(res) {
  // 兼容数值 JSON 或纯文本
  const ct = res.headers.get('content-type') || ''
  try {
    if (ct.includes('application/json')) {
      const n = await res.json()
      return Number(n)
    } else {
      const t = await res.text()
      return Number(t)
    }
  } catch {
    return NaN
  }
}

async function doLogin() {
  resultText.value = ''
  if (!validateBasic()) return
  const params = new URLSearchParams()
  params.append('username', username.value.trim())
  params.append('password', password.value.trim())
  try {
    const res = await fetch(`${apiBase}/login?${params.toString()}`, { method: 'POST' })
    const id = await parseIdResponse(res)
    if (Number.isFinite(id) && id > 0) {
      uid.value = String(id)
      emit('login-success', { username: username.value.trim(), uid: uid.value })
    } else {
      resultText.value = '登录失败：用户名或密码错误'
    }
  } catch (e) {
    resultText.value = '请求异常'
  }
}

async function doRegister() {
  resultText.value = ''
  if (!validateBasic()) return
  const params = new URLSearchParams()
  params.append('username', username.value.trim())
  params.append('password', password.value.trim())
  try {
    const res = await fetch(`${apiBase}/register?${params.toString()}`, { method: 'POST' })
    const id = await parseIdResponse(res)
    if (Number.isFinite(id) && id > 0) {
      uid.value = String(id)
      emit('login-success', { username: username.value.trim(), uid: uid.value })
    } else {
      resultText.value = '注册失败：用户名可能已存在'
    }
  } catch (e) {
    resultText.value = '请求异常'
  }
}
</script>

<style scoped>
body, html, #app { height: 100%; background: linear-gradient(180deg, var(--bg1), var(--bg2)); color: #e9efff;font-family: "微软雅黑", "Microsoft YaHei", "Consolas", "Arial", "sans-serif"; }

.auth { padding: 14px; }
.grid {
  display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 18px;
  align-items: stretch;
}
.left .intro {
  padding: 18px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.12);
  background:
      linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)),
      radial-gradient(600px 240px at 10% 0%, rgba(99,198,255,0.12), transparent 60%),
      radial-gradient(600px 240px at 80% 0%, rgba(141,123,255,0.12), transparent 60%);
}
.intro h1 { margin: 0 0 8px; font-size: 38px; line-height: 1.15; }
.intro h1 span {
  background: linear-gradient(90deg, #63c6ff, #8d7bff);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.intro p { color: #a8b6ff; margin: 6px 0 12px; }
.points { margin: 0; padding-left: 18px; color: #c7d4ff; }
.points li { margin: 6px 0; }

.right { padding: 16px; border-radius: 16px; }
.heading { margin: 0 0 10px; }

.form .row { display: grid; grid-template-columns: 110px 1fr; gap: 10px; align-items: center; margin-bottom: 10px; }
label { color: #c6fe; font-size: 13px; }
input {
  padding: 11px 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.14);
  background: rgba(10,14,32,0.4); color: #e9efff; outline: none;
}

.actions { display: flex; gap: 10px; margin-top: 6px; flex-wrap: wrap;   justify-content: space-between;
  align-items: center;}
button.primary {
  padding: 10px 16px; border-radius: 12px; border: none; cursor: pointer; font-weight: 800;
  background: linear-gradient(135deg, #63c6ff, #8d7bff); color: #0e1120;
  margin-left: 15%;
}
button.secondary {
  padding: 10px 16px; border-radius: 12px; cursor: pointer; font-weight: 800; border: none;
  background: linear-gradient(135deg, #8d7bff, #63c6ff); color: #0e1120;
  margin-right: 15%;
}
button.danger {
  padding: 10px 16px; border-radius: 12px; border: 1px solid rgba(255,120,120,0.4);
  color: #ffb3b3; background: rgba(255, 67, 67, 0.06); cursor: pointer; font-weight: 700;
}

.result { margin-top: 8px; color: #bcd0ff; font-size: 13px; min-height: 18px; }
.hint { margin-top: 6px; font-size: 12px; color: #a6b4ff; }

.account .profile {
  display:flex; align-items:center; gap: 12px; margin: 6px 0 12px;
}
.account .avatar {
  width: 40px; height: 40px; border-radius: 10px; display:grid; place-items:center; font-weight: 900; color:#0f1328;
  background: linear-gradient(135deg, #63c6ff, #8d7bff);
}
.account .info .u { font-weight: 700; }
.account .info .id { color: #a8b6ff; font-size: 12px; }

.madefor {
  margin-top: 14px; display:flex; gap: 12px; flex-wrap: wrap; color: #9fb0ff; font-size: 12px;
}

/* 响应式 */
@media (max-width: 960px) {
  .grid { grid-template-columns: 1fr; }
  .form .row { grid-template-columns: 1fr; }
}
</style>