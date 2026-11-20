import api from './api'

// Timetable sync endpoints (DETAIL_DESIGN §9).

export async function uploadFiles(source, target, onProgress) {
  const form = new FormData()
  form.append('source_file', source)
  form.append('target_file', target)
  const { data } = await api.post('/timetable/jobs', form, {
    onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
  })
  return data.data
}

export async function getJob(jobId) {
  const { data } = await api.get(`/timetable/jobs/${jobId}`)
  return data.data
}

export async function analyze(jobId, selection) {
  const { data } = await api.post(`/timetable/jobs/${jobId}/analyze`, selection)
  return data.data
}

export async function generate(jobId, selection) {
  const { data } = await api.post(`/timetable/jobs/${jobId}/generate`, selection)
  return data.data
}

export async function deleteJob(jobId) {
  await api.delete(`/timetable/jobs/${jobId}`)
}

export function downloadUrl(jobId) {
  return `/api/v1/timetable/jobs/${jobId}/download`
}
