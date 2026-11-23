import { defineStore } from 'pinia'
import { apiError } from '../services/api'
import * as timetable from '../services/timetable'
import { initialSubjects, saveSubjects, toggleDayOff } from '../utils/timetable'

// A page reload (or the phone discarding the tab) must not force a new upload: remember the job id
// for this browser tab and restore the job from the server while it has not expired.
const JOB_KEY = 'tw.timetable.jobId'

function rememberJob(jobId) {
  try {
    if (jobId) sessionStorage.setItem(JOB_KEY, jobId)
    else sessionStorage.removeItem(JOB_KEY)
  } catch {
    // storage blocked: reload simply starts over
  }
}

function rememberedJob() {
  try {
    return sessionStorage.getItem(JOB_KEY)
  } catch {
    return null
  }
}

/**
 * Timetable sync wizard (DETAIL_DESIGN §10.2–§10.3).
 * status: idle → uploading → uploaded → analyzing → preview_ready → generating → completed
 *         (+ upload_failed, analysis_failed, generate_failed, job_expired)
 */
export const useSyncStore = defineStore('sync', {
  state: () => ({
    step: 1,
    status: 'idle',
    error: null, // { code, message, details }
    uploadProgress: 0,
    job: null, // upload response: job_id, file names, weeks, subjects, days, …
    selectedWeeks: [],
    selectedSubjects: [],
    manualDaysOff: [],
    analysis: null,
    result: null,
  }),

  getters: {
    busy: (s) => ['uploading', 'analyzing', 'generating'].includes(s.status),
    selectableWeeks: (s) => (s.job?.weeks ?? []).filter((w) => w.selectable).map((w) => w.week_number),
    selection(s) {
      const weeks = [...s.selectedWeeks].sort((a, b) => a - b)
      return {
        weeks,
        selected_subjects: [...s.selectedSubjects],
        manual_days_off: s.manualDaysOff.filter((m) => weeks.includes(m.week_number)),
      }
    },
  },

  actions: {
    fail(status, error) {
      const err = apiError(error)
      if (err.code === 'JOB_NOT_FOUND') {
        // Job expired or the server restarted (Render Free sleeps): start over (§6.4).
        this.$reset()
        rememberJob(null)
        this.status = 'job_expired'
      } else {
        this.status = status
      }
      this.error = err
    },

    async upload(source, target) {
      if (this.busy) return
      this.status = 'uploading'
      this.error = null
      this.uploadProgress = 0
      try {
        this.useJob(await timetable.uploadFiles(source, target, (p) => (this.uploadProgress = p)))
      } catch (e) {
        this.fail('upload_failed', e)
      }
    },

    useJob(job) {
      this.job = job
      // One-sheet target: the teacher picks ONE source week; otherwise every ready week is pre-selected.
      this.selectedWeeks = job.max_weeks === 1 ? [] : job.weeks.filter((w) => w.selectable).map((w) => w.week_number)
      this.selectedSubjects = initialSubjects(job.subjects, job.default_selected_subjects)
      this.manualDaysOff = []
      this.analysis = null
      this.result = null
      this.status = 'uploaded'
      this.step = 2
      rememberJob(job.job_id)
    },

    /** On page load: continue the job of this tab if the server still has it (back to step 2). */
    async restore() {
      const jobId = rememberedJob()
      if (this.job || !jobId) return
      try {
        this.useJob(await timetable.getJob(jobId))
      } catch {
        rememberJob(null) // expired or gone: start from step 1 without an error message
      }
    },

    async analyze() {
      if (this.busy || !this.job) return
      saveSubjects(this.job.subjects, this.selectedSubjects)
      this.status = 'analyzing'
      this.error = null
      try {
        this.analysis = await timetable.analyze(this.job.job_id, this.selection)
        this.result = null
        this.status = 'preview_ready'
        this.step = 3
      } catch (e) {
        this.fail('analysis_failed', e)
      }
    },

    /** Teacher marks/unmarks a whole day off in the preview; re-analyzes (§4.8). */
    async toggleDay(weekNumber, day, currentState) {
      if (this.busy) return
      this.manualDaysOff = toggleDayOff(this.manualDaysOff, weekNumber, day, currentState)
      await this.analyze()
    },

    async generate() {
      if (this.busy || !this.analysis?.can_generate) return // never twice at once (§10.3)
      this.status = 'generating'
      this.error = null
      try {
        this.result = await timetable.generate(this.job.job_id, this.selection)
        this.status = 'completed'
        this.step = 4
      } catch (e) {
        this.fail('generate_failed', e)
      }
    },

    backToSelection() {
      if (this.busy) return
      this.error = null
      this.status = 'uploaded'
      this.step = 2
    },

    /** New run: drop the server copy of the files right away instead of waiting for the TTL. */
    async startOver() {
      const jobId = this.job?.job_id
      this.$reset()
      rememberJob(null)
      if (jobId) {
        try {
          await timetable.deleteJob(jobId)
        } catch {
          // already expired or gone: nothing to clean up
        }
      }
    },
  },
})
