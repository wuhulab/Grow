<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-title">Graw</div>
      <div class="login-subtitle">服务器管理面板</div>

      <form v-if="!forceChange" @submit.prevent="handleLogin">
        <label class="field">
          <span class="label">账号</span>
          <input
            v-model.trim="username"
            type="text"
            autocomplete="username"
            autofocus
            spellcheck="false"
            required
          />
        </label>
        <label class="field">
          <span class="label">密码</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
          />
        </label>
        <div v-if="error" class="error">{{ error }}</div>
        <button class="btn-primary" type="submit" :disabled="loading">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <form v-else @submit.prevent="handleChangePassword">
        <div class="hint">首次登录或密码已重置，请设置新密码</div>
        <label class="field">
          <span class="label">原密码</span>
          <input v-model="oldPassword" type="password" required />
        </label>
        <label class="field">
          <span class="label">新密码</span>
          <input v-model="newPassword" type="password" minlength="6" required />
        </label>
        <label class="field">
          <span class="label">确认新密码</span>
          <input v-model="confirmPassword" type="password" minlength="6" required />
        </label>
        <div v-if="error" class="error">{{ error }}</div>
        <button class="btn-primary" type="submit" :disabled="loading">
          {{ loading ? '提交中…' : '更新密码并进入' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authApi } from '../api'
import { setAuth, clearAuth } from '../store/auth'

const emit = defineEmits(['login'])

const username = ref('admin')
const password = ref('')
const loading = ref(false)
const error = ref('')

const forceChange = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

async function handleLogin() {
  if (loading.value) return
  error.value = ''
  loading.value = true
  try {
    const data = await authApi.login(username.value, password.value)
    setAuth(data.token, data.user)
    if (data.user?.must_change_password) {
      oldPassword.value = password.value
      password.value = ''
      forceChange.value = true
      return
    }
    emit('login', data.user)
  } catch (e) {
    error.value = e?.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}

async function handleChangePassword() {
  if (loading.value) return
  if (newPassword.value.length < 6) {
    error.value = '新密码至少 6 位'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入的新密码不一致'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await authApi.changePassword(oldPassword.value, newPassword.value)
    const user = auth.user
    if (user) {
      user.must_change_password = false
      setAuth(auth.token, user)
    }
    forceChange.value = false
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    emit('login', user)
  } catch (e) {
    error.value = e?.response?.data?.detail || '修改失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #1f2937;
  background-image: url('../assets/hero.png');
  background-size: cover;
  background-position: center;
}

.login-card {
  width: 360px;
  padding: 32px 32px 28px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 18px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.32), 0 2px 6px rgba(0, 0, 0, 0.12);
  backdrop-filter: saturate(180%) blur(28px);
  -webkit-backdrop-filter: saturate(180%) blur(28px);
  user-select: none;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #0a3d7a;
  letter-spacing: 0.5px;
}

.login-subtitle {
  font-size: 12px;
  color: #6e6e73;
  margin-bottom: 22px;
}

.field {
  display: block;
  margin-bottom: 14px;
}

.field .label {
  display: block;
  font-size: 11px;
  color: #1d1d1f;
  font-weight: 600;
  margin-bottom: 6px;
}

.field input {
  width: 100%;
  padding: 9px 12px;
  font-size: 13px;
  font-family: inherit;
  color: #1d1d1f;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  outline: none;
}

.field input:focus {
  border-color: #0a84ff;
  box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.2);
}

.hint {
  background: rgba(10, 132, 255, 0.12);
  color: #0a3d7a;
  border: 1px solid rgba(10, 132, 255, 0.3);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  margin-bottom: 14px;
}

.error {
  color: #c0392b;
  font-size: 12px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.2);
  border-radius: 8px;
  padding: 6px 10px;
  margin-bottom: 12px;
}

.btn-primary {
  width: 100%;
  margin-top: 4px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  background: #0a84ff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) { background: #006ee6; }
.btn-primary:active:not(:disabled) { background: #0058b8; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
