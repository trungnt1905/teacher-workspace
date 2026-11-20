<script setup>
import { computed } from 'vue'
import { useSyncStore } from '../../stores/sync'
import { TARGET_STATUS } from '../../utils/timetable'

const sync = useSyncStore()

const weeks = computed(() => sync.job?.weeks ?? [])
const subjects = computed(() => sync.job?.subjects ?? [])
const canAnalyze = computed(() => sync.selectedWeeks.length > 0 && sync.selectedSubjects.length > 0 && !sync.busy)

function badgeTone(week) {
  if (week.selectable) return 'ok'
  return week.target_status === 'missing' || week.target_status === 'has_data' ? 'warn' : 'error'
}

function setWeeks(all) {
  sync.selectedWeeks = all ? [...sync.selectableWeeks] : []
}

function setSubjects(all) {
  sync.selectedSubjects = all ? [...subjects.value] : []
}
</script>

<template>
  <section class="step">
    <div class="card">
      <div class="head">
        <h2>Tuần cần đồng bộ</h2>
        <div class="bulk">
          <button type="button" class="link" @click="setWeeks(true)">Chọn tất cả</button>
          <button type="button" class="link" @click="setWeeks(false)">Bỏ chọn</button>
        </div>
      </div>
      <p class="muted small">
        Tệp: <strong>{{ sync.job.source_file_name }}</strong> → <strong>{{ sync.job.target_file_name }}</strong>
      </p>
      <ul class="weeks">
        <li v-for="week in weeks" :key="week.week_number" :class="{ disabled: !week.selectable }">
          <label>
            <input v-model="sync.selectedWeeks" type="checkbox" :value="week.week_number" :disabled="!week.selectable" />
            <span class="week-name">Tuần {{ week.week_number }}</span>
            <span class="badge" :class="badgeTone(week)">{{ TARGET_STATUS[week.target_status] ?? week.target_status }}</span>
          </label>
          <p v-for="err in week.errors" :key="err.code" class="reason">{{ err.message }}</p>
        </li>
      </ul>
      <p v-if="sync.selectableWeeks.length === 0" class="alert alert-warn">
        Chưa có tuần nào sẵn sàng. Hãy copy sheet MẪU thành các sheet tuần trong file đích (xem hướng dẫn ở trên) rồi tải lại file.
      </p>
    </div>

    <div class="card">
      <div class="head">
        <h2>Môn cần đồng bộ</h2>
        <div class="bulk">
          <button type="button" class="link" @click="setSubjects(true)">Chọn tất cả</button>
          <button type="button" class="link" @click="setSubjects(false)">Bỏ chọn</button>
        </div>
      </div>
      <p class="muted small">Môn nào được tích thì mới được điền. Môn không tích giữ nguyên như trong file đích.</p>
      <div class="subjects">
        <label v-for="subject in subjects" :key="subject" class="chip" :class="{ on: sync.selectedSubjects.includes(subject) }">
          <input v-model="sync.selectedSubjects" type="checkbox" :value="subject" />
          {{ subject }}
        </label>
      </div>
    </div>

    <div class="actions">
      <button type="button" class="secondary" :disabled="sync.busy" @click="sync.startOver()">Chọn file khác</button>
      <button type="button" :disabled="!canAnalyze" @click="sync.analyze()">
        {{ sync.status === 'analyzing' ? 'Đang phân tích…' : 'Phân tích và xem trước' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.step {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.bulk {
  display: flex;
  gap: 16px;
}
.small {
  font-size: 0.875rem;
  margin: 4px 0 12px;
  overflow-wrap: anywhere;
}
.weeks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 8px;
}
.weeks li {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
}
.weeks li.disabled {
  background: var(--surface-muted);
}
.weeks label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.weeks li.disabled label {
  cursor: not-allowed;
  color: var(--muted);
}
.week-name {
  font-weight: 600;
  flex: 1;
}
.reason {
  margin: 4px 0 0 24px;
  font-size: 0.8125rem;
  color: var(--muted);
}
.subjects {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px 4px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  cursor: pointer;
  user-select: none;
}
.chip.on {
  border-color: var(--primary);
  background: var(--primary-bg);
}
</style>
