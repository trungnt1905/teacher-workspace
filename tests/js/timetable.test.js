import { describe, expect, it } from 'vitest'
import {
  checkFile,
  dayState,
  formatSize,
  groupTodo,
  initialSubjects,
  saveSubjects,
  skippedCount,
  subjectStatus,
  todoText,
  toggleDayOff,
  unavailableGroups,
} from '../../resources/js/utils/timetable.js'

function memoryStorage(initial = {}) {
  const data = { ...initial }
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => {
      data[k] = v
    },
    data,
  }
}

const KEY = 'tw.timetable.selectedSubjects'

describe('file checks', () => {
  it('accepts xlsx within the limit', () => {
    expect(checkFile({ name: 'LBG.XLSX', size: 1000 })).toBeNull()
  })
  it('rejects xls and oversize files', () => {
    expect(checkFile({ name: 'lbg.xls', size: 10 })).toMatch(/\.xlsx/)
    expect(checkFile({ name: 'lbg.xlsx', size: 6 * 1024 * 1024 }, 5)).toBe('File vượt quá 5MB.')
  })
  it('formats sizes', () => {
    expect(formatSize(500)).toBe('500 B')
    expect(formatSize(250 * 1024)).toBe('250 KB')
    expect(formatSize(3.2 * 1024 * 1024)).toBe('3.2 MB')
  })
})

describe('subject selection memory', () => {
  const available = ['Tiếng Việt', 'Toán', 'Tiếng Anh', 'HĐTV/HĐTT']

  it('uses server defaults the first time', () => {
    expect(initialSubjects(available, ['Tiếng Việt', 'Toán'], memoryStorage())).toEqual(['Tiếng Việt', 'Toán'])
  })

  it('restores the last choice, limited to subjects in these files', () => {
    const storage = memoryStorage({ [KEY]: JSON.stringify(['Toán', 'Tiếng Anh', 'Môn khác']) })
    expect(initialSubjects(available, ['Tiếng Việt'], storage)).toEqual(['Toán', 'Tiếng Anh'])
  })

  it('survives broken storage content', () => {
    expect(initialSubjects(available, ['Toán'], memoryStorage({ [KEY]: '{oops' }))).toEqual(['Toán'])
    expect(initialSubjects(available, ['Toán'], null)).toEqual(['Toán'])
  })

  it('saves ticks and keeps choices for subjects absent from these files', () => {
    const storage = memoryStorage({ [KEY]: JSON.stringify(['Khoa học', 'Toán']) })
    saveSubjects(available, ['Tiếng Việt'], storage)
    expect(JSON.parse(storage.data[KEY])).toEqual(['Khoa học', 'Tiếng Việt'])
  })
})

describe('days off', () => {
  const sessions = ['SÁNG', 'CHIỀU']
  const daysOff = [
    { day: 'Năm', session: 'SÁNG', detected_by: 'auto' },
    { day: 'Năm', session: 'CHIỀU', detected_by: 'auto' },
    { day: 'Sáu', session: 'CHIỀU', detected_by: 'manual' },
  ]

  it('derives the state of each day', () => {
    expect(dayState(daysOff, 'Năm', sessions)).toBe('off')
    expect(dayState(daysOff, 'Sáu', sessions)).toBe('partial')
    expect(dayState(daysOff, 'Hai', sessions)).toBe('on')
  })

  it('toggles a whole day and replaces the previous override for that day', () => {
    let overrides = toggleDayOff([], 7, 'Hai', 'on')
    expect(overrides).toEqual([{ week_number: 7, day: 'Hai', is_day_off: true }])
    overrides = toggleDayOff(overrides, 7, 'Hai', 'off')
    expect(overrides).toEqual([{ week_number: 7, day: 'Hai', is_day_off: false }])
    overrides = toggleDayOff(overrides, 8, 'Sáu', 'partial')
    expect(overrides).toHaveLength(2)
    expect(overrides[1]).toEqual({ week_number: 8, day: 'Sáu', is_day_off: false })
  })
})

describe('unavailable weeks', () => {
  it('groups missing / has-data weeks and keeps other errors separate', () => {
    const weeks = [
      { week_number: 1, selectable: false, target_status: 'missing', errors: [{ message: 'x' }] },
      { week_number: 2, selectable: false, target_status: 'missing', errors: [{ message: 'x' }] },
      { week_number: 3, selectable: false, target_status: 'has_data', errors: [{ message: 'y' }] },
      { week_number: 4, selectable: false, target_status: 'invalid_structure', errors: [{ message: 'Sai cấu trúc' }] },
      { week_number: 8, selectable: true, target_status: 'ready', errors: [] },
    ]
    const groups = unavailableGroups(weeks)
    expect(groups.map((g) => g.title)).toEqual(['Chưa có sheet trong file đích', 'Sheet đã có dữ liệu (bỏ qua)', 'Tuần 4'])
    expect(groups[0].text).toMatch(/^Tuần 1, Tuần 2 — /)
    expect(groups[2].text).toBe('Sai cấu trúc')
  })

  it('returns nothing when every week is selectable', () => {
    expect(unavailableGroups([{ week_number: 1, selectable: true, errors: [] }])).toEqual([])
  })
})

describe('results', () => {
  it('labels subject statuses', () => {
    expect(subjectStatus('matched')).toEqual({ label: 'Điền', tone: 'ok' })
    expect(subjectStatus('skipped_day_off').label).toBe('Bỏ qua — trùng ngày nghỉ')
    expect(subjectStatus('something_new').label).toBe('something_new')
  })

  it('counts skipped subjects', () => {
    const analysis = { weeks: [
      { subjects: [{ status: 'matched' }, { status: 'skipped_day_off' }] },
      { subjects: [{ status: 'skipped_empty_lesson' }] },
    ] }
    expect(skippedCount(analysis)).toBe(2)
    expect(skippedCount(null)).toBe(0)
  })

  it('groups the manual to-do list by week', () => {
    const todo = [
      { week_number: 8, code: 'EMPTY_LESSON', message: 'B' },
      { week_number: 7, code: 'AFFECTED_BY_DAY_OFF', message: 'A' },
      { week_number: 8, code: 'X', message: 'C' },
    ]
    expect(groupTodo(todo)).toEqual([{ week: 7, messages: ['A'] }, { week: 8, messages: ['B', 'C'] }])
    expect(todoText(todo)).toBe('Tuần 7:\n  - A\nTuần 8:\n  - B\n  - C')
  })
})
