<template>
  <div class="health">
    <div class="header">
      <h2>健康档案</h2>
    </div>

    <!-- 个人健康档案（基础信息） -->
    <div class="card profile">
      <div class="profile-head">
        <h3>个人健康档案</h3>
        <div class="ops">
          <button class="ghost" @click="loadProfile">刷新</button>
          <button class="danger" :disabled="!profile.info_id" @click="deleteProfile">删除档案</button>
        </div>
      </div>

      <div class="grid-2-compact">
        <div class="row">
          <label>姓名</label>
          <input v-model="profile.name" placeholder="请输入姓名" />
        </div>
        <div class="row">
          <label>生日</label>
          <input v-model="profile.birth_date" type="date" placeholder="YYYY-MM-DD" />
        </div>
        <div class="row">
          <label>手机</label>
          <input v-model="profile.phone" placeholder="11位手机号" />
        </div>
        <div class="row">
          <label>邮箱</label>
          <input v-model="profile.email" placeholder="example@domain.com" />
        </div>
      </div>

      <div class="actions">
        <button class="primary" @click="saveProfile">{{ profile.info_id ? '保存修改' : '创建档案' }}</button>
        <span class="result">{{ profileResult }}</span>
      </div>
    </div>

    <!-- 切换标签：查询记录 / 新增记录 -->
    <div class="tabs">
      <button :class="['tab', { active: activeTab === 'records' }]" @click="activeTab = 'records'">查询 / 管理记录</button>
      <button :class="['tab', { active: activeTab === 'new' }]" @click="activeTab = 'new'">新增记录</button>
    </div>

    <!-- 查询记录视图（固定宽度单卡 + 限制三个标签） -->
    <div v-if="activeTab === 'records'" class="grid-2">
      <div class="card">
        <h3>查询记录</h3>

        <div class="row">
          <button  @click="loadRecords">查询</button>
<!--          <div class="muted">最新在前</div>-->
        </div>

        <div v-if="!sortedRecords.length" class="list">
          <div class="empty">暂无数据</div>
        </div>

        <div
            v-else
            class="carousel fixed"
            ref="carouselRef"
            @touchstart.passive="onTouchStart"
            @touchmove.prevent="onTouchMove"
            @touchend.passive="onTouchEnd"
            @mousedown.prevent="onMouseDown"
            @mousemove.prevent="onMouseMove"
            @mouseup.prevent="onMouseUp"
            @mouseleave.prevent="onMouseLeave"
        >
          <div class="carousel-stack">
            <div
                class="slide"
                v-for="(r, idx) in sortedRecords"
                :key="r.record_id || idx"
                :class="{ active: idx === activeIndex }"
            >
              <div class="slide-inner">
                <div class="slide-row">
                  <span class="k">时间</span>
                  <span class="v">{{ formatDate(r.date) }}</span>
                </div>
                <div class="slide-row">
                  <span class="k">BMI</span>
                  <span class="v emph">{{ r.bmi }}</span>
                </div>
                <div class="slide-row">
                  <span class="k">身高/体重</span>
                  <span class="v">{{ r.height_cm }} cm / {{ r.weight_kg }} kg</span>
                </div>
                <div class="slide-row">
                  <span class="k">心率</span>
                  <span class="v">{{ r.heart_rate ?? '-' }} 次/分</span>
                </div>
                <div class="slide-row">
                  <span class="k">血糖</span>
                  <span class="v">{{ r.blood_sugar ?? '-' }} mmol/L</span>
                </div>
                <div class="slide-meta">record_id: {{ r.record_id }}</div>
              </div>
            </div>
          </div>

          <button class="nav prev" :disabled="!canPrev" @click="prevSlide" aria-label="上一条">‹</button>
          <button class="nav next" :disabled="!canNext" @click="nextSlide" aria-label="下一条">›</button>

          <!-- 仅三个标签 -->
          <div class="dots three">
            <button
                v-for="i in dotIndexes"
                :key="i"
                :class="['dot', { active: i === activeIndex }]"
                @click="dotClick(i)"
                :aria-label="`跳转到第 ${i+1} 条`"
                :disabled="i === activeIndex"
            />
          </div>
        </div>
      </div>

      <div class="card">
        <h3>清空用户记录</h3>
        <div class="row">
          <label>当前用户</label>
          <div class="static">{{ userName || userId }}</div>
          <button class="danger" @click="clearRecords">清空</button>
        </div>
      </div>
    </div>
    <div v-if="activeTab === 'records'" class="grid-1">
      <!-- 替换原来的 hello 部分（位于 <div v-if="activeTab === 'records'" class="grid-1"> 内） -->
      <div class="chart-wrapper">
        <div class="chart-head">
          <h3>日均趋势（身高/体重/BMI）</h3>
          <div class="legend">
            <span class="lg-item lg-height">身高</span>
            <span class="lg-item lg-weight">体重</span>
            <span class="lg-item lg-bmi">BMI</span>
          </div>
        </div>

        <div v-if="!dailyAverages.length" class="empty">暂无可绘制数据</div>

        <div v-else class="chart-box" ref="chartBoxRef" @mouseleave="clearHover">
          <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" :width="svgWidth" :height="svgHeight">
            <!-- 坐标轴 -->
            <g class="axes">
              <!-- X 轴 -->
              <line :x1="padding.left" :y1="svgHeight - padding.bottom"
                    :x2="svgWidth - padding.right" :y2="svgHeight - padding.bottom"
                    stroke="var(--axis)" stroke-width="1"/>
              <!-- 左 Y 轴 (身高/体重) -->
              <line :x1="padding.left" :y1="padding.top"
                    :x2="padding.left" :y2="svgHeight - padding.bottom"
                    stroke="var(--axis)" stroke-width="1"/>
              <!-- 右 Y 轴 (BMI) -->
              <line :x1="svgWidth - padding.right" :y1="padding.top"
                    :x2="svgWidth - padding.right" :y2="svgHeight - padding.bottom"
                    stroke="var(--axis)" stroke-width="1" stroke-dasharray="4 3"/>
            </g>

            <!-- X 轴刻度与日期标签 -->
            <g class="x-ticks">
              <template v-for="(label,i) in xTickData" :key="'X'+i">
                <line :x1="x(i)" :x2="x(i)"
                      :y1="svgHeight - padding.bottom"
                      :y2="svgHeight - padding.bottom + 6"
                      stroke="var(--axis)" stroke-width="1"/>
                <text v-if="label"
                      :x="x(i)" :y="svgHeight - padding.bottom + 18"
                      text-anchor="middle" class="tick-label">{{ label }}</text>
              </template>
            </g>

            <!-- 左侧 Y 轴刻度 (身高/体重最大值域) -->
            <g class="y-ticks-left">
              <template v-for="v in leftAxisTicks" :key="'L'+v">
                <line
                    :x1="padding.left - 6" :x2="padding.left"
                    :y1="yLeft(v)" :y2="yLeft(v)"
                    stroke="var(--axis)" stroke-width="1"/>
                <text
                    :x="padding.left - 10" :y="yLeft(v) + 4"
                    text-anchor="end"
                    class="tick-label">{{ v }}</text>
              </template>
              <text :x="padding.left - 12" :y="padding.top - 6" text-anchor="end" class="axis-title">身高/体重</text>
            </g>

            <!-- 右侧 Y 轴刻度 (BMI) -->
            <g class="y-ticks-right">
              <template v-for="v in rightAxisTicks" :key="'R'+v">
                <line
                    :x1="svgWidth - padding.right" :x2="svgWidth - padding.right + 6"
                    :y1="yRight(v)" :y2="yRight(v)"
                    stroke="var(--axis)" stroke-width="1"/>
                <text
                    :x="svgWidth - padding.right + 10" :y="yRight(v)+4"
                    text-anchor="start"
                    class="tick-label">{{ v }}</text>
              </template>
              <text :x="svgWidth - padding.right + 12" :y="padding.top - 6" text-anchor="start" class="axis-title">BMI</text>
            </g>

            <!-- 身高 -->
            <template v-if="dailyAverages.length === 1">
              <circle
                  :cx="dataX(0)"
                  :cy="yLeftData(dailyAverages[0].avgHeight)"
                  r="4"
                  class="dot-height"
              />
            </template>
            <polyline
                v-else-if="dailyAverages.length > 1"
                :points="polylinePoints('height')"
                class="line-height"
                fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"
            />
            <!-- 折线：体重 -->
            <polyline
                v-if="dailyAverages.length"
                :points="polylinePoints('weight')"
                class="line-weight"
                fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"
            />
            <!-- 折线：BMI -->
            <polyline
                v-if="dailyAverages.length"
                :points="polylinePoints('bmi')"
                class="line-bmi"
                fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"
            />

            <!-- Hover 圆点与垂线 -->
            <g v-if="hoverIndex !== null">
              <line
                  :x1="dataX(hoverIndex)"
                  :x2="dataX(hoverIndex)"
                  :y1="padding.top + axisGapY"
                  :y2="svgHeight - padding.bottom - axisGapY"
                  stroke="var(--hover-line)"
                  stroke-width="1"
                  stroke-dasharray="4 3"
              />
              <circle :cx="dataX(hoverIndex)" :cy="yLeftData(dailyAverages[hoverIndex].avgHeight)" r="4" class="dot-height"/>
              <circle :cx="dataX(hoverIndex)" :cy="yLeftData(dailyAverages[hoverIndex].avgWeight)" r="4" class="dot-weight"/>
              <circle :cx="dataX(hoverIndex)" :cy="yRightData(dailyAverages[hoverIndex].avgBmi)" r="4" class="dot-bmi"/>
            </g>

            <!-- 交互点（透明的大圆，用于捕获鼠标） -->
            <g class="hit-area">
              <template v-for="(d,i) in dailyAverages" :key="'H'+d.day">
                <circle
                    :cx="dataX(i)"
                    :cy="svgHeight/2"
                    :r="hitRadius"
                    fill="transparent"
                    @mouseenter="setHover(i)"
                    @focus="setHover(i)"
                />
              </template>
            </g>
          </svg>

          <!-- 悬浮提示框 -->
          <div v-if="hoverIndex !== null" class="tooltip" :style="tooltipStyle">
            <div class="tt-day">{{ dailyAverages[hoverIndex].day }}</div>
            <div class="tt-row"><span>身高</span>{{ dailyAverages[hoverIndex].avgHeight.toFixed(2) }} cm</div>
            <div class="tt-row"><span>体重</span>{{ dailyAverages[hoverIndex].avgWeight.toFixed(2) }} kg</div>
            <div class="tt-row"><span>BMI</span>{{ dailyAverages[hoverIndex].avgBmi.toFixed(2) }}</div>
          </div>
        </div>
        <div class="chart-foot-note">提示：同一天多条记录已取均值。左右拖动或移动鼠标查看具体数值。</div>
      </div>
    </div>
    <!-- 新增记录视图 -->
    <div v-if="activeTab === 'new'" class="card new-record-card">
      <h3>新增健康记录</h3>

      <div class="grid-form">
        <div class="row">
          <label>身高 (cm)</label>
          <input v-model="height" />
          <div class="hint-small">必填</div>
        </div>
        <div class="row">
          <label>体重 (kg)</label>
          <input v-model="weight" />
          <div class="hint-small">必填</div>
        </div>
        <div class="row">
          <label>BMI</label>
          <div class="static">{{ computedBmi }}</div>
          <div class="hint-small">自动计算</div>
        </div>
        <div class="row">
          <label>血型</label>
          <input v-model="blood_type" placeholder="A / B / AB / O / 其他" />
        </div>
        <div class="row">
          <label>收缩压</label>
          <input v-model="blood_pressure_systolic" placeholder="mmHg" />
        </div>
        <div class="row">
          <label>舒张压</label>
          <input v-model="blood_pressure_diastolic" placeholder="mmHg" />
        </div>
        <div class="row">
          <label>心率</label>
          <input v-model="heart_rate" placeholder="次/分钟" />
        </div>
        <div class="row">
          <label>体温 (℃)</label>
          <input v-model="body_temperature" placeholder="例如 36.6" />
        </div>
        <div class="row">
          <label>血糖 (mmol/L)</label>
          <input v-model="blood_sugar" />
        </div>
        <div class="row">
          <label>总胆固醇</label>
          <input v-model="cholesterol_total" placeholder="mmol/L" />
        </div>
        <div class="row">
          <label>LDL</label>
          <input v-model="cholesterol_ldl" placeholder="mmol/L" />
        </div>
        <div class="row">
          <label>HDL</label>
          <input v-model="cholesterol_hdl" placeholder="mmol/L" />
        </div>
        <div class="row">
          <label>甘油三酯</label>
          <input v-model="triglycerides" placeholder="mmol/L" />
        </div>
        <div class="row">
          <label>左眼视力</label>
          <input v-model="vision_left" placeholder="例如 1.0" />
        </div>
        <div class="row">
          <label>右眼视力</label>
          <input v-model="vision_right" placeholder="例如 1.0" />
        </div>
        <div class="row">
          <label>吸烟状况</label>
          <input v-model="smoking_status" placeholder="不吸烟 / 偶尔 / 经常" />
        </div>
        <div class="row">
          <label>饮酒状况</label>
          <input v-model="drinking_status" placeholder="不喝 / 偶尔 / 经常" />
        </div>
        <div class="row">
          <label>锻炼频率</label>
          <input v-model="exercise_frequency" placeholder="例如 每周3次" />
        </div>
        <div class="row">
          <label>睡眠时长 (小时)</label>
          <input v-model="sleep_hours" placeholder="例如 7.5" />
        </div>
        <div class="row">
          <label>过敏史</label>
          <input v-model="allergies" placeholder="例如 花粉、海鲜" />
        </div>
        <div class="row">
          <label>慢性病史</label>
          <input v-model="chronic_diseases" placeholder="例如 高血压、糖尿病" />
        </div>
        <div class="row">
          <label>既往病史</label>
          <input v-model="medical_history" placeholder="手术、重大疾病等" />
        </div>
        <div class="row">
          <label>记录时间</label>
          <input v-model="date" type="datetime-local" />
          <div class="hint-small">默认为当前时间</div>
        </div>
      </div>

      <div class="actions">
        <button class="primary" @click="addRecordExtended">添加记录</button>
        <span class="result">{{ addResult }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const baseHealth = 'http://localhost:8080/user-health'
const baseInfo = 'http://localhost:8080/user-info'

const isLoadingRecords = ref(false)
const recordsLoaded = ref(false)

const props = defineProps({
  userId: { type: String, required: true },
  username: { type: String, required: false, default: '' }
})
const userId = props.userId
const userName = props.username
const displayName = computed(() => (props.username && props.username.trim()) ? props.username : userId)

const activeTab = ref('records')

// 记录
const records = ref([])
const addResult = ref('')

// 排序（最新在前）
const sortedRecords = computed(() => [...records.value].sort((a, b) => new Date(b.date) - new Date(a.date)))

// 侧滑状态
const activeIndex = ref(0)
const carouselRef = ref(null)
const dragging = ref(false)
const startX = ref(0)
const deltaX = ref(0)
const SWIPE_THRESHOLD = 50

const canPrev = computed(() => activeIndex.value > 0)
const canNext = computed(() => activeIndex.value < sortedRecords.value.length - 1)

function nextSlide() { if (canNext.value) activeIndex.value++ }
function prevSlide() { if (canPrev.value) activeIndex.value-- }

// 限制三个标签：小于等于3直接全部；否则始终 [0, activeIndex, last]
const dotIndexes = computed(() => {
  const total = sortedRecords.value.length
  if (total <= 3) return Array.from({ length: total }, (_, i) => i)
  const last = total - 1
  const set = new Set([0, activeIndex.value, last])
  return Array.from(set).sort((a, b) => a - b) // 排序保证视觉一致
})
function dotClick(i) {
  if (i === activeIndex.value) return
  activeIndex.value = i
}

// 拖拽滑动
function onTouchStart(e) {
  dragging.value = true
  startX.value = e.touches[0].clientX
  deltaX.value = 0
}
function onTouchMove(e) {
  if (!dragging.value) return
  deltaX.value = e.touches[0].clientX - startX.value
}
function onTouchEnd() {
  if (!dragging.value) return
  if (Math.abs(deltaX.value) > SWIPE_THRESHOLD) {
    if (deltaX.value < 0) nextSlide()
    else prevSlide()
  }
  dragging.value = false
  deltaX.value = 0
}
function onMouseDown(e) {
  dragging.value = true
  startX.value = e.clientX
  deltaX.value = 0
}
function onMouseMove(e) {
  if (!dragging.value) return
  deltaX.value = e.clientX - startX.value
}
function onMouseUp() { onTouchEnd() }
function onMouseLeave() { if (dragging.value) onTouchEnd() }

watch(records, () => { activeIndex.value = 0 })

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { hour12: false })
}

/* ==== 加载 / 清空 ==== */
// 支持 force 参数：true 时强制刷新；否则在已有最新数据时直接跳过
async function loadRecords(force = false) {
  if (!props.userId) return alert('请先登录')
  if (isLoadingRecords.value) return
  if (recordsLoaded.value && !force) return

  isLoadingRecords.value = true
  try {
    const url = `${baseHealth}/records?uid=${encodeURIComponent(props.userId)}`
    console.log('[DEBUG] 请求记录接口 URL =', url)
    const res = await fetch(url)
    const json = await res.json()
    console.log('[DEBUG] 原始返回 records =', json)
    records.value = json
    console.log('[DEBUG] records.value.length =', records.value.length)
    recordsLoaded.value = true
  } catch (e) {
    console.error('[DEBUG] loadRecords 异常', e)
    records.value = []
    recordsLoaded.value = false
  }
}

async function clearRecords() {
  if (!props.userId) return alert('请先登录')
  if (!confirm('确认清空？')) return
  try {
    const res = await fetch(`${baseHealth}/records?uid=${encodeURIComponent(props.userId)}`, { method: 'DELETE' })
    const ok = await res.text()
    alert(ok === 'true' ? '已清空' : '清空失败')
    await loadRecords()
  } catch {
    alert('请求异常')
  }
}

/* ==== 新增记录表单 ==== */
const height = ref('170')
const weight = ref('65')
const blood_type = ref('')
const blood_pressure_systolic = ref('')
const blood_pressure_diastolic = ref('')
const heart_rate = ref('')
const body_temperature = ref('')
const blood_sugar = ref('')
const cholesterol_total = ref('')
const cholesterol_ldl = ref('')
const cholesterol_hdl = ref('')
const triglycerides = ref('')
const vision_left = ref('')
const vision_right = ref('')
const allergies = ref('')
const chronic_diseases = ref('')
const medical_history = ref('')
const smoking_status = ref('')
const drinking_status = ref('')
const exercise_frequency = ref('')
const sleep_hours = ref('')
const nowLocal = () => {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
const date = ref(nowLocal())

const computedBmi = computed(() => {
  const h = parseFloat(height.value)
  const w = parseFloat(weight.value)
  if (!h || !w) return ''
  return (w / ((h / 100) ** 2)).toFixed(2)
})

async function addRecordExtended() {
  if (!props.userId) return alert('请先登录')
  const h = parseFloat(height.value)
  const w = parseFloat(weight.value)
  if (!h || !w) return alert('请输入正确身高/体重')
  const payload = {
    user_id: Number(props.userId),
    height_cm: isNaN(h) ? null : Number(h.toFixed(2)),
    weight_kg: isNaN(w) ? null : Number(w.toFixed(2)),
    blood_type: (blood_type.value || '').trim(),
    bmi: Number(((w / ((h / 100) ** 2)) || 0).toFixed(2)),
    blood_pressure_systolic: parseIntOrNull(blood_pressure_systolic.value),
    blood_pressure_diastolic: parseIntOrNull(blood_pressure_diastolic.value),
    heart_rate: parseIntOrNull(heart_rate.value),
    body_temperature: parseFloatOrNull(body_temperature.value),
    blood_sugar: parseFloatOrNull(blood_sugar.value),
    cholesterol_total: parseFloatOrNull(cholesterol_total.value),
    cholesterol_ldl: parseFloatOrNull(cholesterol_ldl.value),
    cholesterol_hdl: parseFloatOrNull(cholesterol_hdl.value),
    triglycerides: parseFloatOrNull(triglycerides.value),
    vision_left: parseFloatOrNull(vision_left.value),
    vision_right: parseFloatOrNull(vision_right.value),
    allergies: (allergies.value || '').trim(),
    chronic_diseases: (chronic_diseases.value || '').trim(),
    medical_history: (medical_history.value || '').trim(),
    smoking_status: (smoking_status.value || '').trim(),
    drinking_status: (drinking_status.value || '').trim(),
    exercise_frequency: (exercise_frequency.value || '').trim(),
    sleep_hours: parseFloatOrNull(sleep_hours.value),
    date: toISOStringFromLocal(date.value)
  }
  try {
    const res = await fetch(`${baseHealth}/record`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    addResult.value = await res.text()
    await loadRecords()
    activeTab.value = 'records'
  } catch {
    addResult.value = '请求异常'
  }
}

function parseIntOrNull(v) {
  const n = parseInt(v)
  return isNaN(n) ? null : n
}
function parseFloatOrNull(v) {
  const n = parseFloat(v)
  return isNaN(n) ? null : Number(n)
}
function toISOStringFromLocal(localStr) {
  if (!localStr) return new Date().toISOString()
  const d = new Date(localStr)
  return isNaN(d.getTime()) ? new Date().toISOString() : d.toISOString()
}

/* ==== 个人基础信息 ==== */
const profile = ref({
  info_id: null,
  user_id: userId ? Number(userId) : null,
  name: '',
  birth_date: '',
  phone: '',
  email: '',
})
const profileResult = ref('')

watch(() => props.userId, v => {
  if (!v) return
  profile.value.user_id = Number(v)
  loadProfile()
  loadRecords()
}, { immediate: true })

async function loadProfile() {
  profileResult.value = ''
  if (!props.userId) return
  try {
    const res = await fetch(`${baseInfo}/${encodeURIComponent(props.userId)}`)
    if (!res.ok) { profileResult.value = '未找到档案'; return }
    const data = await res.json()
    if (!data || Object.keys(data).length === 0) {
      profile.value = {
        info_id: null,
        user_id: Number(props.userId),
        name: '',
        birth_date: '',
        phone: '',
        email: '',
      }
      profileResult.value = '暂无档案，请创建'
    } else {
      profile.value = {
        info_id: data.info_id ?? null,
        user_id: Number(props.userId),
        name: data.name ?? '',
        birth_date: normalizeDateStr(data.birth_date),
        phone: data.phone ?? '',
        email: data.email ?? '',
      }
      profileResult.value = ''
    }
  } catch {
    profileResult.value = '查询失败'
  }
}

function normalizeDateStr(s) {
  if (!s) return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
  const d = new Date(s)
  if (isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function saveProfile() {
  profileResult.value = '保存中...'
  if (!props.userId) { profileResult.value = '请先登录'; return }
  const payload = {
    info_id: profile.value.info_id,
    user_id: Number(props.userId),
    name: (profile.value.name || '').trim(),
    birth_date: (profile.value.birth_date || '').trim(),
    phone: (profile.value.phone || '').trim(),
    email: (profile.value.email || '').trim(),
  }
  const hasId = !!payload.info_id
  try {
    const res = await fetch(`${baseInfo}`, {
      method: hasId ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const ok = await res.text()
    if (ok === 'true') {
      profileResult.value = hasId ? '已保存修改' : '创建成功'
      await loadProfile()
    } else {
      profileResult.value = '保存失败'
    }
  } catch {
    profileResult.value = '请求异常'
  }
}

async function deleteProfile() {
  if (!profile.value.info_id) return
  if (!confirm('确认删除当前档案？')) return
  try {
    const res = await fetch(`${baseInfo}/${encodeURIComponent(profile.value.info_id)}`, { method: 'DELETE' })
    const ok = await res.text()
    if (ok === 'true') {
      profile.value = {
        info_id: null,
        user_id: Number(props.userId),
        name: '',
        birth_date: '',
        phone: '',
        email: '',
      }
      profileResult.value = '已删除'
    } else {
      profileResult.value = '删除失败'
    }
  } catch {
    profileResult.value = '请求异常'
  }
}

/* 追加到 <script setup> 中（若已有变量避免重复定义） */
const svgWidth = 880
const svgHeight = 300
const padding = { left: 70, right: 70, top: 30, bottom: 50 }
const hitRadius = 24
/* 新增：数据绘制相对四条轴的内边距 */
const axisGapX = 12    // 左右数据线缩进
const axisGapY = 8     // 上下数据线缩进
// 汇总为每日均值
const dailyAverages = computed(() => {
  const src = records.value
  console.log('[DEBUG] dailyAverages 触发，当前 records.length =', src.length)

  if (!src || !src.length) {
    console.log('[DEBUG] dailyAverages 返回空数组（无记录）')
    return []
  }

  const map = new Map()
  src.forEach((r, idx) => {
    const day = formatDay(r.date)
    if (!day) {
      console.warn('[DEBUG] 条目日期无法归类 idx=', idx, '原始 date=', r.date)
      return
    }
    if (!map.has(day)) {
      map.set(day, { count: 0, sumHeight: 0, sumWeight: 0, sumBmi: 0, day })
    }
    const slot = map.get(day)
    slot.count++
    slot.sumHeight += Number(r.height_cm ?? 0)
    slot.sumWeight += Number(r.weight_kg ?? 0)
    slot.sumBmi += Number(r.bmi ?? 0)
  })

  const arr = Array.from(map.values()).sort((a, b) => new Date(a.day) - new Date(b.day))
  const result = arr.map(s => ({
    day: s.day,
    avgHeight: s.count ? s.sumHeight / s.count : 0,
    avgWeight: s.count ? s.sumWeight / s.count : 0,
    avgBmi: s.count ? s.sumBmi / s.count : 0
  }))

  console.log('[DEBUG] dailyAverages 归并结果 =', result)
  return result
})
function formatDay(dateStr) {
  if (!dateStr) {
    console.warn('[DEBUG] formatDay 收到空 dateStr')
    return ''
  }
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) {
    console.warn('[DEBUG] formatDay 解析失败 dateStr =', dateStr)
    return ''
  }
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const result = `${y}-${m}-${day}`
  // 只在前几次输出，避免刷屏
  if (Math.random() < 0.05) console.log('[DEBUG] formatDay 成功 ->', dateStr, '=>', result)
  return result
}
// 坐标函数
// 至少保证 3 个横轴刻度；不足时用占位空字符串
const MIN_X_TICKS = 3
const xTickData = computed(() => {
  const days = dailyAverages.value.map(d => d.day)
  if (days.length >= MIN_X_TICKS) return days
  // 填充到 3；空标签不显示文字
  return days.concat(Array(MIN_X_TICKS - days.length).fill(''))
})

function x(i) {
  const n = xTickData.value.length
  // 固定按 n-1 等分，即便真实数据只有 1 天也展开为 3 段，使轴完整
  const span = (svgWidth - padding.left - padding.right)
  return padding.left + (n === 1 ? span / 2 : (span * i) / (n - 1))
}
function dataX(i) {
  const count = dailyAverages.value.length
  const span = (svgWidth - padding.left - padding.right) - axisGapX * 2
  if (count <= 1) {
    return padding.left + axisGapX + span / 2
  }
  return padding.left + axisGapX + (span * i) / (count - 1)
}
// 增加最小值与域扩展，防止单值导致所有刻度重叠
const leftDomain = computed(() => {
  if (!dailyAverages.value.length) return { min: 0, max: 1 }
  const vals = dailyAverages.value.flatMap(d => [d.avgHeight, d.avgWeight]).filter(v => !isNaN(v))
  let min = Math.min(...vals)
  let max = Math.max(...vals)
  if (min === max) {
    // 单值时上下各扩 1（或按 1% 比例）
    min = min - 1
    max = max + 1
  }
  return { min, max }
})

const rightDomain = computed(() => {
  if (!dailyAverages.value.length) return { min: 0, max: 1 }
  const vals = dailyAverages.value.map(d => d.avgBmi).filter(v => !isNaN(v))
  let min = Math.min(...vals)
  let max = Math.max(...vals)
  if (min === max) {
    min = (min - 1 < 0 ? 0 : min - 1)
    max = max + 1
  }
  return { min, max }
})

// 刻度：固定 5 格（含 0 时保持从 min 到 max）
const leftAxisTicks = computed(() => {
  const { min, max } = leftDomain.value
  const step = (max - min) / 4
  return Array.from({ length: 5 }, (_, i) => Number((min + i * step).toFixed(0)))
})
const rightAxisTicks = computed(() => {
  const { min, max } = rightDomain.value
  const step = (max - min) / 4
  return Array.from({ length: 5 }, (_, i) => Number((min + i * step).toFixed(1)))
})

function yLeft(v) {
  const { min, max } = leftDomain.value
  const h = svgHeight - padding.top - padding.bottom
  // 防止除以 0
  const ratio = max === min ? 0.5 : (v - min) / (max - min)
  return padding.top + (1 - ratio) * h
}
function yRight(v) {
  const { min, max } = rightDomain.value
  const h = svgHeight - padding.top - padding.bottom
  const ratio = max === min ? 0.5 : (v - min) / (max - min)
  return padding.top + (1 - ratio) * h
}
function yLeftData(v) {
  const { min, max } = leftDomain.value
  const h = (svgHeight - padding.top - padding.bottom) - axisGapY * 2
  const ratio = max === min ? 0.5 : (v - min) / (max - min)
  return padding.top + axisGapY + (1 - ratio) * h
}
function yRightData(v) {
  const { min, max } = rightDomain.value
  const h = (svgHeight - padding.top - padding.bottom) - axisGapY * 2
  const ratio = max === min ? 0.5 : (v - min) / (max - min)
  return padding.top + axisGapY + (1 - ratio) * h
}

// 折线点
function polylinePoints(type) {
  if (!dailyAverages.value.length) {
    console.warn('[DEBUG] polylinePoints 空 dailyAverages，type=', type)
    return ''
  }
  return dailyAverages.value.map((d, i) => {
    const cx = dataX(i)
    let cy
    if (type === 'height') cy = yLeftData(d.avgHeight)
    else if (type === 'weight') cy = yLeftData(d.avgWeight)
    else cy = yRightData(d.avgBmi)
    return `${cx},${cy}`
  }).join(' ')
}



const hoverIndex = ref(null)
const chartBoxRef = ref(null)

function setHover(i) {
  hoverIndex.value = i
}
function clearHover() {
  hoverIndex.value = null
}

const tooltipStyle = computed(() => {
  if (hoverIndex.value === null) return {}
  const cx = dataX(hoverIndex.value)
  return {
    left: `${cx - 80}px`,
    top: `60px`
  }
})

</script>

<style scoped>
.health .header { margin-bottom: 10px; }

/* 个人档案卡片 */
.card.profile {
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px;
  background:
      linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)),
      radial-gradient(600px 240px at 10% 0%, rgba(99,198,255,0.12), transparent 60%),
      radial-gradient(600px 240px at 80% 0%, rgba(141,123,255,0.12), transparent 60%);
  padding: 16px;
  margin-bottom: 16px;
}
.profile-head { display:flex; justify-content: space-between; align-items:center; margin-bottom: 10px; }
.ops { display:flex; gap: 8px; }
.grid-2-compact { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.actions { margin-top: 10px; display:flex; align-items:center; gap: 10px; }

/* tabs */
.tabs { display:flex; gap: 8px; margin-bottom: 12px; }
.tab {
  padding: 8px 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.02); color: #dfe8ff; cursor: pointer;
}
.tab.active {
  background: linear-gradient(135deg, #63c6ff, #8d7bff); color: #0e1120; font-weight: 700;
}

/* 主体网格 */
.grid-2 { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 16px; }
.grid-1 {display: grid; }
.card {
  border: 1px solid rgba(255,255,255,0.12); border-radius: 14px;
  background: rgba(255,255,255,0.06); padding: 16px;
}

.row { display: grid; grid-template-columns: 100px 1fr auto; align-items: center; gap: 10px; margin-bottom: 10px; }
.row label { color: #00BFFF; font-size: 13px; }
.row .muted { color: #9fb0ff; font-size: 12px; }
.row input {
  padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.14);
  background: rgba(10,14,32,0.4); color: #e9efff; outline: none;
}
.static {
  padding: 10px; border-radius: 10px; border: 1px dashed rgba(255,255,255,0.18);
  color: blue; background: rgba(255,255,255,0.04);
}

button.ghost {
  padding: 8px 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.04); color: #e9efff; cursor: pointer;
}
button.primary {
  padding: 10px 16px; border-radius: 12px; border: none; cursor: pointer; font-weight: 800;
  background: linear-gradient(135deg, #63c6ff, #8d7bff); color: #0e1120;
}
button.danger {
  padding: 10px 16px; border-radius: 12px; border: 1px solid rgba(255,120,120,0.4);
  color: #ffb3b3; background: rgba(255,67,67,0.06); cursor: pointer; font-weight: 700;
}

/* 固定宽度单卡轮播（叠放） */
.carousel.fixed {
  position: relative;
  overflow: hidden;
  border: 1px dashed rgba(255,255,255,0.15);
  border-radius: 12px;
  background: rgba(0,0,0,0.15);
  margin-top: 8px;
  min-height: 200px;
}
.carousel-stack {
  position: relative;
  width: 100%;
}
.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transform: scale(.96);
  transition: opacity .35s ease, transform .35s ease;
  padding: 12px;
  pointer-events: none;
}
.slide.active {
  opacity: 1;
  transform: scale(1);
  pointer-events: auto;
}
.slide-inner {
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px;
  background: rgba(255,255,255,0.05);
  padding: 12px;
  display: grid;
  gap: 8px;
}
.slide-row { display: grid; grid-template-columns: 90px 1fr; align-items: center; }
.slide-row .k { color: #a6b4ff; font-size: 12px; }
.slide-row .v { color: #e9efff; font-weight: 600; }
.slide-row .v.emph {
  color: #0e1120;
  background: linear-gradient(135deg, rgba(99,198,255,0.25), rgba(141,123,255,0.18));
  border-radius: 8px; padding: 4px 8px; display: inline-block;
}
.slide-meta { color: #bcd0ff; font-size: 12px; opacity: 0.8; margin-top: 4px; }

.nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.1);
  color: #fff; cursor: pointer;
  display: grid; place-items: center;
}
.nav:disabled { opacity: 0.35; cursor: not-allowed; }
.nav.prev { left: 8px; }
.nav.next { right: 8px; }

.dots.three {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: 8px;
  display: flex;
  gap: 8px;
}
.dot {
  width: 10px; height: 10px; border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.35);
  background: rgba(255,255,255,0.15);
  cursor: pointer;
  transition: background .25s;
}
.dot.active {
  background: linear-gradient(135deg, #63c6ff, #8d7bff);
  border-color: transparent;
}
.dot:disabled { cursor: default; opacity: .6; }

.new-record-card { max-width: 980px; margin: 0 auto; }
.grid-form { display: grid; grid-template-columns: 1fr; gap: 6px; }
.hint-small { color: #9fb0ff; font-size: 12px; }

/* 追加到 <style scoped> 中 */
.chart-wrapper {
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px;
  background: rgba(255,255,255,0.05);
  padding: 14px 16px;
  position: relative;
  margin-bottom: 16px;
}
.chart-head {
  display:flex;
  justify-content: space-between;
  align-items:center;
  margin-bottom: 6px;
}
.chart-head h3 { margin:0; font-size:16px; }
.legend { display:flex; gap:10px; font-size:12px; }
.lg-item {
  padding:4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.07);
  font-weight:600;
}
.lg-height { border:1px solid #5aa2ff; color:#5aa2ff; }
.lg-weight { border:1px solid #ff8d5c; color:#ff8d5c; }
.lg-bmi { border:1px solid #9d6bff; color:#9d6bff; }

.chart-box {
  position: relative;
  width: 100%;
  overflow: hidden;
  user-select: none;
  user-select: none;
}

.health {
  /* 轴线颜色换成更明显的蓝灰色；你可再调 */
  --axis: #546b9f;
  --hover-line: #8899cc;
}

.line-height { stroke:#5aa2ff; }
.line-weight { stroke:#ff8d5c; }
.line-bmi { stroke:#9d6bff; }

.dot-height { fill:#5aa2ff; stroke:#fff; stroke-width:1; }
.dot-weight { fill:#ff8d5c; stroke:#fff; stroke-width:1; }
.dot-bmi { fill:#9d6bff; stroke:#fff; stroke-width:1; }

.tick-label {
  font-size:11px;
  fill: rgba(255,255,255,0.7);
}
.axis-title {
  font-size:11px;
  fill: rgba(255,255,255,0.55);
}

.tooltip {
  position: absolute;
  width: 160px;
  background: rgba(20,26,48,0.92);
  border: 1px solid rgba(255,255,255,0.16);
  box-shadow: 0 4px 18px rgba(0,0,0,0.4);
  border-radius: 10px;
  padding: 10px 12px;
  backdrop-filter: blur(8px);
  pointer-events: none;
  font-size: 12px;
  color: #e9efff;
}
.tooltip .tt-day {
  font-weight:700;
  margin-bottom:6px;
  font-size:13px;
  color:#cfe3ff;
}
.tooltip .tt-row {
  display:flex;
  justify-content: space-between;
  margin-bottom:4px;
}
.tooltip .tt-row span {
  color:#9fb0ff;
}

.chart-foot-note {
  font-size: 12px;
  color: #9fb0ff;
  margin-top: 4px;
  text-align: right;
}
.empty {
  padding: 20px;
  text-align: center;
  font-size: 14px;
  color: #9fb0ff;
  border: 1px dashed rgba(255,255,255,0.15);
  border-radius: 12px;
  background: rgba(0,0,0,0.15);
}
/* 坐标系与刻度分组补全样式 */
.axes line {
  stroke: var(--axis);
  stroke-width: 1;
  shape-rendering: crispEdges;
  color: #3a6cff;
}

.x-ticks line,
.y-ticks-left line,
.y-ticks-right line {
  stroke: var(--axis);
  stroke-width: 1;
}

.x-ticks .tick-label,
.y-ticks-left .tick-label,
.y-ticks-right .tick-label {
  fill: rgba(255,255,255,0.7);
  font-size: 11px;
}

.y-ticks-left .tick-label,
.y-ticks-right .tick-label {
  dominant-baseline: middle; /* 使数值在刻度线上垂直居中 */
}

.chart-box svg {
  width: 100%;
  height: auto;
  display: block;
}

@media (max-width: 960px) {
  .grid-2 { grid-template-columns: 1fr; }
  .row { grid-template-columns: 1fr auto; }
  .grid-2-compact { grid-template-columns: 1fr; }
}
</style>