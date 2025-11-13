<script setup>
import { ref } from 'vue'
import SearchView from './SearchView.vue'
import WatchlistView from './WatchlistView.vue'
//import PortfolioView from './PortfolioView.vue'

const activeTab = ref('search')

const tabs = [
  { key: 'search', label: 'Search & Analysis' },
  { key: 'watchlist', label: 'Watchlist' },
  { key: 'portfolio', label: 'Portfolio' }
]
</script>

<template>
  <div class="dashboard-container">
    <!-- ✅ Dashboard Header Tabs -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- ✅ Dynamic Content -->
    <div class="tab-content">
      <SearchView v-if="activeTab === 'search'" />
      <WatchlistView v-if="activeTab === 'watchlist'" />
      <PortfolioView v-if="activeTab === 'portfolio'" />
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}

.tabs {
  display: flex;
  background: #f9fafb;
  border-radius: 9999px;
  padding: 0.25rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  margin-bottom: 2rem;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  border-radius: 9999px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: 0.2s;
}

.tab-btn.active {
  background-color: #3b82f6;
  color: white;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
}

.tab-btn:hover {
  color: #1e3a8a;
}

.tab-content {
  width: 100%;
  max-width: 900px;
}
</style>
