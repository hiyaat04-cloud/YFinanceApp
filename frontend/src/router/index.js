import { createRouter, createWebHistory } from 'vue-router';
// Import the components needed
import HomeWelcomeView from '../views/HomeWelcomeView.vue';
import LoginView from '../views/LoginView.vue';
import SignupView from '../views/SignupView.vue'; // Import SignupView
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL), // Use process.env for Vue CLI
  routes: [
    // --- Routes ---
    {
      // Keep the root path '/' showing the HomeWelcomeView
      path: '/',
      name: 'home',
      component: HomeWelcomeView,
    },
    {
      // Add the route for the login page
      path: '/login',
      name: 'login',
      component: LoginView, // Point this path to the LoginView component
    },
    {
      // Add the route for the signup page
      path: '/signup',
      name: 'signup',
      component: SignupView, // Point this path to the SignupView component
    },
     {
      // Add the route for the signup page
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView, // Point this path to the SignupView component
    }
    // You can add the protected DashboardView route here later
  ]
  // Removed global navigation guard for simplicity for now
});

export default router;

