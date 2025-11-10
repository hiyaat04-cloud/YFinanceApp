<script setup>
import { ref } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import { useMessageStore } from '@/stores/message_store';
import { useAuthStore } from '@/stores/auth_store';
import axios from 'axios';

const router = useRouter();
const username = ref('');
const email = ref('');
const password = ref('');
const confirm_password = ref('');
const isLoading = ref(false);

const messageStore = useMessageStore();
const authStore = useAuthStore();
const backendURL = authStore.getBackendServerURL();

function validateInput() {
  if (!username.value || !email.value || !password.value) {
    messageStore.setFlashMessage('All fields are required.');
    return false;
  }
  if (password.value !== confirm_password.value) {
    messageStore.setFlashMessage('Passwords do not match.');
    return false;
  }
  if (password.value.length < 8) {
    messageStore.setFlashMessage('Password must be at least 8 characters.');
    return false;
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!emailRegex.test(email.value)) {
    messageStore.setFlashMessage('Enter a valid email address.');
    return false;
  }
  return true;
}

async function registerUser(userData) {
  isLoading.value = true;
  messageStore.setFlashMessage('');
  try {
    const res = await axios.post(`${backendURL}/api/v1/signup`, userData, {
      headers: { 'Content-Type': 'application/json' },
    });
    return { ok: true, msg: res.data.message || 'Signup successful.' };
  } catch (err) {
    const msg =
      err.response?.data?.message ||
      err.response?.data?.error ||
      'Signup failed.';
    return { ok: false, msg };
  } finally {
    isLoading.value = false;
  }
}

async function onSubmit() {
  if (!validateInput()) return;
  const payload = { username: username.value, email: email.value, password: password.value };
  const result = await registerUser(payload);
  messageStore.setFlashMessage(result.msg);
  if (result.ok) router.push('/login');
}
</script>

<template>
  <div class="signup-wrapper">
    <div class="signup-box">
      <h2>Create Account</h2>
      <p class="subtitle">Join us and get started</p>

      <form @submit.prevent="onSubmit">
        <div class="form-group">
          <label>Username</label>
          <input v-model="username" type="text" placeholder="Choose a username" required />
        </div>

        <div class="form-group">
          <label>Email</label>
          <input v-model="email" type="email" placeholder="your@email.com" required />
        </div>

        <div class="form-group">
          <label>Password</label>
          <input v-model="password" type="password" placeholder="Minimum 8 characters" required />
        </div>

        <div class="form-group">
          <label>Confirm Password</label>
          <input v-model="confirm_password" type="password" placeholder="Re-enter password" required />
        </div>

        <button type="submit" class="btn" :disabled="isLoading">
          <span v-if="isLoading">Registering...</span>
          <span v-else>Sign Up</span>
        </button>

        <p class="login-text">
          Already have an account?
          <RouterLink to="/login">Login here</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

