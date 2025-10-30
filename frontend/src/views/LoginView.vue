<script setup>
import { ref } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import { useMessageStore } from '@/stores/message_store';
import { useAuthStore } from '@/stores/auth_store';

const router = useRouter();
const username = ref('');
const password = ref('');
const isLoading = ref(false);

const messageStore = useMessageStore();
const authStore = useAuthStore();
const backend_url = authStore.getBackendServerURL();

async function login() {
  isLoading.value = true;
  messageStore.setFlashMessage('');

  try {
    const response = await fetch(`${backend_url}/api/v1/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Login failed');

    if (data.token && data.user) {
      authStore.setToken(data.token);
      authStore.setUserData(data.user);
      messageStore.setFlashMessage('Login successful!');
      router.push('/Dashboard');
    } else {
      messageStore.setFlashMessage('Unexpected server response.');
    }
  } catch (err) {
    messageStore.setFlashMessage(err.message || 'Login failed.');
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-box">
      <h2>Welcome Back</h2>
      <p class="subtitle">Log in to continue</p>

      <form @submit.prevent="login">
        <div class="form-group">
          <label>Username</label>
          <input
            v-model="username"
            type="text"
            placeholder="Enter your username"
            required
          />
        </div>

        <div class="form-group">
          <label>Password</label>
          <input
            v-model="password"
            type="password"
            placeholder="Enter your password"
            required
          />
        </div>

        <button type="submit" class="btn" :disabled="isLoading">
          <span v-if="isLoading">Logging in...</span>
          <span v-else>Login</span>
        </button>

        <p class="signup-text">
          Don't have an account?
          <RouterLink to="/signup">Sign Up</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

