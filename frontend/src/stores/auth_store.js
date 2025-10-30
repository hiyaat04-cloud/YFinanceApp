import { ref, computed } from 'vue';
import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', () => {
    // Backend URL (remains the same)
    const backend_server = 'http://127.0.0.1:5001'; // Ensure this port matches your running backend

    // --- State: Initialize from sessionStorage ---
    const token = ref(sessionStorage.getItem('auth_token') || null);
    // Parse user data safely, defaulting to null if not found or invalid JSON
    const logged_user = ref(JSON.parse(sessionStorage.getItem('user_data') || 'null'));

    // --- Getters (Computed Properties) ---
    const isAuthenticated = computed(() => {
        // Check if token exists and potentially add a check for expiration if needed
        return token.value !== null;
    });

    // --- Actions ---
    function getToken() {
        return token.value;
    }

    function setToken(new_token) {
        token.value = new_token;
        // --- Use sessionStorage ---
        if (new_token) {
            sessionStorage.setItem('auth_token', new_token);
        } else {
            sessionStorage.removeItem('auth_token'); // Remove if null
        }
    }

    function setUserData(new_user_data) {
        logged_user.value = new_user_data;
        // --- Use sessionStorage ---
        if (new_user_data) {
            sessionStorage.setItem('user_data', JSON.stringify(new_user_data));
        } else {
            sessionStorage.removeItem('user_data'); // Remove if null
        }
    }

    function removeAuthUser() {
        token.value = null;
        logged_user.value = null;
        // --- Use sessionStorage ---
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('user_data');
    }

    function getUserData() {
        // Return the reactive ref's value
        return logged_user.value;
    }
    function getUserId() {
        return logged_user.value?.id || null;
    }

    function getBackendServerURL() {
        return backend_server;
    }

    // --- Exposed Actions & Getters ---
    return {
        getBackendServerURL,
        getToken,
        isAuthenticated, // Expose the computed property directly
        getUserData,
        getUserId,
        setUserData,
        setToken,
        removeAuthUser
    };
});

