<template>
  <div>
    <h2>健康档案接口测试</h2>

    <div class="panel">
      <h3>查询记录</h3>
      <div class="row">
        <div class="label">User ID</div>
        <input v-model="userId" class="field" placeholder="输入 user_id (数字)" />
        <button @click="loadRecords">查询</button>
      </div>
      <div class="list">
        <div v-for="r in records" :key="r.record_id" class="row">
          <div class="field">
            <strong>{{ r.date }}</strong> BMI: {{ r.bmi }} — Height: {{ r.height_cm }} cm
            <div class="small">ref: {{ r.record_id }} </div>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <h3>新增记录（示例）</h3>
      <div class="row">
        <div class="label">身高(cm)</div>
        <input v-model="height" class="field" />
      </div>
      <div class="row">
        <div class="label">体重(kg)</div>
        <input v-model="weight" class="field" />
      </div>
      <div class="row">
        <div class="label">User ID</div>
        <input v-model="userIdForAdd" class="field" />
      </div>
      <button @click="addRecord">添加记录</button>
      <span class="small">{{ addResult }}</span>
    </div>

    <div class="panel">
      <h3>清空用户记录</h3>
      <div class="row">
        <div class="label">User ID</div>
        <input v-model="userIdToClear" class="field" />
        <button @click="clearRecords">清空</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const base = '/user-health'

const userId = ref('')
const records = ref([])

const height = ref('170')
const weight = ref('65')
const userIdForAdd = ref('')
const addResult = ref('')
const userIdToClear = ref('')

async function loadRecords() {
  if (!userId.value) return alert('请输入 user id')
  try {
    const res = await fetch(`${base}/records?uid=${encodeURIComponent(userId.value)}`)
    records.value = await res.json()
  } catch (e) { records.value = [] }
}

async function addRecord() {
  if (!userIdForAdd.value) return alert('请输入 user id')
  const body = {
    user_id: Number(userIdForAdd.value),
    height_cm: parseFloat(height.value),
    weight_kg: parseFloat(weight.value),
    bmi: (parseFloat(weight.value) / ((parseFloat(height.value) / 100) ** 2)).toFixed(2),
    date: new Date().toISOString()
  }
  try {
    const res = await fetch(`${base}/record`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    })
    addResult.value = await res.text()
    loadRecords()
  } catch (e) { addResult.value = '请求异常' }
}

async function clearRecords() {
  if (!userIdToClear.value) return alert('请输入 user id')
  if (!confirm('确认清空？')) return
  try {
    const res = await fetch(`${base}/records?uid=${encodeURIComponent(userIdToClear.value)}`, { method: 'DELETE' })
    const ok = await res.text()
    alert(ok === 'true' ? '已清空' : '清空失败')
    loadRecords()
  } catch (e) { alert('请求异常') }
}
</script>

<style scoped>
h2 { margin-top:0 }
</style>