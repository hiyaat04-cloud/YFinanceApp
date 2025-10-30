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

  const input_data = { username: username.value, password: password.value };

  try {
    const response = await fetch(`${backend_url}/api/v1/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input_data),
    });

    const data = await response.json();

    if (!response.ok) throw new Error(data.message || 'Login failed');

    if (data.token && data.user) {
      authStore.setToken(data.token);
      authStore.setUserData(data.user);
      messageStore.setFlashMessage('Login successful!');
      router.push('/Dashboard');
    } else {
      messageStore.setFlashMessage('Unexpected response from server.');
    }
  } catch (error) {
    console.error('Login Error:', error);
    messageStore.setFlashMessage(error.message || 'Login failed.');
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-card">
      <h2 class="login-title text-center mb-4">Login</h2>
      <form @submit.prevent="login">
        <div class="mb-3">
          <label for="usernameInput" class="form-label">Username</label>
          <input
            id="usernameInput"
            type="text"
            v-model="username"
            required
            class="form-control form-control-lg"
            placeholder="Enter your username"
          />
        </div>

        <div class="mb-3">
          <label for="passwordInput" class="form-label">Password</label>
          <input
            id="passwordInput"
            type="password"
            v-model="password"
            required
            class="form-control form-control-lg"
            placeholder="Enter your password"
          />
        </div>

        <button
          type="submit"
          class="btn btn-primary w-100 py-2 mt-3"
          :disabled="isLoading"
        >
          <span
            v-if="isLoading"
            class="spinner-border spinner-border-sm me-2"
            role="status"
          ></span>
          {{ isLoading ? 'Logging in...' : 'Login' }}
        </button>

        <p class="text-center mt-4">
          Don’t have an account?
          <RouterLink to="/signup" class="signup-link">Sign Up</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-wrapper {
  height: 100vh;
  background: linear-gradient(135deg, #e3f2fd, #f8f9fa);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.login-card {
  background: #fff;
  width: 100%;
  max-width: 400px;
  border-radius: 16px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  padding: 2.5rem;
  animation: fadeIn 0.6s ease-in-out;
}

.login-title {
  font-weight: 600;
  color: #2c3e50;
}

.form-label {
  font-weight: 500;
  color: #495057;
}

.form-control {
  border-radius: 10px;
  padding: 0.8rem 1rem;
  font-size: 1rem;
  border: 1px solid #ced4da;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-control:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.15);
}

.btn-primary {
  font-size: 1rem;
  border-radius: 10px;
  font-weight: 500;
  transition: background-color 0.2s ease-in-out;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.signup-link {
  color: #007bff;
  font-weight: 500;
  text-decoration: none;
}

.signup-link:hover {
  text-decoration: underline;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
