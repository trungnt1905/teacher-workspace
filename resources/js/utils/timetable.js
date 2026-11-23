// Pure helpers for the timetable sync wizard (no Vue, no network) — unit tested in tests/js.

export const TARGET_STATUS = {
  ready: 'Sẵn sàng',
  has_data: 'Đã có dữ liệu',
  missing: 'Chưa có sheet',
  invalid_structure: 'Sai cấu trúc',
  duplicate: 'Trùng sheet',
}

export const SUBJECT_STATUS = {
  matched: { label: 'Điền', tone: 'ok' },
  skipped_count_mismatch: { label: 'Bỏ qua — lệch số tiết', tone: 'warn' },
  skipped_day_off: { label: 'Bỏ qua — trùng ngày nghỉ', tone: 'warn' },
  skipped_empty_lesson: { label: 'Bỏ qua — nguồn chưa có tên bài', tone: 'warn' },
  skipped_unknown_subject: { label: 'Bỏ qua — chỉ có ở một file', tone: 'warn' },
}

export function subjectStatus(status) {
  return SUBJECT_STATUS[status] ?? { label: status, tone: 'warn' }
}

export function formatSize(bytes) {
  if (!Number.isFinite(bytes)) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

/** Client-side pre-check; the server validates again. Returns an error message or null. */
export function checkFile(file, maxMb = 5) {
  if (!file) return null
  if (!/\.xlsx$/i.test(file.name)) return 'Chỉ hỗ trợ file .xlsx. Nếu file là .xls, hãy mở bằng Excel và “Lưu thành” .xlsx.'
  if (file.size > maxMb * 1024 * 1024) return `File vượt quá ${maxMb}MB.`
  return null
}

const SUBJECTS_KEY = 'tw.timetable.selectedSubjects'

/**
 * Subjects ticked at start: the teacher's last choice (restricted to subjects present in these
 * files) or, the first time, the server defaults (§4.9).
 */
export function initialSubjects(available, defaults, storage = safeStorage()) {
  let saved = null
  try {
    saved = JSON.parse(storage?.getItem(SUBJECTS_KEY) ?? 'null')
  } catch {
    saved = null
  }
  if (!Array.isArray(saved)) return available.filter((s) => defaults.includes(s))
  return available.filter((s) => saved.includes(s))
}

/** Remember ticks. Keeps choices for subjects not present in the current files. */
export function saveSubjects(available, selected, storage = safeStorage()) {
  try {
    const previous = JSON.parse(storage?.getItem(SUBJECTS_KEY) ?? '[]')
    const kept = Array.isArray(previous) ? previous.filter((s) => !available.includes(s)) : []
    storage?.setItem(SUBJECTS_KEY, JSON.stringify([...kept, ...selected]))
  } catch {
    // storage may be blocked (private mode): the choice simply is not remembered
  }
}

function safeStorage() {
  try {
    return globalThis.localStorage ?? null
  } catch {
    return null
  }
}

/** 'off' (whole day), 'partial' (one session) or 'on' for a day of an analyzed week. */
export function dayState(daysOff, day, sessions) {
  const off = daysOff.filter((d) => d.day === day).map((d) => d.session)
  if (off.length === 0) return 'on'
  return sessions.every((s) => off.includes(s)) ? 'off' : 'partial'
}

/**
 * Toggle a whole day: if it is (partly) off it becomes a school day, otherwise a day off.
 * Returns the new manual override list (one entry per week+day).
 */
export function toggleDayOff(overrides, weekNumber, day, currentState) {
  const rest = overrides.filter((o) => !(o.week_number === weekNumber && o.day === day))
  return [...rest, { week_number: weekNumber, day, is_day_off: currentState === 'on' }]
}

/**
 * Why a source week cannot be selected: 'target_missing' (the target file has no sheet for it),
 * 'has_data' (the target sheet is already filled) or 'error' (sheet unreadable, duplicate, …).
 */
export function weekProblem(week) {
  if (week.selectable) return null
  const codes = week.errors.map((e) => e.code)
  if (codes.length === 1 && codes[0] === 'TARGET_WEEK_SHEET_MISSING') return 'target_missing'
  if (codes.length === 1 && codes[0] === 'TARGET_WEEK_HAS_DATA') return 'has_data'
  return 'error'
}

/**
 * Reasons why weeks cannot be selected, grouped so that the same reason for several weeks is one
 * line ("Tuần 9, Tuần 10…") instead of repeated messages. Other problems keep their own message.
 */
export function unavailableGroups(weeks) {
  const grouped = { target_missing: [], has_data: [] }
  const others = []
  for (const w of weeks ?? []) {
    const problem = weekProblem(w)
    if (!problem) continue
    if (problem in grouped) grouped[problem].push(w.week_number)
    else others.push(...w.errors.map((e) => ({ tone: 'red', title: `Tuần ${w.week_number}`, text: e.message })))
  }
  const list = (nums) => nums.map((n) => `Tuần ${n}`).join(', ')
  const groups = []
  if (grouped.target_missing.length) {
    groups.push({ tone: 'amber', title: 'File đích không có sheet cho tuần này', text: `${list(grouped.target_missing)} — dùng file đích chỉ có một sheet (ví dụ file mẫu) hoặc thêm sheet “TUẦN n”.` })
  }
  if (grouped.has_data.length) {
    groups.push({ tone: 'gray', title: 'Sheet đã có dữ liệu (bỏ qua)', text: `${list(grouped.has_data)} — muốn làm lại thì dùng sheet tuần còn trống.` })
  }
  return [...groups, ...others]
}

/** Number of subjects (across weeks) that the teacher has to fill by hand. */
export function skippedCount(analysis) {
  return (analysis?.weeks ?? []).reduce(
    (n, w) => n + w.subjects.filter((s) => s.status !== 'matched').length,
    0,
  )
}

/** Manual to-do grouped by week for the result page (§10.2 step 4). */
export function groupTodo(todo) {
  const groups = new Map()
  for (const item of todo ?? []) {
    if (!groups.has(item.week_number)) groups.set(item.week_number, [])
    groups.get(item.week_number).push(item.message)
  }
  return [...groups.entries()].sort((a, b) => a[0] - b[0]).map(([week, messages]) => ({ week, messages }))
}

/** Plain-text version of the to-do list for copy/print. */
export function todoText(todo) {
  return groupTodo(todo)
    .map((g) => [`Tuần ${g.week}:`, ...g.messages.map((m) => `  - ${m}`)].join('\n'))
    .join('\n')
}
