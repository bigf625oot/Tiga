<script setup lang="ts">
import { Globe } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useI18n } from '@/locales'

const { locale, setLocale } = useI18n()

const languages = [
  { code: 'zh-CN', name: '简体中文' },
  { code: 'en-US', name: 'English' },
  { code: 'ja-JP', name: '日本語' },
  { code: 'ko-KR', name: '한국어' }
] as const;
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" size="icon" class="h-9 w-9 rounded-full text-muted-foreground hover:text-foreground">
        <Globe class="h-[1.2rem] w-[1.2rem]" />
        <span class="sr-only">Toggle language</span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" class="w-32">
      <DropdownMenuItem
        v-for="lang in languages" 
        :key="lang.code"
        @click="setLocale(lang.code)"
        :class="{ 'bg-muted': locale === lang.code }"
      >
        <span>{{ lang.name }}</span>
        <span v-if="locale === lang.code" class="ml-auto text-xs opacity-60">✓</span>
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>