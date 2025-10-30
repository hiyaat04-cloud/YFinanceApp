<script setup>
import { ref } from 'vue';
import { useMessageStore } from '@/stores/message_store';
import { useAuthStore } from '@/stores/auth_store'; // To get backend URL
import { useRouter, RouterLink } from 'vue-router';
import axios from 'axios'; // Import axios

const router = useRouter();
const username = ref('');
const email = ref(''); // Keep email ref
const password = ref('');
const confirm_password = ref('');
const isLoading = ref(false);

// Stores
const messageStore = useMessageStore();
const authStore = useAuthStore();
// Use the correct getter name based on your auth_store.js
const backendURL = authStore.getBackendServerURL();

// --- Input Validation ---
// Simplified validation for basic user signup
function validateInput() {
  // Check if passwords match
  if (password.value !== confirm_password.value) {
    messageStore.setFlashMessage('Password and Confirm Password do not match.');
    return false;
  }
  // Check required fields
  if (!username.value || !email.value || !password.value) {
      messageStore.setFlashMessage('Username, Email, and Password cannot be empty.');
      return false;
  }
  // Basic email format check
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.value)) {
        messageStore.setFlashMessage('Please enter a valid email address.');
        return false;
    }
  // Check password length
  if (password.value.length < 8) { // Keep min length check
      messageStore.setFlashMessage('Password must be at least 8 characters long.');
      return false;
  }
  return true; // All checks passed
}

// --- API Call for Registration ---
// Simplified API call, ensure backend expects only username, email, password
async function registerUser(userData) {
  isLoading.value = true;
  messageStore.setFlashMessage(''); // Clear previous messages
  try {
    // Make sure the endpoint matches your backend route in main.py (e.g., /api/v1/signup)
    const response = await axios.post(`${backendURL}/api/v1/signup`, userData, {
       headers: { 'Content-Type': 'application/json' }
    });
    // Assuming backend returns { "message": "..." } on success (201 Created)
    return { status: true, message: response.data.message || 'Signup successful!' };
  } catch (error) {
    console.error('Signup Error:', error.response || error);
    // Use error message from backend if available, otherwise generic message
    const errorMessage = error.response?.data?.message || error.response?.data?.error || 'Signup failed. Please try again.';
    return { status: false, message: errorMessage };
  } finally {
      isLoading.value = false;
  }
}

// --- Form Submission Handler ---
// Simplified onSubmit
async function onSubmit() {
  if (validateInput()) {
    // Prepare simplified data payload
    const data = {
      username: username.value,
      email: email.value,
      password: password.value,
      // No role, address, or professional details needed
    };

    const result = await registerUser(data);
    messageStore.setFlashMessage(result.message); // Show success or error message

    if (result.status) {
      // Redirect to login page after successful registration
      router.push({ path: '/login' });
    }
  }
}

</script>

<template>
  <div class="auth-page">
    <div class="auth-container container mt-4 p-4 p-md-5">
      <h1 class="text-center mb-4 auth-title">Create Account</h1>
      <div class="row justify-content-center">
        <div class="col-lg-8 col-md-10">
          <form @submit.prevent="onSubmit" class="auth-form">

            <!-- Username Input -->
            <div class="mb-3">
              <label for="username" class="form-label">Username</label>
              <input
                type="text"
                class="form-control form-control-lg"
                id="username"
                v-model="username"
                required
                placeholder="Choose a username"
              />
               <div id="usernameHelp" class="form-text mt-1">This will be used for login.</div>
            </div>

            <!-- Email Input -->
            <div class="mb-3">
              <label for="email" class="form-label">Email Address</label>
              <input
                type="email"
                class="form-control form-control-lg"
                id="email"
                v-model="email"
                required
                aria-describedby="emailHelp"
                placeholder="your.email@example.com"
              />
              <div id="emailHelp" class="form-text mt-1">Optional, for notifications or recovery.</div>
              <!-- Removed email availability check display -->
            </div>

            <!-- Password Inputs -->
            <div class="row g-3 mb-3">
              <div class="col-md-6">
                <label for="password" class="form-label">Password</label>
                <input
                  type="password"
                  class="form-control form-control-lg"
                  id="password"
                  v-model="password"
                  required
                  placeholder="Min. 8 characters"
                />
              </div>
              <div class="col-md-6">
                <label for="confirmPassword" class="form-label">Confirm Password</label>
                <input
                  type="password"
                  class="form-control form-control-lg"
                  id="confirmPassword"
                  v-model="confirm_password"
                  required
                  placeholder="Re-enter password"
                />
              </div>
            </div>

            <!-- Removed Address Button & Summary -->
            <!-- Removed Role Selection -->

            <!-- Submit Button -->
            <div class="d-grid gap-2 mb-3 mt-4">
              <button type="submit" class="btn btn-primary btn-lg auth-button" :disabled="isLoading">
                <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                {{ isLoading ? ' Registering...' : 'Sign Up' }}
              </button>
            </div>

            <!-- Link to Login -->
            <div class="text-center mt-4">
              <span class="login-prompt">Already have an account? </span>
              <RouterLink to="/login" class="login-link">Login Here</RouterLink>
            </div>
          </form>
        </div>
      </div>
    </div>
    <!-- Removed Modals -->
  </div>
</template>

<style scoped>
/* Scoped styles remain the same - focused on form appearance */

/* Define color variables (adjust as needed) */
:root {
  --primary-color-auth: #0056b3; /* A deeper blue */
  --primary-hover-auth: #004494;
  --secondary-text-auth: #6c757d;
  --border-color-auth: #ced4da;
  --background-color-auth: #f8f9fa; /* Light grey background */
  --card-background-auth: #ffffff;
  --box-shadow-auth: 0 6px 18px rgba(0, 0, 0, 0.08); /* Softer shadow */
}

.auth-page {
  background-color: var(--background-color-auth);
  min-height: calc(100vh - 80px); /* Adjust based on navbar height */
  display: flex;
  align-items: center; /* Vertically center the card */
  padding: 2rem 0; /* Add some top/bottom padding */
}

.auth-container {
  max-width: 650px; /* Slightly wider card */
  margin: auto; /* Center horizontally */
  background-color: var(--card-background-auth);
  border-radius: 12px; /* More rounded corners */
  box-shadow: var(--box-shadow-auth);
  border: 1px solid #e9ecef; /* Subtle border */
}

.auth-title {
  color: #343a40; /* Darker heading */
  font-weight: 600; /* Slightly bolder */
  margin-bottom: 2rem !important; /* Increase space below title */
}

.auth-form label {
  font-weight: 500;
  margin-bottom: 0.5rem; /* Space between label and input */
  color: #495057; /* Slightly darker label text */
}

.form-control-lg {
  padding: 0.9rem 1.1rem; /* More padding in inputs */
  font-size: 1rem; /* Adjust font size if needed */
  border-radius: 6px; /* Slightly rounded inputs */
  border-color: var(--border-color-auth);
  transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.form-control-lg:focus {
  border-color: var(--primary-color-auth);
  box-shadow: 0 0 0 0.2rem rgba(0, 86, 179, 0.25); /* Focus ring */
}

.form-text {
  font-size: 0.8rem; /* Smaller help text */
  color: var(--secondary-text-auth);
}

.auth-button {
  background-color: var(--primary-color-auth);
  border-color: var(--primary-color-auth);
  padding: 0.9rem 1.25rem;
  font-size: 1.1rem;
  font-weight: 500;
  border-radius: 6px;
  transition: background-color 0.2s ease-in-out, border-color 0.2s ease-in-out;
  display: flex; /* For spinner alignment */
  align-items: center;
  justify-content: center;
}
.auth-button .spinner-border {
  margin-right: 0.5rem; /* Space between spinner and text */
}


.auth-button:disabled {
  background-color: #6c757d;
  border-color: #6c757d;
}

.auth-button:not(:disabled):hover {
  background-color: var(--primary-hover-auth);
  border-color: var(--primary-hover-auth);
}

.login-prompt {
   color: var(--secondary-text-auth);
}

.login-link {
  color: var(--primary-color-auth);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease-in-out;
}

.login-link:hover {
  color: var(--primary-hover-auth);
  text-decoration: underline;
}

/* Adjust row spacing if using g-3 */
.row.g-3 {
  --bs-gutter-x: 1.5rem; /* Ensure consistent spacing */
}
</style>

