import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'
import LoginPage from '../pages/LoginPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import TimetableSyncPage from '../pages/TimetableSyncPage.vue'
import { setUnauthenticatedHandler } from '../services/api'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'login', component: LoginPage, meta: { guest: true, title: 'Đăng nhập' } },
  {
    path: '/',
    component: AppLayout,
    children: [
      { path: '', name: 'dashboard', component: DashboardPage, meta: { title: 'Tổng quan' } },
      { path: 'lich-bao-giang', name: 'timetable-sync', component: TimetableSyncPage, meta: { title: 'Lịch báo giảng' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Every page except /login needs a session (DETAIL_DESIGN §3.1 A).
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.check()

  if (to.meta.guest) {
    return auth.loggedIn ? { path: typeof to.query.redirect === 'string' ? to.query.redirect : '/' } : true
  }
  return auth.loggedIn ? true : { name: 'login', query: { redirect: to.fullPath } }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · Teacher Workspace` : 'Teacher Workspace'
})

// Session expired while using the app: back to login, then return here.
setUnauthenticatedHandler(() => {
  useAuthStore().forget()
  const current = router.currentRoute.value
  if (current.name !== 'login') router.push({ name: 'login', query: { redirect: current.fullPath } })
})

export default router
