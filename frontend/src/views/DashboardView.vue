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
const backendURL = computed(() => authStore.getBackendServerURL());
const token = computed(() => authStore.getToken());
const userId = computed(() => authStore.getUserId());

// --- Analyzer State ---
const tickerInput = ref('');
const analysisResults = ref(null);
const analysisNews = ref([]);     // State for news headlines
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
  analysisNews.value = []; // Reset news state
  analysisError.value = null;

  const tickerToAnalyze = tickerInput.value.toUpperCase();
  const exchangeToQuery = 'NS';

  try {
    const url = `${backendURL.value}/api/v1/analyze?ticker=${tickerToAnalyze}&exchange=${exchangeToQuery}`;
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
    
    // --- Destructure the payload into analysis and news ---
    const analysis = data.analysis;
    const news = data.news_headlines || [];

    analysisResults.value = {
      ticker: analysis.ticker,
      company_name: analysis.company_name,
      exchange: analysis.exchange,
      last_price: analysis.last_price || 'N/A',
      previous_close: analysis.previous_close || 'N/A',
      open_price: analysis.open_price || 'N/A',
      day_high: analysis.day_high || 'N/A',
      day_low: analysis.day_low || 'N/A',
      volume: analysis.volume || 'N/A',
      change_percent: analysis.change_percent || 'N/A',
      market_cap: analysis.market_cap || 'N/A',
      sector: analysis.sector || 'N/A',
      industry: analysis.industry || 'N/A',
      employees: analysis.employees || 'N/A',
      summary: analysis.summary || 'No summary available.',
    };
    
    // Update news results state
    analysisNews.value = news;

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
    const checkUrl = `${backendURL.value}/api/v1/has_watchlist/${currentUserId}`;
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

    const fetchUrl = `${backendURL.value}/api/v1/watchlist/${currentUserId}`;
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
    const url = `${backendURL.value}/api/v1/watchlist/add`;

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
    const url = `${backendURL.value}/api/v1/watchlist/${itemId}`;
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
function formatDate(dateString) {
    if (!dateString || dateString === 'N/A' || dateString.includes('Failed')) return 'N/A';
    // dateString format from backend is 'YYYY-MM-DD HH:MM:SS'
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
    } catch {
        return dateString.split(' ')[0]; // Fallback to just date part
    }
}
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-grid">
      <section class="analyzer">
        <h3 class="section-title">Stock Analyzer</h3>
        <form @submit.prevent="getAnalysis" class="analyzer-form">
          <input
            v-model.trim="tickerInput"
            type="text"
            placeholder="Enter Ticker (e.g., TCS)"
            class="ticker-input"
            required
          />
          <button type="submit" class="btn-analyze" :disabled="analysisLoading">
            <span v-if="analysisLoading" class="spinner-border spinner-border-sm"></span>
            <span v-else>Analyze</span>
          </button>
        </form>

        <div v-if="analysisLoading" class="loading">
          <div class="spinner-border text-primary"></div>
        </div>
        <div v-else-if="analysisError" class="alert alert-danger">{{ analysisError }}</div>

        <div v-else-if="analysisResults" class="analysis-result">
          <h5>{{ analysisResults.company_name }} ({{ analysisResults.ticker }})</h5>
          <p><strong>Exchange:</strong> {{ analysisResults.exchange }}</p>
          <p><strong>Current Price:</strong> {{ formatPrice(analysisResults.last_price) }}</p>
          <p><strong>Change:</strong> {{ analysisResults.change_percent }}%</p>
          <p><strong>Volume:</strong> {{ formatVolume(analysisResults.volume) }}</p>
          <hr />
          <p><strong>Market Cap:</strong> {{ formatMarketCap(analysisResults.market_cap) }}</p>
          <p><strong>Range:</strong> {{ formatPrice(analysisResults.day_low) }} - {{ formatPrice(analysisResults.day_high) }}</p>
          <p><strong>Prev. Close:</strong> {{ formatPrice(analysisResults.previous_close) }}</p>
          <p><strong>Sector:</strong> {{ analysisResults.sector }}</p>
          <p><strong>Industry:</strong> {{ analysisResults.industry }}</p>
          <p class="summary">{{ analysisResults.summary.substring(0, 120) + '...' }}</p>

          <div class="news-section">
            <h6 class="news-title">Latest News 📰</h6>
            <ul v-if="analysisNews.length > 0 && !analysisNews[0].message" class="news-list">
              <li v-for="(news, index) in analysisNews" :key="index" class="news-item">
                <a :href="news.link" target="_blank" rel="noopener noreferrer" class="news-link">
                  {{ news.title }}
                </a>
                <p class="news-meta">
                  <span class="news-source">{{ news.source }}</span>
                  <span class="news-separator">|</span>
                  <span class="news-date">{{ formatDate(news.published_at) }}</span>
                </p>
              </li>
            </ul>
            <p v-else class="empty-news">
                {{ analysisNews.length > 0 && analysisNews[0].message ? analysisNews[0].message : 'No recent news found for this ticker.' }}
            </p>
          </div>
          <button
            @click="addToWatchlist(analysisResults.ticker)"
            :disabled="isTickerInWatchlist(analysisResults.ticker)"
            class="btn-add"
          >
            {{ isTickerInWatchlist(analysisResults.ticker)
              ? 'Already in Watchlist'
              : 'Add to Watchlist' }}
          </button>
        </div>
      </section>

      <section class="watchlist">
        <h3 class="section-title">My Watchlist</h3>
        <div v-if="watchlistLoading" class="loading">
          <div class="spinner-border text-secondary"></div>
        </div>
        <div v-else-if="watchlistError" class="alert alert-warning">{{ watchlistError }}</div>
        <div v-else-if="watchlist.length === 0" class="empty">
          Your watchlist is empty.
        </div>

        <ul v-else class="watchlist-list">
          <li v-for="item in watchlist" :key="item.id" class="watchlist-item">
            <span>{{ item.ticker }}</span>
            <button
              @click="deleteFromWatchlist(item.id, item.ticker)"
              class="btn-delete"
              title="Remove"
            >
              ×
            </button>
          </li>
          <li v-if="!analysisResults && watchlist.length > 0" class="watchlist-hint">
            Select a ticker to analyze.
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* All styles remain the same, just included here for completeness */
.dashboard {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 2rem;
  background-color: #f9fafb;
  height: 100vh;
  overflow: hidden;
}

.dashboard-grid {
  display: flex;
  gap: 2rem;
  width: 100%;
  max-width: 1100px;
  height: 90%;
  overflow: hidden;
}

/* Panels */
.analyzer,
.watchlist {
  flex: 1;
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  overflow-y: auto;
}

/* Keep scroll inside cards neat */
.analyzer::-webkit-scrollbar,
.watchlist::-webkit-scrollbar {
  width: 6px;
}
.analyzer::-webkit-scrollbar-thumb,
.watchlist::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

/* Rest of previous styles stay same */
.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.5rem;
}

.analyzer-form {
  display: flex;
  gap: 0.5rem;
}

.ticker-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}
.ticker-input:focus {
  border-color: #3b82f6;
  outline: none;
}

.btn-analyze {
  background-color: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  padding: 0.55rem 1.1rem;
  font-weight: 500;
  transition: background 0.2s ease;
}
.btn-analyze:hover {
  background-color: #2563eb;
}

.analysis-result {
  margin-top: 1.2rem;
  font-size: 0.9rem;
  color: #334155;
}
.analysis-result h5 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.6rem;
}

.summary {
  color: #64748b;
  margin-top: 0.5rem;
}

.btn-add {
  margin-top: 0.8rem;
  background-color: #10b981;
  border: none;
  color: #fff;
  font-size: 0.85rem;
  border-radius: 0.5rem;
  padding: 0.45rem 1rem;
}
.btn-add:hover {
  background-color: #059669;
}

/* Watchlist */
.watchlist-list {
  list-style: none;
  padding: 0;
  margin-top: 1rem;
}
.watchlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 0.8rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.9rem;
}
.watchlist-hint {
    font-size: 0.8rem;
    color: #94a3b8;
    text-align: center;
    padding: 1rem 0;
    font-style: italic;
}
.btn-delete {
  background: none;
  border: none;
  color: #ef4444;
  font-size: 1rem;
  cursor: pointer;
}
.btn-delete:hover {
  color: #dc2626;
}
.empty {
  font-size: 0.9rem;
  color: #64748b;
  text-align: center;
  padding: 1rem 0;
}
.loading {
  text-align: center;
  padding: 1rem 0;
}

/* --- News Styling --- */
.news-section {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px dashed #e2e8f0;
}

.news-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0.8rem;
}

.news-list {
    list-style: none;
    padding: 0;
}

.news-item {
    margin-bottom: 1rem;
}

.news-link {
    font-size: 0.9rem;
    color: #3b82f6;
    text-decoration: none;
    font-weight: 500;
    line-height: 1.3;
    display: block;
}
.news-link:hover {
    text-decoration: underline;
    color: #2563eb;
}

.news-meta {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 0.2rem;
}

.news-separator {
    margin: 0 0.3rem;
}

.empty-news {
    font-size: 0.85rem;
    color: #64748b;
    font-style: italic;
}
</style>