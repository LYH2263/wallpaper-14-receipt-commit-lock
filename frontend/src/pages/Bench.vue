<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import DropStripBar from '../components/DropStripBar.vue'
const walls = ref([]); const rolls = ref([]); const wallId = ref(1); const rollId = ref(1)
const out = ref(null); const msg = ref(''); const confirming = ref(false)
onMounted(async () => {
  walls.value = (await getJSON('/api/walls')).items.filter(w => w.data_quality==='clean')
  rolls.value = (await getJSON('/api/rolls')).items.filter(r => r.data_quality==='clean')
  if (walls.value.length) wallId.value = walls.value[0].id
  if (rolls.value.length) rollId.value = rolls.value[0].id
})
function reset() { out.value = null; msg.value = '' }
async function dry() {
  reset()
  try {
    out.value = await postJSON('/api/estimate', { wall_id: wallId.value, roll_id: rollId.value })
  } catch (e) { msg.value = '试算失败：' + e.message }
}
async function confirm() {
  if (!out.value?.receipt || confirming.value) return
  confirming.value = true
  try {
    const r = await postJSON('/api/estimate/confirm', { receipt: out.value.receipt })
    out.value = null  // 回执已核销，需重新试算
    msg.value = `已落库，记录 #${r.run_id}（${r.rolls} 卷）`
  } catch (e) {
    out.value = null  // 确认失败，回执不可再用，需重新试算拿新回执
    msg.value = '确认失败，请重新试算获取新回执：' + e.message
  } finally { confirming.value = false }
}
</script>
<template>
  <div class="page"><h1>算卷工作台</h1>
  <select v-model.number="wallId" @change="reset"><option v-for="w in walls" :key="w.id" :value="w.id">{{ w.name }}</option></select>
  <select v-model.number="rollId" @change="reset"><option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.name }}</option></select>
  <button @click="dry">试算</button>
  <button :disabled="!out || confirming" @click="confirm">确认落库</button>
  <div v-if="out"><strong>{{ out.rolls }} 卷</strong> · {{ out.drops }} 条 · 每条 {{ out.drop_len_m }}m
  <div>回执 <code>{{ out.receipt }}</code>（一次性，确认后失效）</div>
  <DropStripBar :drops="out.drops" :drop-len="out.drop_len_m" :rolls="out.rolls" /></div>
  <p v-if="msg">{{ msg }}</p>
  </div>
</template>
