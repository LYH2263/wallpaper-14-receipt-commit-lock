<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import DropStripBar from '../components/DropStripBar.vue'
const walls = ref([]); const rolls = ref([]); const wallId = ref(1); const rollId = ref(1)
const out = ref(null); const note = ref(''); const error = ref(''); const confirmed = ref(null)
const receiptDead = ref(false); const busy = ref(false)
onMounted(async () => {
  walls.value = (await getJSON('/api/walls')).items.filter(w => w.data_quality==='clean')
  rolls.value = (await getJSON('/api/rolls')).items.filter(r => r.data_quality==='clean')
  if (walls.value.length) wallId.value = walls.value[0].id
  if (rolls.value.length) rollId.value = rolls.value[0].id
})
async function dryRun() {
  error.value = ''; confirmed.value = null; busy.value = true
  try {
    out.value = await postJSON('/api/estimate/dry-run', { wall_id: wallId.value, roll_id: rollId.value })
    receiptDead.value = false
  } catch (e) { error.value = e.message; out.value = null }
  finally { busy.value = false }
}
async function confirm() {
  if (!out.value?.receipt || receiptDead.value) return
  error.value = ''; busy.value = true
  try {
    confirmed.value = await postJSON('/api/estimate/confirm', { receipt: out.value.receipt.token, note: note.value })
    out.value = null // 回执已核销，历史列表出现新行；再次入账需重新干算
  } catch (e) {
    error.value = e.message
    receiptDead.value = true // 当前回执已失效，需重新干算拿新回执
  } finally { busy.value = false }
}
</script>
<template>
  <div class="page"><h1>算卷工作台</h1>
  <select v-model.number="wallId"><option v-for="w in walls" :key="w.id" :value="w.id">{{ w.name }}</option></select>
  <select v-model.number="rollId"><option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.name }}</option></select>
  <input v-model="note" placeholder="备注（确认时写入）" />
  <button :disabled="busy" @click="dryRun">干算</button>
  <button :disabled="busy || !out || !out.receipt || receiptDead" @click="confirm">确认入账</button>
  <p v-if="error" class="warn">{{ error }} — 可重新干算获取新回执</p>
  <p v-if="confirmed">已入账 run #{{ confirmed.run_id }}（{{ confirmed.rolls }} 卷），记录页可见新行</p>
  <div v-if="out"><strong>{{ out.rolls }} 卷</strong> · {{ out.drops }} 条 · 每条 {{ out.drop_len_m }}m
  <p v-if="out.receipt" class="receipt-line">一次性回执：<code>{{ out.receipt.token }}</code><span v-if="receiptDead" class="warn">（已失效，请重新干算）</span></p>
  <DropStripBar :drops="out.drops" :drop-len="out.drop_len_m" :rolls="out.rolls" /></div>
  </div>
</template>
