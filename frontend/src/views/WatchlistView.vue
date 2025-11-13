<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth_store'
import { useMessageStore } from '@/stores/message_store'

// --- Initialize Stores ---
const authStore = useAuthStore()
const messageStore = useMessageStore()

// --- Reactive State ---
const watchlist = ref([])
const watchlistLoading = ref(false)
const watchlistError = ref(null)

// Monte Carlo modal state
const showMonteCarloModal = ref(false)
const monteCarloData = ref(null)
const monteLoading = ref(false)
const monteError = ref(null)

// --- Computed Properties ---
const backendURL = computed(() => authStore.getBackendServerURL())
const token = computed(() => authStore.getToken())
const userId = computed(() => authStore.getUserId())

// --- Helper Functions ---
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  if (token.value) headers['Authorization'] = `Bearer ${token.value}`
  return headers
}

// --- Fetch Watchlist ---
async function fetchWatchlist() {
  if (!userId.value) return
  watchlistLoading.value = true
  watchlistError.value = null

  try {
    const url = `${backendURL.value}/api/v1/watchlist/${userId.value}`
    const res = await fetch(url, { headers: getAuthHeaders() })

    if (!res.ok) throw new Error('Failed to fetch watchlist')

    const data = await res.json()
    watchlist.value = data.watchlist || []
  } catch (err) {
    watchlistError.value = err.message
    messageStore.setFlashMessage(`Error: ${err.message}`)
  } finally {
    watchlistLoading.value = false
  }
}

// --- Delete from Watchlist ---
async function deleteFromWatchlist(id, ticker) {
  try {
    const url = `${backendURL.value}/api/v1/watchlist/${id}`
    const res = await fetch(url, { method: 'DELETE', headers: getAuthHeaders() })

    if (!res.ok) throw new Error(`Failed to delete ${ticker}`)

    watchlist.value = watchlist.value.filter(i => i.id !== id)
    messageStore.setFlashMessage(`Removed ${ticker} from watchlist`)
  } catch (err) {
    messageStore.setFlashMessage(`Error: ${err.message}`)
  }
}

// --- Monte Carlo Prediction ---
async function predictMonteCarlo() {
  if (!watchlist.value.length) return

  monteLoading.value = true
  monteError.value = null
  monteCarloData.value = null
  showMonteCarloModal.value = true

  try {
    const stocks = watchlist.value.map(s => s.ticker)

    const res = await fetch(`${backendURL.value}/api/v1/montecarlo`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ stocks })
    })

    const data = await res.json()
    if (!res.ok || data.error) throw new Error(data.error || 'Monte Carlo simulation failed')

    // Map API keys to template-friendly keys
    monteCarloData.value = {
      stocks: data.stocks || stocks,
      expected_return: Number(data.expected_return_percent ?? 0),
      volatility: Number(data.volatility_percent ?? 0),
      worst_5_percent: Number(data.worst_5_percent_percent ?? 0),
      conclusion: data.conclusion || 'No conclusion'
    }

    console.log('Monte Carlo Data:', monteCarloData.value)
  } catch (err) {
    monteError.value = err.message || 'Monte Carlo simulation failed'
  } finally {
    monteLoading.value = false
  }
}

// --- Watch userId changes ---
watch(userId, (id) => {
  if (id) fetchWatchlist()
}, { immediate: true })
</script>

<template>
  <div class="watchlist-view">
    <h2>My Watchlist</h2>

    <div v-if="watchlistLoading">Loading...</div>
    <div v-else-if="watchlistError" class="error">{{ watchlistError }}</div>
    <div v-else-if="!watchlist.length" class="empty">No items in watchlist.</div>

    <ul v-else class="list">
      <li v-for="item in watchlist" :key="item.id">
        {{ item.ticker }}
        <button @click="deleteFromWatchlist(item.id, item.ticker)">×</button>
      </li>
    </ul>

    <!-- Monte Carlo Button -->
    <button
      v-if="watchlist.length > 0"
      @click="predictMonteCarlo"
      class="btn-montecarlo"
    >
      Monte Carlo Portfolio Simulation
    </button>

    <!-- Monte Carlo Modal -->
    <div
      v-if="showMonteCarloModal"
      class="modal-backdrop"
      @click.self="showMonteCarloModal = false"
    >
      <div class="modal-content">
        <h3>Monte Carlo Portfolio Simulation</h3>

        <div v-if="monteLoading">Simulating...</div>
        <div v-else-if="monteError" class="error">{{ monteError }}</div>
        <div v-else-if="monteCarloData">
          <p><strong>Stocks:</strong> {{ monteCarloData.stocks.join(', ') }}</p>
          <p><strong>Expected Return:</strong> {{ monteCarloData.expected_return }}%</p>
          <p><strong>Volatility:</strong> {{ monteCarloData.volatility }}%</p>
          <p><strong>Worst 5%:</strong> {{ monteCarloData.worst_5_percent }}%</p>
          <p><strong>Conclusion:</strong> {{ monteCarloData.conclusion }}</p>
        </div>

        <button @click="showMonteCarloModal = false" class="btn-close">Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.watchlist-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.list li {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.list button {
  border: none;
  background: none;
  color: #ef4444;
  font-size: 1.1rem;
  cursor: pointer;
}

.btn-montecarlo {
  margin-top: 1rem;
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
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
  width: 350px;
  max-width: 90%;
}

.btn-close {
  margin-top: 1rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.error {
  color: #ef4444;
}
</style>
