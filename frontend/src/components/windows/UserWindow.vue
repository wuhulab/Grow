<template>
  <div style="display:flex; flex-direction:column; height:100%; background:#f5f5f7;">
    <div class="toolbar">
      <span style="color:#0a3d7a; font-weight:600;">账号管理</span>
      <span style="color:#6e6e73; font-size:11px;">共 {{ users.length }} 个账号</span>
      <button class="btn" style="margin-left:auto;" @click="openCreate">+ 新建</button>
      <button class="btn" @click="refresh">刷新</button>
    </div>

    <div style="flex:1; overflow:auto;">
      <table class="dt">
        <thead>
          <tr>
            <th>账号</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th style="width:200px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="users.length === 0">
            <td colspan="5" class="empty">暂无账号</td>
          </tr>
          <tr v-for="u in users" :key="u.username">
            <td>
              <span style="font-family: ui-monospace, monospace; font-weight:600;">{{ u.username }}</span>
              <span v-if="u.username === currentUser" style="color:#0a84ff; font-size:11px; margin-left:6px;">(我)</span>
            </td>
            <td>
              <span :class="['role-pill', u.role]">{{ u.role === 'admin' ? '管理员' : '用户' }}</span>
            </td>
            <td>
              <span v-if="u.must_change_password" style="color:#c0392b; font-size:11px;">待改密</span>
              <span v-else style="color:#67c23a; font-size:11px;">正常</span>
            </td>
            <td style="font-size:11px; color:#6e6e73;">{{ formatTime(u.created_at) }}</td>
            <td>
              <button class="btn" @click="openResetPwd(u)">重置密码</button>
              <button class="btn" @click="toggleRole(u)">
                {{ u.role === 'admin' ? '降为用户' : '升为管理' }}
              </button>
              <button class="btn danger" :disabled="u.username === currentUser" @click="del(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建对话框 -->
    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <div class="modal">
        <div class="modal-title">新建账号</div>
        <label class="field">
          <span class="label">账号 (2-32 字符)</span>
          <input v-model.trim="form.username" maxlength="32" />
        </label>
        <label class="field">
          <span class="label">密码 (至少 6 位)</span>
          <input v-model="form.password" type="password" />
        </label>
        <label class="field">
          <span class="label">角色</span>
          <select v-model="form.role">
            <option value="user">用户</option>
            <option value="admin">管理员</option>
          </select>
        </label>
        <div v-if="modalError" class="error">{{ modalError }}</div>
        <div class="modal-actions">
          <button class="btn" @click="showCreate = false">取消</button>
          <button class="btn-primary" :disabled="saving" @click="submitCreate">
            {{ saving ? '创建中…' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 重置密码对话框 -->
    <div v-if="showReset" class="modal-mask" @click.self="showReset = false">
      <div class="modal">
        <div class="modal-title">重置密码 · {{ resetTarget?.username }}</div>
        <label class="field">
          <span class="label">新密码 (至少 6 位)</span>
          <input v-model="resetPwd" type="password" />
        </label>
        <label class="field checkbox">
          <input type="checkbox" v-model="resetMustChange" />
          <span>下次登录必须修改</span>
        </label>
        <div v-if="modalError" class="error">{{ modalError }}</div>
        <div class="modal-actions">
          <button class="btn" @click="showReset = false">取消</button>
          <button class="btn-primary" :disabled="saving" @click="submitReset">
            {{ saving ? '提交中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { authApi } from '../../api'
import { auth } from '../../store/auth'

const users = ref([])
const showCreate = ref(false)
const showReset = ref(false)
const resetTarget = ref(null)
const resetPwd = ref('')
const resetMustChange = ref(true)
const form = ref({ username: '', password: '', role: 'user' })
const saving = ref(false)
const modalError = ref('')
let timer = null

const currentUser = auth.user?.username

async function refresh() {
  try {
    users.value = await authApi.listUsers()
    users.value.sort((a, b) => (a.created_at || 0) - (b.created_at || 0))
  } catch (e) {
    if (e?.response?.status !== 401) {
      console.warn('list users failed', e)
    }
  }
}

function openCreate() {
  form.value = { username: '', password: '', role: 'user' }
  modalError.value = ''
  showCreate.value = true
}

async function submitCreate() {
  if (saving.value) return
  if (form.value.username.length < 2) { modalError.value = '账号至少 2 字符'; return }
  if (form.value.password.length < 6) { modalError.value = '密码至少 6 位'; return }
  saving.value = true
  modalError.value = ''
  try {
    await authApi.createUser(form.value.username, form.value.password, form.value.role)
    showCreate.value = false
    await refresh()
  } catch (e) {
    modalError.value = e?.response?.data?.detail || '创建失败'
  } finally {
    saving.value = false
  }
}

function openResetPwd(u) {
  resetTarget.value = u
  resetPwd.value = ''
  resetMustChange.value = true
  modalError.value = ''
  showReset.value = true
}

async function submitReset() {
  if (saving.value) return
  if (resetPwd.value.length < 6) { modalError.value = '密码至少 6 位'; return }
  saving.value = true
  modalError.value = ''
  try {
    await authApi.updateUser(resetTarget.value.username, {
      password: resetPwd.value,
      must_change_password: resetMustChange.value
    })
    showReset.value = false
  } catch (e) {
    modalError.value = e?.response?.data?.detail || '重置失败'
  } finally {
    saving.value = false
  }
}

async function toggleRole(u) {
  const next = u.role === 'admin' ? 'user' : 'admin'
  try {
    await authApi.updateUser(u.username, { role: next })
    await refresh()
  } catch (e) {
    alert(e?.response?.data?.detail || '修改角色失败')
  }
}

async function del(u) {
  if (!confirm(`确认删除账号 ${u.username}?`)) return
  try {
    await authApi.deleteUser(u.username)
    await refresh()
  } catch (e) {
    alert(e?.response?.data?.detail || '删除失败')
  }
}

function formatTime(t) {
  if (!t) return '-'
  try { return new Date(t * 1000).toLocaleString() } catch { return '-' }
}

onMounted(() => { refresh(); timer = setInterval(refresh, 10000) })
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.role-pill {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.role-pill.admin { background: rgba(10, 132, 255, 0.12); color: #0a3d7a; }
.role-pill.user { background: rgba(0, 0, 0, 0.06); color: #1d1d1f; }

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal {
  width: 360px;
  background: #ffffff;
  border-radius: 14px;
  padding: 22px 22px 16px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.32);
  user-select: none;
}

.modal-title {
  font-size: 14px;
  font-weight: 700;
  color: #1d1d1f;
  margin-bottom: 14px;
}

.field {
  display: block;
  margin-bottom: 12px;
}

.field.checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #1d1d1f;
}

.field.checkbox input { width: auto; }

.field .label {
  display: block;
  font-size: 11px;
  color: #6e6e73;
  font-weight: 600;
  margin-bottom: 4px;
}

.field input, .field select {
  width: 100%;
  padding: 8px 10px;
  font-size: 13px;
  font-family: inherit;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  outline: none;
  background: #ffffff;
  color: #1d1d1f;
}

.field input:focus, .field select:focus {
  border-color: #0a84ff;
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.18);
}

.error {
  color: #c0392b;
  font-size: 12px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.2);
  border-radius: 8px;
  padding: 6px 10px;
  margin-bottom: 10px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
}

.btn-primary {
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
  background: #0a84ff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.btn-primary:hover:not(:disabled) { background: #006ee6; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
