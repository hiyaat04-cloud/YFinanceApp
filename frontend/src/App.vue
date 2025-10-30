<script setup>
import { computed } from 'vue';
import { useRouter, RouterLink, RouterView } from 'vue-router';
import axios from 'axios';
import { useMessageStore } from './stores/message_store';
import { useAuthStore } from './stores/auth_store';

const messageStore = useMessageStore();
const authStore = useAuthStore();
const router = useRouter();

const message = computed(() => messageStore.getFlashMessage());
const user = computed(() => authStore.getUserData());
const isAuthenticated = computed(() => authStore.isAuthenticated);

async function logout() {
  try {
    await fetch(`${authStore.getBackendServerURL()}/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.getToken()}`
      }
    });
  } catch (error) {
    console.warn("Logout endpoint failed or missing:", error);
  } finally {
    authStore.removeAuthUser();
    messageStore.setFlashMessage("You have been logged out.");
    router.push('/login');
  }
}

// --- Axios Interceptors ---
axios.interceptors.request.use(config => {
  const token = authStore.getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
axios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401 && authStore.isAuthenticated) {
      messageStore.setFlashMessage('Session expired. Please log in again.');
      authStore.removeAuthUser();
      router.push('/login');
    }
    return Promise.reject(err);
  }
);
</script>

<template>
  <div id="app-layout">
    <!-- Navbar -->
    <nav class="navbar">
      <RouterLink :to="isAuthenticated ? '/dashboard' : '/'" class="brand">
        Finance Dashboard
      </RouterLink>

      <div class="nav-links">
        <template v-if="!isAuthenticated">
          <RouterLink to="/login" class="nav-btn">Login</RouterLink>
          <RouterLink to="/signup" class="nav-btn">Sign Up</RouterLink>
        </template>
        <template v-else>
          <span class="user-text">
            Welcome, {{ user?.username || 'User' }}
            (<RouterLink to="/dashboard" class="nav-btn subtle">Dashboard</RouterLink>)
          </span>
          <button @click="logout" class="nav-btn">Logout</button>
        </template>
      </div>
    </nav>

    <!-- Flash Message -->
    <div v-if="message" class="flash">
      {{ message }}
      <button class="close" @click="messageStore.clearFlashMessage()">×</button>
    </div>

    <!-- Main -->
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>

/* Navbar */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  border-bottom: 1px solid #dee2e6;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}

.brand {
  font-size: 1.4rem;
  font-weight: 600;
  color: #0d6efd;
  text-decoration: none;
}

/* Navbar Buttons (Text Style) */
.nav-links {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}

.nav-btn {
  background: none;
  border: none;
  color: #0d6efd;
  font-weight: 500;
  font-size: 0.95rem;
  text-decoration: none;
  cursor: pointer;
  padding: 0.4rem 0.6rem;
  transition: color 0.25s, transform 0.15s;
}

.nav-btn:hover {
  color: #0b5ed7;
  transform: translateY(-1px);
}

.nav-btn.highlight {
  color: #fff;
  background: #0d6efd;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.25s ease;
}

.nav-btn.highlight:hover {
  background: #0b5ed7;
}

.nav-btn.subtle {
  color: #495057;
}

.user-text {
  color: #343a40;
  font-size: 0.95rem;
}




</style>
