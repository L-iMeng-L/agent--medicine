<template>
  <div class="app-shell">
    <div class="bg-aurora"></div>
    <div class="centered">
    <header class="topbar glass">
      <div class="brand" @click="goHome">
        <div class="logo">AI</div>
        <div class="title">
          <div class="name">AI WHU Health</div>
          <div class="sub">用户健康智能管理咨询</div>
        </div>
      </div>

      <nav class="nav" v-if="auth.loggedIn">
        <button :class="{active: tab==='home'}" @click="setTab('home')" aria-pressed="tab==='home'">首页</button>
        <button :class="{active: tab==='chat'}" @click="setTab('chat')" aria-pressed="tab==='chat'">AI 咨询</button>
        <button :class="{active: tab==='health'}" @click="setTab('health')" aria-pressed="tab==='health'">健康档案</button>
        <button :class="{active: tab==='account'}" @click="setTab('account')" aria-pressed="tab==='account'">账户</button>
      </nav>

      <div class="userbox" v-if="auth.loggedIn">
        <div class="chip">
          <div class="avatar">{{ initials }}</div>
          <div class="who">
            <div class="u">{{ auth.username }}</div>
            <div class="id">UID: {{ auth.uid }}</div>
          </div>
          <button class="logout" @click="logout">退出</button>
        </div>
      </div>
    </header>

    <!-- 未登录：仅显示独立登录页 -->
    <main v-if="!auth.loggedIn" class="content content-auth">
      <section class="panel glass fullscreen-auth">
        <AuthPanel @login-success="handleLogin" />
      </section>
    </main>

    <!-- 已登录：显示应用主体 -->
    <main v-else class="content">
      <section v-if="tab==='home'" class="hero">
        <div class="hero-text">
          <h1><span>用 AI 驱动健康</span><br/>让管理与咨询更智慧</h1>
          <p>连接你的健康档案，实时咨询 AI 健康助手，见证数据到洞察的每一步。</p>
          <div class="cta">
            <button class="primary" @click="setTab('chat')">开始咨询</button>
            <button class="ghost" @click="setTab('health')">查看档案</button>
          </div>
          <div class="badges">
            <span class="badge">WebSocket 实时</span>
            <span class="badge">文件上传预览</span>
            <span class="badge">轻量高性能</span>
          </div>
        </div>
        <div class="hero-visual">
          <div class="orb orb-1"></div>
          <div class="orb orb-2"></div>
          <div class="grid"></div>
        </div>
      </section>

      <section v-if="tab==='chat'" class="panel glass">
        <AIAssistantChat :user-id="auth.uid" />
      </section>

      <section v-if="tab==='health'" class="panel glass">
        <HealthRecords :user-id="auth.uid" :username="auth.username" />
      </section>

      <section v-if="tab==='account'" class="panel glass">
        <AuthPanel :logged-in="auth.loggedIn" :username="auth.username" :uid="auth.uid" @logout="logout" />
      </section>
    </main>

    <!-- 移动端底部导航（仅在已登录且小屏时显示） -->
    <nav class="mobile-nav glass" v-if="auth.loggedIn">
      <button :class="{active: tab==='home'}" @click="setTab('home')" aria-label="首页">首页</button>
      <button :class="{active: tab==='chat'}" @click="setTab('chat')" aria-label="AI 咨询">咨询</button>
      <button :class="{active: tab==='health'}" @click="setTab('health')" aria-label="健康档案">档案</button>
      <button :class="{active: tab==='account'}" @click="setTab('account')" aria-label="账户">账户</button>
    </nav>

<!--    <footer class="footer glass">-->
<!--      <div>后端服务默认：http://localhost:8080</div>-->
<!--      <div class="links">-->
<!--        <span>API：/user, /user-health, /conversation, /ws/conversation, /file/upload</span>-->
<!--      </div>-->
<!--    </footer>-->
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, onMounted, ref, watch } from 'vue'
import AIAssistantChat from './components/AIAssistantChat.vue'
import HealthRecords from './components/HealthRecords.vue'
import AuthPanel from './components/AuthPanel.vue'

const tab = ref('home')
const allowedTabs = new Set(['home','chat','health','account'])

// 简易认证状态（本地持久化）
const auth = reactive({
  loggedIn: false,
  username: '',
  uid: '' // 来自后端返回的 user_id
})

onMounted(() => {
  const savedUser = localStorage.getItem('auth.username')
  const savedUid = localStorage.getItem('auth.uid')
  const savedTab = localStorage.getItem('ui.tab')
  if (savedUser && savedUid) {
    auth.loggedIn = true
    auth.username = savedUser
    auth.uid = savedUid
  }
  if (savedTab && allowedTabs.has(savedTab)) {
    tab.value = savedTab
  }
})

watch(tab, (v) => {
  if (allowedTabs.has(v)) localStorage.setItem('ui.tab', v)
})

function setTab(v) {
  if (allowedTabs.has(v)) tab.value = v
}

function handleLogin(payload) {
  // payload: { username, uid }，uid 为后端返回 user_id
  auth.loggedIn = true
  auth.username = payload.username
  auth.uid = String(payload.uid || '')
  localStorage.setItem('auth.username', auth.username)
  localStorage.setItem('auth.uid', auth.uid)
  // 登录后，若存在上次的 tab 则恢复，否则回到首页
  const savedTab = localStorage.getItem('ui.tab')
  tab.value = (savedTab && allowedTabs.has(savedTab)) ? savedTab : 'home'
}

function logout() {
  auth.loggedIn = false
  auth.username = ''
  auth.uid = ''
  localStorage.removeItem('auth.username')
  localStorage.removeItem('auth.uid')
  // 退出后仍保留 ui.tab，方便下次登录回到原先模块
  tab.value = 'home'
}

const initials = computed(() => {
  if (!auth.username) return 'U'
  return auth.username.slice(0, 2).toUpperCase()
})

function goHome() {
  if (auth.loggedIn) setTab('home')
}
</script>

<style scoped>
:root {
  --bg1: #0b1020;
  --bg2: #0f1230;
  --card: rgba(255,255,255,0.06);
  --stroke: rgba(255,255,255,0.12);
  --text: #e9efff;
  --muted: #9fb0ff;
  --primary1: #63c6ff;
  --primary2: #8d7bff;
  --accent: #40e0d0;
}
* { box-sizing: border-box; }
body, html, #app { height: 100%; background: linear-gradient(180deg, var(--bg1), var(--bg2)); color: #e9efff;font-family: "微软雅黑", "Microsoft YaHei", "Consolas", "Arial", "sans-serif"; }
.centered {
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
  /* 适应响应式：两侧自动缩进，最大宽度 1100px */
  padding-left: 8px;
  padding-right: 8px;
  box-sizing: border-box;
}

.app-shell { position: relative; min-height: 100vh; padding: 16px; overflow: hidden; }
.bg-aurora {
  position: absolute; inset: -20% -10% auto -10%; height: 60vh;
  background:
      radial-gradient(800px 300px at 10% 10%, rgba(141,123,255,0.28), transparent 60%),
      radial-gradient(900px 400px at 90% 5%, rgba(99,198,255,0.24), transparent 60%),
      radial-gradient(600px 300px at 50% 0%, rgba(64,224,208,0.18), transparent 50%);
  filter: blur(24px);
  pointer-events: none;
  z-index: 0;
}

.glass {
  background: linear-gradient(180deg, rgba(255,255,255,0.1), rgba(255,255,255,0.04));
  border: 1px solid var(--stroke);
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 40px rgba(0,0,0,0.25);
  border-radius: 16px;
}


.brand { display:flex; align-items:center; gap:12px; cursor: pointer; user-select: none; }
.logo {
  width: 40px; height: 40px; border-radius: 10px;
  background: linear-gradient(135deg, var(--primary1), var(--primary2));
  display: grid; place-items: center; font-weight: 900; color: #101426; letter-spacing: 1px;
  box-shadow: 0 10px 30px rgba(99,198,255,0.28);
}
.title .name { font-size: 18px; font-weight: 700; }
.title .sub { font-size: 12px; color: var(--muted); }

.nav button {
  margin: 10px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid var(--stroke);
  background: #fff;
  color: #7a7a7a;
  font-weight: 600;
  cursor: pointer;
  transition:
      background 0.23s cubic-bezier(.43,.36,.84,.41),
      color 0.23s cubic-bezier(.43,.36,.84,.41);
}
.nav button.active {
  background: #fff;
  color: #181920;
  font-weight: 700;
  border-color: var(--stroke);
}
.nav button:hover {
  background: #181920;
  color: #fff;
  transition:
      background 0.25s cubic-bezier(.5,.3,.6,.8),
      color 0.25s cubic-bezier(.5,.3,.6,.8);
}

.chip {
  display:flex; align-items:center; gap:10px; padding: 6px 8px; border-radius: 14px;
  border: 1px solid var(--stroke); background: rgba(255,255,255,0.06);
}
.avatar {
  width: 32px; height: 32px; border-radius: 8px; display:grid; place-items:center; font-weight: 900; color:#0f1328;
  background: linear-gradient(135deg, var(--primary1), var(--primary2));
}
.who { display:flex; flex-direction: column; line-height: 1.1; }
.u { font-size: 12px; font-weight: 700; }
.id { font-size: 11px; color: var(--muted); }
.logout {
  margin-left: 6px; padding: 6px 10px; border-radius: 10px; border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.06); color: #e9efff; cursor: pointer; font-weight: 700;
}
.content-auth { max-width: 820px; }
.fullscreen-auth { padding: 0; overflow: hidden; }

.hero {
  display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; align-items: center;
  padding: 28px;
}
.hero-text h1 {
  font-size: 48px; line-height: 1.15; margin: 0 0 10px 0; letter-spacing: 0.5px;
}
.hero-text h1 span {
  background: linear-gradient(90deg, var(--primary1), var(--primary2));
  -webkit-background-clip: text; background-clip: text; color: transparent;
  filter: drop-shadow(0 8px 30px rgba(99,198,255,0.22));
}
.hero-text p { color: var(--muted); margin: 0 0 16px 0; font-size: 16px; }
.cta { display:flex; gap: 12px; margin: 10px 0 14px; }
.primary {
  padding: 10px 18px; border-radius: 12px; border: none; cursor: pointer; font-weight: 800;
  background: linear-gradient(135deg, var(--primary1), var(--primary2));
  color: #0e1120; box-shadow: 0 12px 30px rgba(99,198,255,0.25);
}
.ghost {
  padding: 10px 16px; border-radius: 12px; cursor: pointer; font-weight: 700;
  border: 1px solid var(--stroke); background: rgba(255,255,255,0.04); color: #e9efff;
}
.badges { display:flex; gap: 8px; flex-wrap: wrap; }
.badge {
  padding: 6px 10px; font-size: 12px; color:#0f1022; border-radius: 999px;
  background: linear-gradient(90deg, #d1e6ff, #e7e1ff);
  opacity: 0.9;
}

.hero-visual { position: relative; height: 360px; border-radius: 16px; overflow: hidden; }
.orb { position: absolute; border-radius: 50%; filter: blur(16px); }
.orb-1 { width: 220px; height: 220px; background: radial-gradient(#7b8bff, transparent); top: 20%; left: 10%; opacity: 0.55; }
.orb-2 { width: 280px; height: 280px; background: radial-gradient(#63c6ff, transparent); bottom: -10%; right: -5%; opacity: 0.5; }
.grid {
  position: absolute; inset: 0;
  background-image:
      linear-gradient(rgba(255,255,255,0.07) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.07) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(120% 80% at 50% 50%, black 60%, transparent 100%);
}

.panel { padding: 18px; }
.centered {
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
  /* 适应响应式：两侧自动缩进，最大宽度 1100px */
  padding-left: 8px;
  padding-right: 8px;
  box-sizing: border-box;
}


.topbar {
  position: sticky; top: 8px; z-index: 10;
  display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 16px;
  padding: 12px 16px;
}
.userbox { display:flex; align-items:center; gap:10px; }
.content { position: relative; z-index: 1; margin: 18px auto; max-width: 1100px; }
.footer {
  margin: 18px auto 0; max-width: 1100px;
  display:flex; justify-content: space-between; align-items:center; padding: 12px 16px; color: #9fb0ff;
  font-size: 13px;
}

/* 移动端底部导航 */
.mobile-nav {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 10px;
  z-index: 20;
  display: none; /* 默认桌面隐藏，媒体查询中显示 */
  gap: 8px;
  padding: 8px;
  border-radius: 16px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
.mobile-nav button {
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.04);
  color: #e9efff;
  min-width: 64px;
}
.mobile-nav button.active {
  background: linear-gradient(135deg, var(--primary1), var(--primary2));
  color: #0f1120;
  border-color: transparent;
}

/* 响应式 */
@media (max-width: 960px) {
  .topbar { grid-template-columns: 1fr auto; }
  .nav { display: none; }
  .hero { grid-template-columns: 1fr; }
  .mobile-nav { display: grid; grid-auto-flow: column; }
  .content { padding-bottom: 84px; } /* 给底部导航留出空间，避免遮挡内容 */
}
</style>