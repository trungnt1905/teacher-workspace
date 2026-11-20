<script setup>
import { computed } from 'vue'
import { useSyncStore } from '../../stores/sync'
import { dayState, skippedCount, subjectStatus } from '../../utils/timetable'

const sync = useSyncStore()

const weeks = computed(() => sync.analysis?.weeks ?? [])
const days = computed(() => sync.job?.days ?? [])
const skipped = computed(() => skippedCount(sync.analysis))
const busy = computed(() => sync.busy)

const generateLabel = computed(() => {
  if (sync.status === 'generating') return 'Đang tạo file…'
  return skipped.value > 0 ? `Tạo file (${skipped.value} môn cần điền thủ công)` : 'Tạo file'
})

const DAY_STATE_TEXT = { on: 'Đi học', off: 'Nghỉ', partial: 'Nghỉ một buổi' }

function stateOf(week, day) {
  return dayState(week.days_off, day.label, day.sessions)
}

function autoDetected(week, day) {
  return week.days_off.some((d) => d.day === day.label && d.detected_by === 'auto')
}

// Reasons for skipped subjects first, then minor notes (long lesson names).
function skipReasons(week) {
  return week.warnings.filter((w) => w.code !== 'CONTENT_TOO_LONG')
}

function minorNotes(week) {
  return week.warnings.filter((w) => w.code === 'CONTENT_TOO_LONG')
}
</script>

<template>
  <section class="step">
    <p v-if="!sync.analysis.can_generate" class="alert alert-warn">
      Không có môn nào đủ điều kiện để điền. Kiểm tra lại tuần/môn đã chọn hoặc ngày nghỉ bên dưới.
    </p>

    <article v-for="week in weeks" :key="week.week_number" class="card week">
      <header class="week-head">
        <h2>Tuần {{ week.week_number }}</h2>
        <span v-if="week.status === 'blocked'" class="badge error">Không xử lý được</span>
      </header>

      <template v-if="week.status === 'blocked'">
        <p v-for="err in week.errors" :key="err.code + err.message" class="alert alert-error">{{ err.message }}</p>
      </template>

      <template v-else>
        <div class="days">
          <span class="muted">Ngày nghỉ (bấm để đổi):</span>
          <button v-for="day in days" :key="day.label" type="button" class="day" :class="stateOf(week, day)"
                  :disabled="busy" :title="autoDetected(week, day) ? 'Tự phát hiện từ file nguồn' : ''"
                  @click="sync.toggleDay(week.week_number, day.label, stateOf(week, day))">
            Thứ {{ day.label }}: {{ DAY_STATE_TEXT[stateOf(week, day)] }}
          </button>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Môn</th>
                <th class="num">Nguồn</th>
                <th class="num">Đích</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="subject in week.subjects" :key="subject.subject">
                <tr>
                  <td>{{ subject.subject }}</td>
                  <td class="num">{{ subject.source_count }}</td>
                  <td class="num">{{ subject.target_count }}</td>
                  <td>
                    <span class="badge" :class="subjectStatus(subject.status).tone">{{ subjectStatus(subject.status).label }}</span>
                  </td>
                </tr>
                <tr v-if="subject.items.length" class="detail-row">
                  <td colspan="4">
                    <details>
                      <summary>Xem {{ subject.items.length }} tiết sẽ điền</summary>
                      <div class="table-wrap">
                        <table class="items">
                          <thead>
                            <tr><th>Thứ</th><th>Tiết</th><th>Tên bài</th><th>Đồ dùng</th></tr>
                          </thead>
                          <tbody>
                            <tr v-for="item in subject.items" :key="item.order">
                              <td>{{ item.target_day }}</td>
                              <td>{{ item.target_period }}</td>
                              <td>
                                {{ item.lesson }}
                                <span v-if="item.subject_rename" class="badge">
                                  Đổi tên môn: {{ item.subject_rename.from }} → {{ item.subject_rename.to }}
                                </span>
                              </td>
                              <td>{{ item.equipment ?? '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </details>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <ul v-if="skipReasons(week).length" class="reasons">
          <li v-for="w in skipReasons(week)" :key="w.message">{{ w.message }}</li>
        </ul>
        <ul v-if="minorNotes(week).length" class="reasons muted">
          <li v-for="w in minorNotes(week)" :key="w.message">{{ w.message }}</li>
        </ul>
      </template>
    </article>

    <div class="actions">
      <button type="button" class="secondary" :disabled="busy" @click="sync.backToSelection()">Quay lại chọn tuần/môn</button>
      <button type="button" :disabled="!sync.analysis.can_generate || busy" @click="sync.generate()">{{ generateLabel }}</button>
    </div>
  </section>
</template>

<style scoped>
.step {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.week {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.week-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.days {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.day {
  padding: 4px 10px;
  font-size: 0.875rem;
  background: var(--surface);
  color: var(--text);
  border-color: var(--border);
}
.day.off {
  background: var(--warn-bg);
  border-color: var(--warn);
  color: var(--warn);
}
.day.partial {
  background: var(--warn-bg);
  border-style: dashed;
  border-color: var(--warn);
  color: var(--warn);
}
.detail-row td {
  padding-top: 0;
}
.detail-row summary {
  cursor: pointer;
  color: var(--primary);
  font-size: 0.875rem;
}
.items {
  margin-top: 6px;
  font-size: 0.875rem;
  background: var(--surface-muted);
}
.reasons {
  margin: 0;
  padding-left: 20px;
  font-size: 0.875rem;
}
</style>
