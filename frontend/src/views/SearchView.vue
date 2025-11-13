
<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth_store'
import { useMessageStore } from '@/stores/message_store'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const messageStore = useMessageStore()
const router = useRouter()

const backendURL = computed(() => authStore.getBackendServerURL())
const token = computed(() => authStore.getToken())
const userId = computed(() => authStore.getUserId())

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  if (token.value) headers['Authorization'] = `Bearer ${token.value}`
  return headers
}

// --- State ---
const searchQuery = ref('')
const analysisResults = ref(null)
const analysisNews = ref([])
const loading = ref(false)
const error = ref(null)
const watchlist = ref([])

// --- Modal State ---
const showPredictModal = ref(false)
const predictedData = ref(null)
const predictLoading = ref(false)
const predictError = ref(null)

// --- Fetch Watchlist ---
async function fetchWatchlist() {
  if (!userId.value) return
  try {
    const res = await fetch(`${backendURL.value}/api/v1/watchlist/${userId.value}`, {
      headers: getAuthHeaders()
    })
    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (err) { console.warn('Watchlist JSON parse failed:', text, err) }
    watchlist.value = data?.watchlist || []
  } catch (err) {
    console.error('❌ Fetch watchlist failed:', err)
  }
}

// --- Check if ticker exists in watchlist ---
const isTickerInWatchlist = computed(() => (ticker) =>
  watchlist.value.some(i => i.ticker === ticker.toUpperCase())
)

// --- Search & Analyze Ticker ---
async function analyzeTicker() {
  const query = searchQuery.value.trim().toUpperCase()
  if (!query) return
  loading.value = true
  error.value = null
  analysisResults.value = null
  analysisNews.value = []

  try {
    const url = `${backendURL.value}/api/v1/analyze?ticker=${query}&exchange=NS`
    const res = await fetch(url, { headers: getAuthHeaders() })
    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (err) { console.warn('Analyze JSON parse failed:', text, err) }
    if (!res.ok || !data) throw new Error(data?.message || `HTTP ${res.status}`)

    const analysis = data.analysis
    const news = data.news_headlines || []

    analysisResults.value = {
      ticker: analysis.ticker,
      company_name: analysis.company_name,
      exchange: analysis.exchange,
      last_price: analysis.last_price || 'N/A',
      previous_close: analysis.previous_close || 'N/A',
      day_high: analysis.day_high || 'N/A',
      day_low: analysis.day_low || 'N/A',
      change_percent: analysis.change_percent || 'N/A',
      volume: analysis.volume || 'N/A',
      market_cap: analysis.market_cap || 'N/A',
      sector: analysis.sector || 'N/A',
      industry: analysis.industry || 'N/A',
      summary: analysis.summary || 'No summary available.'
    }

    analysisNews.value = news
  } catch (err) {
    error.value = err.message || 'Failed to fetch analysis data.'
  } finally {
    loading.value = false
  }
}

// --- Add to Watchlist ---
async function addToWatchlist(ticker) {
  if (!userId.value) {
    messageStore.setFlashMessage('Please log in to save watchlist.')
    router.push('/login')
    return
  }

  if (isTickerInWatchlist.value(ticker)) {
    messageStore.setFlashMessage(`${ticker} already in watchlist.`)
    return
  }

  try {
    const res = await fetch(`${backendURL.value}/api/v1/watchlist/add`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'user-id': userId.value.toString() },
      body: JSON.stringify({ ticker: ticker.toUpperCase(), notes: '' })
    })
    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (err) { console.warn('Add watchlist JSON parse failed:', text, err) }
    if (!res.ok || !data) throw new Error(data?.message || 'Failed to add.')
    messageStore.setFlashMessage(`${ticker} added to watchlist.`)
    await fetchWatchlist()
  } catch (err) {
    messageStore.setFlashMessage(err.message || 'Failed to add to watchlist.')
  }
}

// --- Predict Future Price ---
async function predictFuturePrice(ticker) {
  predictLoading.value = true
  predictError.value = null
  predictedData.value = null
  showPredictModal.value = true

  try {
    const url = `${backendURL.value}/api/v1/predict?stock=${ticker.toUpperCase()}`
    const res = await fetch(url, { headers: getAuthHeaders() })
    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (err) { console.warn('Predict JSON parse failed:', text, err) }
    if (!res.ok || !data) throw new Error(data?.message || `Prediction failed. Status ${res.status}`)
    predictedData.value = data
  } catch (err) {
    predictError.value = err.message || 'Prediction failed.'
  } finally {
    predictLoading.value = false
  }
}

// --- Format Helpers ---
function formatPrice(price) {
  if (!price || price === 'N/A') return 'N/A'
  const num = Number(price)
  return isNaN(num) ? 'N/A' : `₹${num.toFixed(2)}`
}
function formatMarketCap(cap) {
  if (!cap || cap === 'N/A') return 'N/A'
  const num = Number(cap)
  return isNaN(num) ? 'N/A' : `₹${num.toLocaleString('en-IN')}`
}
function formatVolume(vol) {
  if (!vol || vol === 'N/A') return 'N/A'
  const num = Number(vol)
  return isNaN(num) ? 'N/A' : num.toLocaleString('en-IN')
}
function formatDate(dateString) {
  if (!dateString || dateString === 'N/A') return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    })
  } catch {
    return dateString.split(' ')[0]
  }
}

// --- Init ---
if (userId.value) fetchWatchlist()
</script>


<template>
  <div class="search-section">
    <h2 class="title">Stock Search & Analysis</h2>

    <form @submit.prevent="analyzeTicker" class="search-form">
      <input
        v-model.trim="searchQuery"
        type="text"
        placeholder="Enter stock ticker (e.g., TCS)"
        required
        class="search-input"
      />
      <button type="submit" class="btn-search" :disabled="loading">
        <span v-if="loading">Analyzing...</span>
        <span v-else>Analyze</span>
      </button>
    </form>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="analysisResults" class="analysis-card">
      <h3>{{ analysisResults.company_name }} ({{ analysisResults.ticker }})</h3>
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
      <p class="summary">{{ analysisResults.summary }}</p>

      <div class="button-group">
        <button
          @click="addToWatchlist(analysisResults.ticker)"
          :disabled="isTickerInWatchlist(analysisResults.ticker)"
          class="btn-add"
        >
          {{ isTickerInWatchlist(analysisResults.ticker)
            ? 'Already in Watchlist'
            : 'Add to Watchlist' }}
        </button>

        <button
          @click="predictFuturePrice(analysisResults.ticker)"
          class="btn-predict"
        >
          Predict Future Price
        </button>
      </div>

      <!-- News Section -->
      <div class="news-section" v-if="analysisNews.length > 0">
        <h4>Related News 📰</h4>
        <ul class="news-list">
          <li v-for="(news, i) in analysisNews" :key="i">
            <a :href="news.link" target="_blank">{{ news.title }}</a>
            <p class="news-meta">{{ news.source }} | {{ formatDate(news.published_at) }}</p>
          </li>
        </ul>
      </div>
    </div>

    <!-- Prediction Modal -->
    <div v-if="showPredictModal" class="modal-backdrop" @click.self="showPredictModal = false">
      <div class="modal-content">
        <h3>Predicted Future Price: {{ analysisResults?.ticker }}</h3>

        <div v-if="predictLoading">Predicting...</div>
        <div v-else-if="predictError" class="error">{{ predictError }}</div>
        <div v-else-if="predictedData">
          <p><strong>Last Price ({{ predictedData.last_date }}):</strong> {{ formatPrice(predictedData.last_price) }}</p>
          <p><strong>Day 7 ({{ predictedData.day_7.date }}):</strong> {{ formatPrice(predictedData.day_7.price) }}</p>
          <p><strong>Day 14 ({{ predictedData.day_14.date }}):</strong> {{ formatPrice(predictedData.day_14.price) }}</p>
        </div>

        <button @click="showPredictModal = false" class="btn-close">Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-section {
  padding: 1.5rem;
  margin-top: 1.5rem;
  background: #f9fafb;
  border-radius: 1rem;
}
.title {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 1rem;
}
.search-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.search-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
}
.btn-search {
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.6rem 1rem;
}
.analysis-card {
  background: white;
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
}
.news-section {
  margin-top: 1rem;
}
.news-list {
  list-style: none;
  padding: 0;
}
.news-list li {
  margin-bottom: 0.5rem;
}
.news-meta {
  font-size: 0.8rem;
  color: #94a3b8;
}
.error {
  color: #ef4444;
}
.button-group {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.btn-add {
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
}
.btn-predict {
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}
.modal-content {
  background: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  width: 300px;
  max-width: 90%;
}
.btn-close {
  margin-top: 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
}
</style>
