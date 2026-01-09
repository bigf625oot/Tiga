<template>
  <div class="max-w-[1000px] mx-auto p-4">
    <!-- Search Box Area -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
        <div class="flex gap-4">
            <div class="flex-1 relative">
                <input 
                    v-model="query" 
                    @keyup.enter="handleSearch" 
                    type="text" 
                    placeholder="输入关键词，例如：'2024年工业互联网发展趋势'" 
                    class="w-full pl-4 pr-4 py-3 rounded-lg border border-slate-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all"
                >
            </div>
            <button 
                @click="handleSearch" 
                :disabled="loading || !query.trim()"
                class="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
                <svg v-if="loading" class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <span v-else>搜索</span>
            </button>
        </div>
        
        <!-- Search Options (Simple) -->
        <div class="mt-4 flex gap-6 text-sm text-slate-500">
            <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="useGovSites" class="rounded text-blue-600 focus:ring-blue-500">
                <span>优先政府官网</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" v-model="useAuthSites" class="rounded text-blue-600 focus:ring-blue-500">
                <span>优先权威媒体</span>
            </label>
        </div>
    </div>

    <!-- Status / Error -->
    <div v-if="error" class="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-2">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        {{ error }}
    </div>

    <!-- Results List -->
    <div v-if="results.length > 0" class="space-y-6">
        <div class="flex items-center justify-between text-slate-500 text-sm mb-2">
            <span>找到 {{ results.length }} 条相关结果</span>
            <button @click="results = []" class="hover:text-red-500">清除结果</button>
        </div>

        <div v-for="(item, index) in results" :key="index" class="bg-white rounded-xl p-6 shadow-sm border border-slate-100 hover:shadow-md transition-shadow group">
            <div class="flex items-start justify-between gap-4 mb-2">
                <h3 class="text-lg font-bold text-slate-800 group-hover:text-blue-600 transition-colors leading-tight">
                    <a :href="item.url" target="_blank" class="hover:underline">{{ item.title }}</a>
                </h3>
                <span 
                    class="text-xs px-2 py-1 rounded border whitespace-nowrap"
                    :class="{
                        'bg-red-50 text-red-600 border-red-100': item.tier === 'core',
                        'bg-blue-50 text-blue-600 border-blue-100': item.tier === 'authoritative',
                        'bg-slate-50 text-slate-500 border-slate-100': item.tier === 'global'
                    }"
                >
                    {{ getTierLabel(item.tier) }}
                </span>
            </div>
            
            <div class="flex items-center gap-4 text-xs text-slate-400 mb-3">
                <span class="flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    {{ item.source }}
                </span>
                <span class="flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    {{ item.news_time }}
                </span>
            </div>
            
            <p class="text-slate-600 text-sm leading-relaxed line-clamp-3">{{ item.content }}</p>
        </div>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="!loading && !error && hasSearched" class="text-center py-20 text-slate-400">
        <div class="mb-4 text-6xl">🔍</div>
        <p>未找到相关结果，请尝试更换关键词</p>
    </div>
    
    <!-- Intro State -->
    <div v-else-if="!loading && !hasSearched" class="text-center py-20">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-blue-50 rounded-full mb-6">
            <svg class="w-10 h-10 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </div>
        <h3 class="text-xl font-bold text-slate-800 mb-2">全网智能检索</h3>
        <p class="text-slate-500 max-w-md mx-auto">聚合政府官网、权威媒体及全网信息，为您提供精准的行业情报。</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1' 
});

const query = ref('');
const loading = ref(false);
const error = ref('');
const results = ref([]);
const hasSearched = ref(false);

const useGovSites = ref(true);
const useAuthSites = ref(true);

const getTierLabel = (tier) => {
    const map = {
        'core': '政府官网',
        'authoritative': '权威媒体',
        'global': '全网检索'
    };
    return map[tier] || tier;
};

const handleSearch = async () => {
    if (!query.value.trim()) return;
    
    loading.value = true;
    error.value = '';
    results.value = [];
    hasSearched.value = true;
    
    try {
        const govSites = useGovSites.value ? ["gov.cn", "miit.gov.cn"] : []; // Example sites
        
        const payload = {
            keywords: [query.value],
            gov_sites: govSites,
            authoritative_sites: useAuthSites.value ? undefined : [], // Use default if checked, else empty
            max_results: 20
        };
        
        const res = await api.post('/news_search/search', payload);
        
        if (res.data.success) {
            results.value = res.data.data.results;
        } else {
            error.value = res.data.message || '搜索失败';
        }
    } catch (e) {
        error.value = e.response?.data?.detail || '网络请求失败';
        console.error(e);
    } finally {
        loading.value = false;
    }
};
</script>
