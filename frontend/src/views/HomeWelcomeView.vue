    <script setup>
    import { RouterLink } from 'vue-router';
    </script>

    <template>
      <div class="welcome-container text-center mt-5">
        <h1 class="display-4">Welcome to the Finance Dashboard</h1>
        <p class="lead">
          Analyze stock data and manage your personal watchlist.
        </p>
        <hr class="my-4">
        <p>
          Please log in to access your dashboard or sign up to create a new account.
        </p>
        <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
          <RouterLink to="/login" class="btn btn-primary btn-lg px-4 gap-3">Login</RouterLink>
          <RouterLink to="/signup" class="btn btn-outline-secondary btn-lg px-4">Sign Up</RouterLink>
        </div>
      </div>
    </template>

    <style scoped>
    .welcome-container {
      max-width: 600px;
      margin: 3rem auto; /* Added more margin */
      padding: 2rem;
      background-color: #fff; /* Optional: background for the container */
      border-radius: 8px; /* Optional: rounded corners */
      box-shadow: 0 4px 12px rgba(0,0,0,0.05); /* Optional: subtle shadow */
    }

    .lead {
      color: #6c757d; /* Softer text color */
    }

    .btn-lg {
        font-weight: 500; /* Slightly bolder button text */
    }
    </style>
    
