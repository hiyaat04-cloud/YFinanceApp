<script setup>
import { RouterLink } from 'vue-router';
</script>

<template>
  <div class="welcome-container">
    <h1>Welcome to the Finance Dashboard</h1>
    <p class="subtitle">Analyze stock data and manage your personal watchlist.</p>
    <hr />
    <p>Please log in to access your dashboard or sign up to create a new account.</p>
    <div class="action-buttons">
      <RouterLink to="/login" class="btn primary">Login</RouterLink>
      <RouterLink to="/signup" class="btn secondary">Sign Up</RouterLink>
    </div>
  </div>
</template>

<style scoped>

</style>
