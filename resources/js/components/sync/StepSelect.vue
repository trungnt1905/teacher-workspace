<script setup>
import { computed } from 'vue'
import { AlertTriangle, Check, ChevronLeft, ChevronRight, Info, Loader2 } from 'lucide-vue-next'
import { useSyncStore } from '../../stores/sync'
import { unavailableGroups, weekProblem } from '../../utils/timetable'
import AppPanel from '../ui/AppPanel.vue'

const sync = useSyncStore()

const weeks = computed(() => sync.job?.weeks ?? [])
const subjects = computed(() => sync.job?.subjects ?? [])
const defaults = computed(() => sync.job?.default_selected_subjects ?? [])
const reasons = computed(() => unavailableGroups(weeks.value))
const canAnalyze = computed(() => sync.selectedWeeks.length > 0 && sync.selectedSubjects.length > 0 && !sync.busy)

const PROBLEM_TEXT = { target_missing: 'File đích không có sheet cho tuần này', has_data: 'Sheet đã có dữ liệu', error: 'Không đọc được sheet' }
// One-sheet target (file made from the template): exactly one source week per run.
const singleSheet = computed(() => sync.job?.single_target_sheet ?? null)

function tileClass(week) {
  const problem = weekProblem(week)
  if (problem) return `off ${problem}`
  return sync.selectedWeeks.includes(week.week_number) ? 'selected' : 'ready'
}

function toggleWeek(week) {
  if (!week.selectable) return
  const n = week.week_number
  if (singleSheet.value) {
    sync.selectedWeeks = sync.selectedWeeks.includes(n) ? [] : [n]
    return
  }
  sync.selectedWeeks = sync.selectedWeeks.includes(n) ? sync.selectedWeeks.filter((w) => w !== n) : [...sync.selectedWeeks, n]
}

function toggleSubject(subject) {
  sync.selectedSubjects = sync.selectedSubjects.includes(subject)
    ? sync.selectedSubjects.filter((s) => s !== subject)
    : [...sync.selectedSubjects, subject]
}
</script>

<template>
  <AppPanel eyebrow="Bước 2 · Chọn tuần và môn" title="Đồng bộ tuần nào, môn nào?"
             description="Các tuần lấy từ file nguồn. Chọn tuần cần điền và các môn cần đồng bộ; môn không tích giữ nguyên như file đích.">
    <section class="group">
      <div class="group-head">
        <h3>Tuần <span class="muted count">{{ sync.selectedWeeks.length }}/{{ sync.selectableWeeks.length }} đã chọn</span></h3>
        <div v-if="!singleSheet" class="bulk">
          <button type="button" class="btn btn-link" @click="sync.selectedWeeks = [...sync.selectableWeeks]">Chọn tất cả</button>
          <button type="button" class="btn btn-link" @click="sync.selectedWeeks = []">Bỏ chọn</button>
        </div>
      </div>

      <p v-if="singleSheet" class="callout">
        <Info />
        <span>
          File đích chỉ có một sheet (<strong>{{ singleSheet }}</strong>): <strong>chọn 1 tuần</strong> — tên bài, đồ dùng,
          tiêu đề và ngày tháng của tuần đó sẽ được điền vào sheet này, và sheet được đổi tên thành “TUẦN n”.
        </span>
      </p>

      <div class="tiles weeks">
        <button v-for="week in weeks" :key="week.week_number" type="button" class="tile" :class="tileClass(week)"
                :disabled="!week.selectable" :aria-pressed="sync.selectedWeeks.includes(week.week_number)"
                :title="week.selectable ? `Tuần ${week.week_number}` : `Tuần ${week.week_number}: ${PROBLEM_TEXT[weekProblem(week)]}`"
                @click="toggleWeek(week)">
          <span class="tile-label">Tuần</span>
          <span class="tile-num">{{ week.week_number }}</span>
        </button>
      </div>

      <div class="legend small">
        <span><i class="sw selected"></i>Đã chọn</span>
        <span><i class="sw ready"></i>Sẵn sàng</span>
        <span><i class="sw target_missing"></i>File đích chưa có sheet</span>
        <span><i class="sw has_data"></i>Đã có dữ liệu</span>
        <span><i class="sw error"></i>Không đọc được</span>
      </div>

      <ul v-if="reasons.length" class="reasons">
        <li v-for="r in reasons" :key="r.title + r.text" :class="r.tone">
          <AlertTriangle v-if="r.tone !== 'gray'" /><Info v-else />
          <span><strong>{{ r.title }}:</strong> {{ r.text }}</span>
        </li>
      </ul>
      <p v-if="sync.selectableWeeks.length === 0" class="callout warn">
        <AlertTriangle />
        <span>Chưa có tuần nào đồng bộ được. Dùng file đích chỉ có một sheet (ví dụ file mẫu), hoặc file đích có sheet “TUẦN n” còn trống.</span>
      </p>
    </section>

    <section class="group">
      <div class="group-head">
        <h3>Môn <span class="muted count">{{ sync.selectedSubjects.length }}/{{ subjects.length }} đã chọn</span></h3>
        <div class="bulk">
          <button type="button" class="btn btn-link" @click="sync.selectedSubjects = [...subjects]">Chọn tất cả</button>
          <button type="button" class="btn btn-link" @click="sync.selectedSubjects = subjects.filter((s) => defaults.includes(s))">Mặc định</button>
          <button type="button" class="btn btn-link" @click="sync.selectedSubjects = []">Bỏ chọn</button>
        </div>
      </div>
      <div class="subjects">
        <button v-for="subject in subjects" :key="subject" type="button" class="option"
                :class="{ on: sync.selectedSubjects.includes(subject) }" role="checkbox"
                :aria-checked="sync.selectedSubjects.includes(subject)" @click="toggleSubject(subject)">
          <span class="box"><Check /></span>
          <span class="option-text">{{ subject }}</span>
        </button>
      </div>
      <p class="muted small">“Mặc định” bỏ các môn giáo viên bộ môn dạy. Lựa chọn của bạn được nhớ cho lần sau.</p>
    </section>

    <template #footer>
      <button type="button" class="btn btn-secondary" :disabled="sync.busy" @click="sync.startOver()">
        <ChevronLeft /> Chọn file khác
      </button>
      <span class="muted small">{{ sync.selectedWeeks.length }} tuần · {{ sync.selectedSubjects.length }} môn</span>
      <button type="button" class="btn btn-primary" :disabled="!canAnalyze" @click="sync.analyze()">
        <Loader2 v-if="sync.status === 'analyzing'" class="spin" />
        {{ sync.status === 'analyzing' ? 'Đang phân tích…' : 'Phân tích và xem trước' }}
        <ChevronRight v-if="sync.status !== 'analyzing'" />
      </button>
    </template>
  </AppPanel>
</template>

<style scoped>
.group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.group + .group {
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}
.group-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.count {
  font-weight: 400;
  font-size: 0.8125rem;
  margin-left: 6px;
}
.bulk {
  display: flex;
  gap: 16px;
}

/* Week tiles (like the question grid) */
.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(76px, 1fr));
  gap: 10px;
}
.tile {
  font: inherit;
  position: relative;
  height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
}
.tile-label {
  font-size: 0.6875rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.tile-num {
  font-size: 1.125rem;
  font-weight: 700;
}
.tile.ready:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-soft);
}
.tile.selected {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  box-shadow: inset 0 0 0 1px var(--color-primary);
  color: var(--color-primary-strong);
}
.tile.selected .tile-label {
  color: var(--color-primary);
}
.tile.off {
  cursor: not-allowed;
  background: var(--color-surface-muted);
  color: var(--color-text-subtle);
  border-style: dashed;
}
.tile.off::after {
  content: '';
  position: absolute;
  top: 7px;
  right: 7px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-danger);
}
.tile.target_missing::after {
  background: var(--color-warning);
}
.tile.has_data::after {
  background: var(--color-text-subtle);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  color: var(--color-text-muted);
}
.legend span {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sw {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  border: 1px solid var(--color-border-strong);
  background: var(--color-surface);
}
.sw.selected {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}
.sw.target_missing,
.sw.has_data,
.sw.error {
  border-style: dashed;
  background: var(--color-surface-muted);
  position: relative;
}
.sw.target_missing::after,
.sw.has_data::after,
.sw.error::after {
  content: '';
  position: absolute;
  top: -3px;
  right: -3px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-warning);
}
.sw.has_data::after {
  background: var(--color-text-subtle);
}
.sw.error::after {
  background: var(--color-danger);
}

.reasons {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reasons li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
}
.reasons svg {
  flex: none;
  width: 16px;
  height: 16px;
  margin-top: 1px;
  color: var(--color-text-muted);
}
.reasons .amber {
  background: var(--color-warning-soft);
}
.reasons .amber svg {
  color: var(--color-warning);
}
.reasons .red {
  background: var(--color-danger-soft);
}
.reasons .red svg {
  color: var(--color-danger);
}

/* Subject options (like answer choices) */
.subjects {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 140px), 1fr));
  gap: 8px;
}
.option {
  font: inherit;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  text-align: left;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.option:hover {
  border-color: var(--color-primary-border);
}
.box {
  flex: none;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  border: 1.5px solid var(--color-border-strong);
  display: grid;
  place-items: center;
  color: transparent;
}
.box svg {
  width: 14px;
  height: 14px;
  stroke-width: 3;
}
.option.on {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-border);
  color: var(--color-primary-strong);
  font-weight: 500;
}
.option.on .box {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
}
</style>
