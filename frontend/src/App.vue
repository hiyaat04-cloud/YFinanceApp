<script setup>

// --- Imports ---
import { computed } from 'vue';
import { useRouter, RouterLink, RouterView } from 'vue-router';
import axios from 'axios'; // For setting up interceptors

// Import Pinia stores (Make sure these files exist in src/stores/)
import { useMessageStore } from './stores/message_store';
import { useAuthStore } from './stores/auth_store';

// --- Store & Router Initialization ---
const messageStore = useMessageStore();
const authStore = useAuthStore();
const router = useRouter();

// --- Reactive State from Stores ---
const message = computed(() => messageStore.getFlashMessage()); // Get flash message
const user = computed(() => authStore.getUserData()); // Get logged-in user data {username: ...}
const isAuthenticated = computed(() => authStore.isAuthenticated); // Check if user is logged in

// --- Methods ---

// Logout Function
async function logout() {
  try {
    // Optional: Call backend logout endpoint
    await fetch(`${authStore.getBackendServerURL()}/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.getToken()}`
      }
    });
    console.log("Backend logout called (optional).");

  } catch (error) {
    console.error("Backend logout API call failed (or endpoint doesn't exist):", error);
  } finally {
    // Always perform local logout
    authStore.removeAuthUser();
    messageStore.setFlashMessage("You have been logged out.");
    router.push('/login'); // Redirect to login after logout
  }
}

// --- Axios Global Configuration (Interceptors remain the same) ---
axios.interceptors.request.use(config => {
  const currentToken = authStore.getToken();
  if (currentToken) {
    config.headers.Authorization = `Bearer ${currentToken}`;
  }
  return config;
}, error => Promise.reject(error));

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401 && authStore.isAuthenticated) {
      console.warn("Unauthorized (401) request or token expired. Logging out.");
      messageStore.setFlashMessage('Session expired. Please log in again.');
      authStore.removeAuthUser();
      router.push('/login');
    }
    return Promise.reject(error);
});

</script>

<template>
  <div id="app-layout">
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg bg-white shadow-sm fixed-top border-bottom">
      <div class="container-fluid d-flex justify-content-between align-items-center px-4 py-2">
        <!-- Brand -->
        <RouterLink :to="isAuthenticated ? '/dashboard' : '/'" class="navbar-brand text-primary fw-bold fs-5">
          Finance Dashboard
        </RouterLink>

        <!-- Mobile toggler -->
        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <!-- Right section -->
        <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
          <div class="d-flex align-items-center gap-2">
            <!-- Not logged in -->
            <template v-if="!isAuthenticated">
              <RouterLink to="/login" class="btn btn-outline-primary btn-sm">Login</RouterLink>
              <RouterLink to="/signup" class="btn btn-primary btn-sm">Sign Up</RouterLink>
            </template>

            <!-- Logged in -->
            <template v-else>
              <span class="text-secondary me-2">
                Welcome, {{ user?.username || 'User' }}
                (<RouterLink to="/dashboard" class="dashboard-link">Dashboard</RouterLink>)
              </span>
              <button @click="logout" class="btn btn-outline-secondary btn-sm">Logout</button>
            </template>
          </div>
        </div>
      </div>
    </nav>

    <!-- Flash Message -->
    <div
      v-if="message"
      class="alert alert-info alert-dismissible fade show flash-message"
      role="alert"
    >
      {{ message }}
      <button
        type="button"
        class="btn-close"
        @click="messageStore.clearFlashMessage()"
        aria-label="Close"
      ></button>
    </div>

    <!-- Main Content -->
    <main class="container main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
/* --- Navbar --- */
.navbar {
  height: 60px;
}

.navbar-brand:hover {
  color: #0b5ed7 !important;
  text-decoration: none;
}

/* --- Dashboard Link --- */
.dashboard-link {
  color: #0d6efd;
  text-decoration: none;
}
.dashboard-link:hover {
  text-decoration: underline;
}

/* --- Buttons --- */
.btn {
  font-weight: 500;
  border-radius: 8px;
  padding: 0.35rem 0.75rem;
  transition: all 0.2s ease;
}

/* --- Flash Message --- */
.flash-message {
  position: fixed;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1050;
  min-width: 300px;
  max-width: 90%;
  text-align: center;
}

/* --- Main Content --- */
.main-content {
  padding-top: 100px; /* Leave space for navbar */
  padding-bottom: 2rem;
}

/* --- Background --- */
body {
  background-color: #f8f9fa;
}
</style>
