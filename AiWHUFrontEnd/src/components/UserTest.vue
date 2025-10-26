<template>
  <div>
    <h2>用户接口测试</h2>

    <div class="panel">
      <h3>注册</h3>
      <div class="row">
        <div class="label">用户名</div>
        <input v-model="regName" class="field" placeholder="username" />
      </div>
      <div class="row">
        <div class="label">密码</div>
        <input v-model="regPass" type="password" class="field" placeholder="password" />
      </div>
      <button @click="register">Register</button>
      <span class="small">{{ regResult }}</span>
    </div>

    <div class="panel">
      <h3>登录</h3>
      <div class="row">
        <div class="label">用户名</div>
        <input v-model="loginName" class="field" />
      </div>
      <div class="row">
        <div class="label">密码</div>
        <input v-model="loginPass" type="password" class="field" />
      </div>
      <button @click="login">Login</button>
      <span class="small">{{ loginResult }}</span>
    </div>

    <div class="panel">
      <h3>用户列表 & 操作</h3>
      <button @click="loadUsers">刷新用户列表</button>
      <div class="list">
        <div v-for="u in users" :key="u.user_id" class="row">
          <div class="field">ID: {{ u.user_id }} — {{ u.username }}</div>
          <button @click="deleteUser(u.username)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const apiBase = 'http://localhost:8080/user'

const regName = ref('')
const regPass = ref('')
const regResult = ref('')

const loginName = ref('')
const loginPass = ref('')
const loginResult = ref('')

const users = ref([])

async function register() {
  regResult.value = '...'
  const params = new URLSearchParams()
  params.append('username', regName.value)
  params.append('password', regPass.value)
  try {
    const res = await fetch(`${apiBase}/register?${params.toString()}`, { method: 'POST' })
    const ok = await res.text()
    regResult.value = ok === 'true' ? '注册成功' : '注册失败（可能已存在）'
    if (ok === 'true') await loadUsers()
  } catch (e) { regResult.value = '请求异常' }
}

async function login() {
  loginResult.value = '...'
  const params = new URLSearchParams()
  params.append('username', loginName.value)
  params.append('password', loginPass.value)
  try {
    const res = await fetch(`${apiBase}/login?${params.toString()}`, { method: 'POST' })
    const ok = await res.text()
    loginResult.value = ok === 'true' ? '登录成功' : '登录失败'
  } catch (e) { loginResult.value = '请求异常' }
}

async function loadUsers() {
  try {
    const res = await fetch(`${apiBase}/all`)
    users.value = await res.json()
  } catch (e) { users.value = [] }
}

async function deleteUser(username) {
  if (!confirm(`确认删除用户 ${username} ?`)) return
  try {
    const res = await fetch(`${apiBase}/delete?username=${encodeURIComponent(username)}`, { method: 'DELETE' })
    const ok = await res.text()
    alert(ok === 'true' ? '删除成功' : '删除失败')
    loadUsers()
  } catch (e) { alert('请求异常') }
}

// 初次加载
loadUsers()
</script>

<style scoped>
h2 { margin-top:0 }
.panel h3 { margin:0 0 8px 0 }
</style>