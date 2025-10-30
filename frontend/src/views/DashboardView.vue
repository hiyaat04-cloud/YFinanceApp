<script setup>
import { ref, computed, watch } from 'vue';
import { useAuthStore } from '@/stores/auth_store';
import { useMessageStore } from '@/stores/message_store';
import { useRouter } from 'vue-router';

// --- Stores & Router ---
const authStore = useAuthStore();
const messageStore = useMessageStore();
const router = useRouter();

// --- Backend Config ---
const backendURL = authStore.getBackendServerURL();
const token = computed(() => authStore.getToken());
const userId = computed(() => authStore.getUserId());

// --- Analyzer State ---
const tickerInput = ref('');
const analysisResults = ref(null);
const analysisLoading = ref(false);
const analysisError = ref(null);

// --- Watchlist State ---
const watchlist = ref([]);
const watchlistLoading = ref(false);
const watchlistError = ref(null);

// --- Helper: Auth Headers ---
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const currentToken = token.value;
  if (currentToken) headers['Authorization'] = `Bearer ${currentToken}`;
  return headers;
}

// --- Computed: Check if Ticker in Watchlist ---
const isTickerInWatchlist = computed(() => {
  return (ticker) => {
    if (!ticker) return false;
    return watchlist.value.some(item => item.ticker === ticker.toUpperCase());
  };
});

// --- ✅ API: Get Stock Analysis ---
async function getAnalysis() {
  if (!tickerInput.value) return;

  analysisLoading.value = true;
  analysisResults.value = null;
  analysisError.value = null;

  const tickerToAnalyze = tickerInput.value.toUpperCase();
  const exchangeToQuery = 'NS';

  try {
    const url = `${backendURL}/api/v1/analyze?ticker=${tickerToAnalyze}&exchange=${exchangeToQuery}`;
    console.log(`🔍 Fetching analysis from: ${url}`);

    const response = await fetch(url);
    if (!response.ok) {
      const data = await response.text();
      if (data.startsWith('<!doctype'))
        throw new Error(`Route Not Found or Internal Server Error. Check '/api/v1/analyze'.`);
      try {
        const errorData = JSON.parse(data);
        throw new Error(errorData.message || `HTTP ${response.status}`);
      } catch {
        throw new Error(`HTTP error! Status: ${response.status}.`);
      }
    }

    const data = await response.json();
    analysisResults.value = {
      ticker: data.ticker,
      company_name: data.company_name,
      exchange: data.exchange,
      last_price: data.last_price || 'N/A',
      previous_close: data.previous_close || 'N/A',
      open_price: data.open_price || 'N/A',
      day_high: data.day_high || 'N/A',
      day_low: data.day_low || 'N/A',
      volume: data.volume || 'N/A',
      change_percent: data.change_percent || 'N/A',
      market_cap: data.market_cap || 'N/A',
      sector: data.sector || 'N/A',
      industry: data.industry || 'N/A',
      employees: data.employees || 'N/A',
      summary: data.summary || 'No summary available.',
    };
  } catch (err) {
    analysisError.value = err.message || 'Ticker not found or external data unavailable.';
    console.error('❌ Analysis Fetch Error:', err);
  } finally {
    analysisLoading.value = false;
  }
}

// --- ✅ API: Fetch Watchlist ---
async function fetchWatchlist() {
  if (!userId.value) {
    watchlistError.value = 'User not authenticated.';
    return;
  }

  watchlistLoading.value = true;
  watchlistError.value = null;
  const currentUserId = userId.value;

  try {
    const checkUrl = `${backendURL}/api/v1/has_watchlist/${currentUserId}`;
    let response = await fetch(checkUrl, { headers: getAuthHeaders() });
    let data = await response.json();

    if (!response.ok) {
      if (response.status === 401) {
        messageStore.setFlashMessage('Session expired. Please log in again.');
        authStore.removeAuthUser();
        router.push('/login');
        return;
      }
      throw new Error(data.error || data.message);
    }

    if (!data.has_watchlist_records) {
      watchlist.value = [];
      watchlistLoading.value = false;
      return;
    }

    const fetchUrl = `${backendURL}/api/v1/watchlist/${currentUserId}`;
    response = await fetch(fetchUrl, { headers: getAuthHeaders() });
    data = await response.json();

    if (!response.ok) throw new Error(data.error || data.message);
    watchlist.value = data.watchlist || [];
  } catch (err) {
    watchlistError.value = err.message || 'Failed to load watchlist.';
    console.error('❌ Fetch Watchlist Error:', err);
  } finally {
    watchlistLoading.value = false;
  }
}

async function addToWatchlist(ticker) {
  if (!ticker || isTickerInWatchlist.value(ticker)) return;

  const tickerUpper = ticker.toUpperCase();
  try {
    const url = `${backendURL}/api/v1/watchlist/add`;

    // 🧠 Ensure userId.value is valid before sending
    if (!userId.value || isNaN(Number(userId.value))) {
      throw new Error(`Invalid User ID: ${userId.value}`);
    }

    const headers = getAuthHeaders();
    headers['user-id'] = userId.value.toString(); // ✅ send as header string
    headers['Content-Type'] = 'application/json';
    console.log("User ID before fetch:", userId.value);
    console.log(headers['user-id']);

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        ticker: tickerUpper,
        notes: "",
      }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);

    messageStore.setFlashMessage(`${tickerUpper} added to watchlist.`);
    await fetchWatchlist();
  } catch (err) {
    messageStore.setFlashMessage(err.message || 'Failed to add item.');
    console.error('Add Watchlist Error:', err);
  }
}


// 
async function deleteFromWatchlist(itemId, itemTicker) {
  const originalWatchlist = [...watchlist.value];
  watchlist.value = watchlist.value.filter(item => item.id !== itemId);

  try {
    const url = `${backendURL}/api/v1/watchlist/${itemId}`;
    const response = await fetch(url, { method: 'DELETE', headers: getAuthHeaders() });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.error || `HTTP ${response.status}`);
    }
    messageStore.setFlashMessage(`${itemTicker} removed from watchlist.`);
  } catch (err) {
    watchlist.value = originalWatchlist;
    messageStore.setFlashMessage(err.message || 'Failed to remove from watchlist.');
    console.error(' Delete Watchlist Error:', err);
  }
}

// --- Auto-fetch Watchlist on Login ---
watch(userId, (newUserId) => {
  if (newUserId) fetchWatchlist();
}, { immediate: true });

// --- Format Helpers ---
function formatPrice(price) {
  if (!price || price === 'N/A') return 'N/A';
  const num = Number(price);
  return isNaN(num) ? 'N/A' : `₹${num.toFixed(2)}`;
}
function formatMarketCap(cap) {
  if (!cap || cap === 'N/A') return 'N/A';
  const num = Number(cap);
  return isNaN(num) ? 'N/A' : `₹${num.toLocaleString('en-IN')}`;
}
function formatVolume(vol) {
  if (!vol || vol === 'N/A') return 'N/A';
  const num = Number(vol);
  return isNaN(num) ? 'N/A' : num.toLocaleString('en-IN');
}
</script>

<template>
<div class="dashboard-container">
  <h2 class="text-center mb-4">Your Dashboard</h2>
  <div class="container dashboard-grid">

    <!-- Stock Analyzer -->
    <section class="column analyzer-column card shadow-sm">
      <div class="card-body">
        <h3 class="card-title h5">Stock Analyzer</h3>

        <form @submit.prevent="getAnalysis" class="analyzer-form mb-3">
          <div class="input-group">
            <input
              type="text"
              class="form-control form-control-lg"
              v-model.trim="tickerInput"
              placeholder="Enter Ticker (e.g., TCS)"
              required
            />
            <button type="submit" class="btn btn-primary" :disabled="analysisLoading">
              <span v-if="analysisLoading" class="spinner-border spinner-border-sm"></span>
              <span v-else>Analyze</span>
            </button>
          </div>
        </form>

        <div v-if="analysisLoading" class="text-center p-3">
          <div class="spinner-border text-primary"></div>
        </div>
        <div v-else-if="analysisError" class="alert alert-danger">{{ analysisError }}</div>
        <div v-else-if="analysisResults" class="card mt-3 bg-light">
          <div class="card-body">
            <h5>{{ analysisResults.company_name }} ({{ analysisResults.ticker }})</h5>
            <p><strong>Exchange:</strong> {{ analysisResults.exchange }}</p>
            <p><strong>Current Price:</strong> {{ formatPrice(analysisResults.last_price) }}</p>
            <p><strong>Change (%):</strong> {{ analysisResults.change_percent }}%</p>
            <p><strong>Volume:</strong> {{ formatVolume(analysisResults.volume) }}</p>
            <hr>
            <p><strong>Market Cap:</strong> {{ formatMarketCap(analysisResults.market_cap) }}</p>
            <p><strong>Today's Range:</strong> {{ formatPrice(analysisResults.day_low) }} - {{ formatPrice(analysisResults.day_high) }}</p>
            <p><strong>Prev. Close:</strong> {{ formatPrice(analysisResults.previous_close) }}</p>
            <p><strong>Sector:</strong> {{ analysisResults.sector }}</p>
            <p><strong>Industry:</strong> {{ analysisResults.industry }}</p>
            <p class="text-muted small">{{ analysisResults.summary.substring(0, 150) + '...' }}</p>

            <button
              @click="addToWatchlist(analysisResults.ticker)"
              :disabled="isTickerInWatchlist(analysisResults.ticker)"
              class="btn btn-success btn-sm mt-2"
            >
              {{ isTickerInWatchlist(analysisResults.ticker) ? 'Already in Watchlist' : 'Add to Watchlist' }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Watchlist -->
    <section class="column watchlist-column card shadow-sm">
      <div class="card-body">
        <h3 class="card-title h5">My Watchlist</h3>
        <div v-if="watchlistLoading" class="text-center p-3">
          <div class="spinner-border text-secondary"></div>
        </div>
        <div v-else-if="watchlistError" class="alert alert-warning">{{ watchlistError }}</div>
        <div v-else-if="watchlist.length === 0" class="text-muted border p-3 rounded">
          Your watchlist is empty. Use the analyzer to add stocks.
        </div>
        <ul v-else class="list-group list-group-flush">
          <li v-for="item in watchlist" :key="item.id" class="list-group-item d-flex justify-content-between align-items-center">
            <strong>{{ item.ticker }}</strong>
            <button @click="deleteFromWatchlist(item.id, item.ticker)" class="btn btn-outline-danger btn-sm">&times;</button>
          </li>
        </ul>
      </div>
    </section>

  </div>
</div>
</template>

<style scoped>
.dashboard-container {
  padding-top: 1rem;
}
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}
.add-watchlist-btn:disabled {
  opacity: 0.65;
}
</style>
