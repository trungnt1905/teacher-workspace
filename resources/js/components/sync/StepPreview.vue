<script setup>
import { computed } from 'vue'
import { AlertTriangle, ArrowRight, CalendarCheck, CalendarOff, Check, ChevronDown, ChevronLeft, ChevronRight, Flag, Info, Loader2, Minus } from 'lucide-vue-next'
import { useSyncStore } from '../../stores/sync'
import { dayState, skippedCount, subjectStatus } from '../../utils/timetable'
import AppPanel from '../ui/AppPanel.vue'

const sync = useSyncStore()

const weeks = computed(() => sync.analysis?.weeks ?? [])
const days = computed(() => sync.job?.days ?? [])
const skipped = computed(() => skippedCount(sync.analysis))
const busy = computed(() => sync.busy)
const filledTotal = computed(() => weeks.value.reduce((n, w) => n + counts(w).filled, 0))

const generateLabel = computed(() => {
  if (sync.status === 'generating') return 'Đang tạo file…'
  return skipped.value > 0 ? `Tạo file (${skipped.value} môn cần điền thủ công)` : 'Tạo file'
})

const DAY_STATE_TEXT = { on: 'Đi học', off: 'Nghỉ', partial: 'Nghỉ 1 buổi' }

function stateOf(week, day) {
  return dayState(week.days_off, day.label, day.sessions)
}

function autoDetected(week, day) {
  return week.days_off.some((d) => d.day === day.label && d.detected_by === 'auto')
}

function counts(week) {
  const filled = week.subjects.filter((s) => s.status === 'matched').length
  return { filled, skipped: week.subjects.length - filled }
}

function skipReasons(week) {
  return week.warnings.filter((w) => w.code !== 'CONTENT_TOO_LONG')
}

function minorNotes(week) {
  return week.warnings.filter((w) => w.code === 'CONTENT_TOO_LONG')
}
</script>

<template>
  <AppPanel eyebrow="Bước 3 · Xem trước" title="Kiểm tra trước khi tạo file"
             description="Môn “Điền” sẽ được ghi vào file; môn “Bỏ qua” giữ nguyên để bạn điền tay. Bấm vào ngày để đánh dấu nghỉ.">
    <template #aside>
      <span class="pill green"><Check /> {{ filledTotal }} môn điền</span>
      <span v-if="skipped" class="pill amber"><Flag /> {{ skipped }} môn bỏ qua</span>
    </template>

    <p v-if="!sync.analysis.can_generate" class="callout warn">
      <AlertTriangle />
      <span>Không có gì để ghi: các tuần đã chọn đều không xử lý được. Kiểm tra lại lý do bên dưới.</span>
    </p>
    <p v-else-if="filledTotal === 0" class="callout">
      <Info />
      <span>Không có môn nào được điền. File kết quả chỉ cập nhật tiêu đề tuần và ngày tháng theo file nguồn.</span>
    </p>

    <article v-for="week in weeks" :key="week.week_number" class="week">
      <header class="week-head">
        <h3>Tuần {{ week.week_number }}</h3>
        <template v-if="week.status === 'blocked'">
          <span class="pill red">Không xử lý được</span>
        </template>
        <template v-else>
          <span class="muted small">{{ counts(week).filled }} điền · {{ counts(week).skipped }} bỏ qua</span>
        </template>
      </header>

      <template v-if="week.status === 'blocked'">
        <p v-for="err in week.errors" :key="err.code + err.message" class="callout error"><AlertTriangle /><span>{{ err.message }}</span></p>
      </template>

      <template v-else>
        <div class="days" role="group" aria-label="Ngày nghỉ">
          <span class="days-label muted small"><CalendarOff /> Ngày nghỉ</span>
          <button v-for="day in days" :key="day.label" type="button" class="day" :class="stateOf(week, day)" :disabled="busy"
                  :aria-pressed="stateOf(week, day) !== 'on'"
                  :title="autoDetected(week, day) ? 'Tự phát hiện từ file nguồn — bấm để đổi' : 'Bấm để đổi'"
                  @click="sync.toggleDay(week.week_number, day.label, stateOf(week, day))">
            Thứ {{ day.label }}: {{ DAY_STATE_TEXT[stateOf(week, day)] }}
          </button>
        </div>

        <section class="header-changes" :class="{ none: !week.header_changes.length }">
          <h4><CalendarCheck /> Tiêu đề và ngày tháng</h4>
          <p v-if="!week.header_changes.length" class="muted small">Đã đúng theo file nguồn — không thay đổi.</p>
          <table v-else>
            <thead>
              <tr><th>Ô</th><th>Hiện tại (file đích)</th><th></th><th>Sẽ đổi thành (theo file nguồn)</th></tr>
            </thead>
            <tbody>
              <tr v-for="c in week.header_changes" :key="c.cell">
                <td class="label">{{ c.label }}</td>
                <td class="old">{{ c.from?.trim() || '(trống)' }}</td>
                <td class="arrow"><ArrowRight /></td>
                <td class="new">{{ c.to?.trim() || '(trống)' }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <ul class="subjects">
          <li v-for="subject in week.subjects" :key="subject.subject" :class="subjectStatus(subject.status).tone">
            <details :class="{ static: !subject.items.length }">
              <summary @click="!subject.items.length && $event.preventDefault()">
                <span class="status-dot"><Check v-if="subject.status === 'matched'" /><Minus v-else /></span>
                <span class="subject-name">{{ subject.subject }}</span>
                <span class="counts muted small">{{ subject.source_count }} → {{ subject.target_count }} tiết</span>
                <span class="pill" :class="subjectStatus(subject.status).tone === 'ok' ? 'green' : 'amber'">
                  {{ subjectStatus(subject.status).label }}
                </span>
                <ChevronDown v-if="subject.items.length" class="chev" />
              </summary>
              <div v-if="subject.items.length" class="table-wrap items">
                <table>
                  <thead>
                    <tr><th>Thứ</th><th>Tiết</th><th>Tên bài</th><th>Đồ dùng</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in subject.items" :key="item.order">
                      <td>{{ item.target_day }}</td>
                      <td>{{ item.target_period }}</td>
                      <td>
                        {{ item.lesson }}
                        <span v-if="item.subject_rename" class="pill blue rename">
                          Đổi tên môn: {{ item.subject_rename.from }} → {{ item.subject_rename.to }}
                        </span>
                      </td>
                      <td>{{ item.equipment ?? '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>
          </li>
        </ul>

        <ul v-if="skipReasons(week).length" class="notes warn">
          <li v-for="w in skipReasons(week)" :key="w.message"><Flag /><span>{{ w.message }}</span></li>
        </ul>
        <ul v-if="minorNotes(week).length" class="notes">
          <li v-for="w in minorNotes(week)" :key="w.message"><AlertTriangle /><span>{{ w.message }}</span></li>
        </ul>
      </template>
    </article>

    <template #footer>
      <button type="button" class="btn btn-secondary" :disabled="busy" @click="sync.backToSelection()">
        <ChevronLeft /> Chọn lại tuần/môn
      </button>
      <span v-if="sync.status === 'analyzing'" class="muted small"><Loader2 class="spin inline" /> Đang phân tích lại…</span>
      <button type="button" class="btn btn-primary" :disabled="!sync.analysis.can_generate || busy" @click="sync.generate()">
        <Loader2 v-if="sync.status === 'generating'" class="spin" />
        {{ generateLabel }}
        <ChevronRight v-if="sync.status !== 'generating'" />
      </button>
    </template>
  </AppPanel>
</template>

<style scoped>
.week {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.week + .week {
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}
.week-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.week-head h3 {
  font-size: 1rem;
}

.days {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.days-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 4px;
}
.days-label svg {
  width: 16px;
  height: 16px;
}
.day {
  font: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.day:hover:not(:disabled) {
  border-color: var(--color-border-strong);
  background: var(--color-surface-muted);
}
.day.off {
  background: var(--color-warning-soft);
  border-color: var(--color-warning);
  color: var(--color-warning-strong);
}
.day.partial {
  background: var(--color-warning-soft);
  border-style: dashed;
  border-color: var(--color-warning);
  color: var(--color-warning-strong);
}
.day:disabled {
  opacity: 0.6;
  cursor: wait;
}

/* Subject rows (like answer choices) */
.subjects {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.subjects > li {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  overflow: hidden;
}
.subjects > li.warn {
  border-color: var(--color-warning-border);
  background: var(--color-warning-surface);
}
summary {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  padding: 8px 14px;
  cursor: pointer;
  list-style: none;
}
summary::-webkit-details-marker {
  display: none;
}
details.static summary {
  cursor: default;
}
.status-dot {
  flex: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1px solid var(--color-success-border);
  background: var(--color-success-soft);
  color: var(--color-success);
}
.warn .status-dot {
  border-color: var(--color-warning-border);
  background: var(--color-warning-soft);
  color: var(--color-warning);
}
.status-dot svg {
  width: 15px;
  height: 15px;
  stroke-width: 2.5;
}
.subject-name {
  font-weight: 600;
  flex: 1;
  min-width: 0;
}
.counts {
  white-space: nowrap;
}
.chev {
  flex: none;
  width: 18px;
  height: 18px;
  color: var(--color-text-muted);
  transition: transform 0.15s;
}
details[open] .chev {
  transform: rotate(180deg);
}
.items {
  border-top: 1px solid var(--color-border);
}
.items table {
  font-size: 0.8125rem;
}
.rename {
  margin-left: 6px;
  height: auto;
  white-space: normal;
}

.header-changes {
  border: 1px solid var(--color-primary-muted);
  border-radius: var(--radius);
  background: var(--color-primary-soft);
  padding: var(--space-3) 14px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.header-changes.none {
  background: var(--color-surface-muted);
  border-color: var(--color-border);
  flex-direction: row;
  align-items: center;
  gap: var(--space-3);
}
.header-changes h4 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-secondary);
}
.header-changes h4 svg {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
}
.header-changes table {
  font-size: var(--text-sm);
  background: var(--color-surface);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.header-changes .label {
  font-weight: 500;
  white-space: nowrap;
}
.header-changes .old {
  color: var(--color-text-muted);
  text-decoration: line-through;
}
.header-changes .new {
  font-weight: 600;
  color: var(--color-primary-strong);
}
.header-changes .arrow {
  width: 24px;
  color: var(--color-text-subtle);
}
.header-changes .arrow svg {
  width: 14px;
  height: 14px;
}

.notes {
  list-style: none;
  margin: 0;
  padding: 12px 14px;
  border-radius: var(--radius);
  background: var(--color-surface-muted);
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}
.notes.warn {
  background: var(--color-warning-soft);
  border: 1px solid var(--color-warning-border);
  color: var(--color-warning-text);
}
.notes li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.notes svg {
  flex: none;
  width: 15px;
  height: 15px;
  margin-top: 2px;
  color: var(--color-warning);
}
.inline {
  width: 14px;
  height: 14px;
  vertical-align: -2px;
}

</style>
