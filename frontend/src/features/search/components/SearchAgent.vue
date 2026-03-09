<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import { Search, Loader2, ChevronDown, SlidersHorizontal, AlertCircle, X, ExternalLink, Calendar, Globe } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { useToast } from '@/components/ui/toast/use-toast'

// Types
interface SearchResult {
  title: string
  url: string
  content: string
  source: string
  news_time: string
  tier: 'core' | 'crawler' | 'authoritative' | 'tavily' | 'global' | 'aliyun'
}

interface AdvancedForm {
  groupTag: string
  constraints: string
  timeRange: string
  requirements: string
  enabledTiers: string[]
}

// State
const query = ref('')
const loading = ref(false)
const error = ref('')
const results = ref<SearchResult[]>([])
const hasSearched = ref(false)
const showAdvanced = ref(false)

// Options
const useGovSites = ref(true)
const useAuthSites = ref(true)

const advancedForm = ref<AdvancedForm>({
  groupTag: '',
  constraints: '',
  timeRange: '不限',
  requirements: '',
  enabledTiers: ['crawler', 'tavily', 'aliyun']
})

const timeRangeOptions = ['不限', '最近一天', '最近一周', '最近一月', '最近一年']

const api = axios.create({
  baseURL: '/api/v1'
})

const { toast } = useToast()

// Computed
const hasResults = computed(() => results.value.length > 0)
const isSearchDisabled = computed(() => loading.value || !query.value.trim())

// Methods
const getTierLabel = (tier: string) => {
  const map: Record<string, string> = {
    'core': '政府官网',
    'crawler': '政府官网',
    'authoritative': '权威媒体',
    'tavily': '权威媒体',
    'global': '全网检索',
    'aliyun': '全网检索'
  }
  return map[tier] || tier
}

const getTierVariant = (tier: string): "default" | "secondary" | "destructive" | "outline" => {
  if (tier === 'core' || tier === 'crawler') return 'destructive'
  if (tier === 'authoritative' || tier === 'tavily') return 'secondary' // Using secondary for purple-ish feel if customized, or default
  return 'outline'
}

const handleSearch = async () => {
  if (!query.value.trim()) return
  
  loading.value = true
  error.value = ''
  results.value = []
  hasSearched.value = true
  
  try {
    const hasAdvancedInput = advancedForm.value.groupTag || 
                             advancedForm.value.constraints || 
                             advancedForm.value.requirements || 
                             (advancedForm.value.timeRange && advancedForm.value.timeRange !== '不限')

    if (showAdvanced.value || hasAdvancedInput) {
      let extraRequirements: string[] = []
      if (useGovSites.value) extraRequirements.push("优先来源于政府官网的信息")
      if (useAuthSites.value) extraRequirements.push("优先来源于权威媒体的报道")
      
      const baseRequirements = advancedForm.value.requirements || ''
      const finalRequirements = [baseRequirements, ...extraRequirements].filter(Boolean).join('，')

      const payload = {
        keywords: [query.value],
        group_tag: advancedForm.value.groupTag || '通用',
        keyword_constraints: advancedForm.value.constraints || '',
        result_requirements: finalRequirements,
        time_range: advancedForm.value.timeRange === '不限' ? null : advancedForm.value.timeRange,
        max_char_limit: 1000,
        enabled_tiers: advancedForm.value.enabledTiers
      }
      
      const res = await api.post('/news_search/custom_search', payload)
      
      if (res.data.success) {
        results.value = res.data.data.results
        if (results.value.length === 0) {
          toast({
            title: "未找到结果",
            description: "请尝试调整关键词或搜索条件",
            variant: "default",
          })
        }
      } else {
        throw new Error(res.data.message || '搜索失败')
      }
    } else {
      const govSites = useGovSites.value ? ["gov.cn", "miit.gov.cn"] : []
      
      const payload = {
        keywords: [query.value],
        gov_sites: govSites,
        authoritative_sites: useAuthSites.value ? undefined : [],
        max_results: 20
      }
      
      const res = await api.post('/news_search/search', payload)
      
      if (res.data.success) {
        results.value = res.data.data.results
        if (results.value.length === 0) {
          toast({
            title: "未找到结果",
            description: "请尝试调整关键词",
            variant: "default",
          })
        }
      } else {
        throw new Error(res.data.message || '搜索失败')
      }
    }
  } catch (e: any) {
    const errorMsg = e.response?.data?.detail || e.message || '网络请求失败'
    error.value = errorMsg
    toast({
      title: "搜索出错",
      description: errorMsg,
      variant: "destructive",
    })
    console.error(e)
  } finally {
    loading.value = false
  }
}

const clearResults = () => {
  results.value = []
  hasSearched.value = false
  query.value = ''
}
</script>

<template>
  <div class="w-full max-w-5xl mx-auto p-4 md:p-6 space-y-8 min-h-[calc(100vh-4rem)]">
    <!-- Header / Intro -->
    <div v-if="!hasResults && !loading" class="text-center py-12 md:py-20 animate-in fade-in zoom-in duration-500">
      <div class="inline-flex items-center justify-center w-16 h-16 md:w-20 md:h-20 bg-primary/10 rounded-full mb-6 ring-4 ring-primary/5">
        <Globe class="w-8 h-8 md:w-10 md:h-10 text-primary" />
      </div>
      <h1 class="text-2xl md:text-3xl font-bold tracking-tight mb-3 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
        全网智能检索
      </h1>
      <p class="text-muted-foreground max-w-lg mx-auto text-sm md:text-base leading-relaxed">
        聚合政府官网、权威媒体及全网信息，为您提供精准的行业情报与深度洞察。
      </p>
    </div>

    <!-- Search Area -->
    <Card class="border-none shadow-lg bg-card/50 backdrop-blur-sm sticky top-4 z-10 transition-all duration-300" :class="{ 'shadow-sm': hasResults }">
      <CardContent class="p-4 md:p-6 space-y-4">
        <div class="flex flex-col md:flex-row gap-3 md:gap-4">
          <div class="relative flex-1 group">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
            <Input 
              v-model="query" 
              @keyup.enter="handleSearch"
              type="text" 
              placeholder="输入关键词，例如：'2024年工业互联网发展趋势'" 
              class="pl-10 h-12 text-base shadow-sm border-muted-foreground/20 focus-visible:ring-primary/20"
              aria-label="搜索关键词"
            />
          </div>
          <Button 
            @click="handleSearch" 
            :disabled="isSearchDisabled"
            size="lg"
            class="h-12 px-8 font-medium shadow-md transition-all active:scale-95"
          >
            <Loader2 v-if="loading" class="w-5 h-5 mr-2 animate-spin" />
            <span v-else>立即搜索</span>
          </Button>
        </div>

        <!-- Quick Filters -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
          <div class="flex items-center gap-6">
            <div class="flex items-center space-x-2">
              <Checkbox id="gov-sites" v-model:checked="useGovSites" />
              <Label for="gov-sites" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer">
                优先政府官网
              </Label>
            </div>
            <div class="flex items-center space-x-2">
              <Checkbox id="auth-sites" v-model:checked="useAuthSites" />
              <Label for="auth-sites" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer">
                优先权威媒体
              </Label>
            </div>
          </div>
          
          <Collapsible v-model:open="showAdvanced" class="w-full sm:w-auto">
            <CollapsibleTrigger as-child>
              <Button variant="ghost" size="sm" class="w-full sm:w-auto text-muted-foreground hover:text-primary gap-2">
                <SlidersHorizontal class="w-4 h-4" />
                <span>高级筛选</span>
                <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': showAdvanced }" />
              </Button>
            </CollapsibleTrigger>
          </Collapsible>
        </div>

        <!-- Advanced Options Panel -->
        <Collapsible v-model:open="showAdvanced">
          <CollapsibleContent class="space-y-4 pt-4 animate-accordion-down overflow-hidden">
            <Separator class="my-4" />
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">关键词分组</Label>
                <Input v-model="advancedForm.groupTag" placeholder="例如：能源行业、政策法规" class="h-9" />
              </div>
              <div class="space-y-2">
                <Label class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">时间范围</Label>
                <Select v-model="advancedForm.timeRange">
                  <SelectTrigger class="h-9 w-full">
                    <SelectValue placeholder="选择时间范围" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="opt in timeRangeOptions" :key="opt" :value="opt">
                      {{ opt }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">关键词限定</Label>
                <Input v-model="advancedForm.constraints" placeholder="例如：必须包含'碳达峰'，不包含'煤炭'" class="h-9" />
              </div>
              <div class="space-y-2">
                <Label class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">结果要求</Label>
                <Input v-model="advancedForm.requirements" placeholder="例如：按时间倒序，优先权威媒体" class="h-9" />
              </div>
              <div class="col-span-1 md:col-span-2 space-y-3">
                <Label class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">数据来源</Label>
                <div class="flex flex-wrap gap-4">
                  <div class="flex items-center space-x-2 bg-muted/50 px-3 py-1.5 rounded-md">
                    <Checkbox 
                      id="source-crawler" 
                      :checked="advancedForm.enabledTiers.includes('crawler')"
                      @update:checked="(checked) => {
                        if (checked) advancedForm.enabledTiers.push('crawler')
                        else advancedForm.enabledTiers = advancedForm.enabledTiers.filter(t => t !== 'crawler')
                      }"
                    />
                    <Label for="source-crawler" class="text-sm font-normal cursor-pointer">政府官网爬虫</Label>
                  </div>
                  <div class="flex items-center space-x-2 bg-muted/50 px-3 py-1.5 rounded-md">
                    <Checkbox 
                      id="source-tavily" 
                      :checked="advancedForm.enabledTiers.includes('tavily')"
                      @update:checked="(checked) => {
                        if (checked) advancedForm.enabledTiers.push('tavily')
                        else advancedForm.enabledTiers = advancedForm.enabledTiers.filter(t => t !== 'tavily')
                      }"
                    />
                    <Label for="source-tavily" class="text-sm font-normal cursor-pointer">权威媒体 (Tavily)</Label>
                  </div>
                  <div class="flex items-center space-x-2 bg-muted/50 px-3 py-1.5 rounded-md">
                    <Checkbox 
                      id="source-aliyun" 
                      :checked="advancedForm.enabledTiers.includes('aliyun')"
                      @update:checked="(checked) => {
                        if (checked) advancedForm.enabledTiers.push('aliyun')
                        else advancedForm.enabledTiers = advancedForm.enabledTiers.filter(t => t !== 'aliyun')
                      }"
                    />
                    <Label for="source-aliyun" class="text-sm font-normal cursor-pointer">全网检索 (Aliyun)</Label>
                  </div>
                </div>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>

    <!-- Error State -->
    <Alert v-if="error" variant="destructive" class="animate-in fade-in slide-in-from-top-2">
      <AlertCircle class="h-4 w-4" />
      <AlertTitle>搜索失败</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Loading Skeletons -->
    <div v-if="loading" class="space-y-4 animate-in fade-in duration-500">
      <div class="flex justify-between items-center mb-4">
        <Skeleton class="h-4 w-32" />
        <Skeleton class="h-4 w-20" />
      </div>
      <div v-for="i in 3" :key="i" class="space-y-3 p-6 border rounded-xl bg-card">
        <div class="flex justify-between">
          <Skeleton class="h-6 w-2/3" />
          <Skeleton class="h-5 w-16" />
        </div>
        <div class="flex gap-4">
          <Skeleton class="h-4 w-24" />
          <Skeleton class="h-4 w-32" />
        </div>
        <Skeleton class="h-20 w-full" />
      </div>
    </div>

    <!-- Results List -->
    <div v-if="hasResults && !loading" class="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div class="flex items-center justify-between px-1">
        <h2 class="text-lg font-semibold tracking-tight flex items-center gap-2">
          搜索结果
          <Badge variant="secondary" class="rounded-full px-2.5">{{ results.length }}</Badge>
        </h2>
        <Button variant="ghost" size="sm" @click="clearResults" class="text-muted-foreground hover:text-destructive transition-colors">
          <X class="w-4 h-4 mr-1" />
          清除结果
        </Button>
      </div>

      <ScrollArea class="h-[calc(100vh-24rem)] pr-4">
        <div class="space-y-4 pb-8">
          <Card v-for="(item, index) in results" :key="index" class="group hover:shadow-md transition-all duration-300 border-muted/60 hover:border-primary/20">
            <CardHeader class="pb-3 space-y-2">
              <div class="flex items-start justify-between gap-4">
                <CardTitle class="text-lg leading-snug font-semibold text-card-foreground group-hover:text-primary transition-colors">
                  <a :href="item.url" target="_blank" rel="noopener noreferrer" class="hover:underline flex items-start gap-2">
                    {{ item.title }}
                    <ExternalLink class="w-4 h-4 opacity-0 group-hover:opacity-50 transition-opacity mt-1" />
                  </a>
                </CardTitle>
                <Badge :variant="getTierVariant(item.tier)" class="shrink-0 font-normal">
                  {{ getTierLabel(item.tier) }}
                </Badge>
              </div>
              <CardDescription class="flex items-center gap-4 text-xs mt-1">
                <span class="flex items-center gap-1.5 text-muted-foreground/80">
                  <Globe class="w-3.5 h-3.5" />
                  {{ item.source }}
                </span>
                <span class="flex items-center gap-1.5 text-muted-foreground/80">
                  <Calendar class="w-3.5 h-3.5" />
                  {{ item.news_time }}
                </span>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p class="text-sm text-muted-foreground leading-relaxed line-clamp-3 group-hover:text-foreground/80 transition-colors">
                {{ item.content }}
              </p>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>

    <!-- Empty State -->
    <div v-if="hasSearched && !hasResults && !loading && !error" class="text-center py-20 text-muted-foreground animate-in fade-in zoom-in duration-300">
      <div class="w-16 h-16 bg-muted/30 rounded-full flex items-center justify-center mx-auto mb-4">
        <Search class="w-8 h-8 opacity-50" />
      </div>
      <h3 class="text-lg font-medium text-foreground mb-1">未找到相关结果</h3>
      <p class="text-sm">请尝试更换关键词或调整筛选条件</p>
    </div>
  </div>
</template>

<style scoped>
/* Custom animations can go here if not covered by Tailwind Animate */
</style>
