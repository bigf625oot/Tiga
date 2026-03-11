<script setup lang="ts">
import { Moon, Sun, Monitor, Palette } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu'
import { useTheme, type ColorTheme } from '@/composables/useTheme'

const { theme, setTheme, colorTheme, setColorTheme } = useTheme()

const colorThemes: { name: ColorTheme; color: string }[] = [
  { name: 'blue', color: 'bg-blue-500' },
  { name: 'green', color: 'bg-green-500' },
  { name: 'orange', color: 'bg-orange-500' },
  { name: 'purple', color: 'bg-purple-500' },
  { name: 'red', color: 'bg-red-500' },
]
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" size="icon" class="h-9 w-9 rounded-full">
        <Sun class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
        <Moon class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        <span class="sr-only">Toggle theme</span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" class="w-48">
      <DropdownMenuLabel>模式</DropdownMenuLabel>
      <DropdownMenuItem @click="setTheme('light')">
        <Sun class="mr-2 h-4 w-4" />
        <span>浅色</span>
        <span v-if="theme === 'light'" class="ml-auto text-xs opacity-60">✓</span>
      </DropdownMenuItem>
      <DropdownMenuItem @click="setTheme('dark')">
        <Moon class="mr-2 h-4 w-4" />
        <span>深色</span>
        <span v-if="theme === 'dark'" class="ml-auto text-xs opacity-60">✓</span>
      </DropdownMenuItem>
      <DropdownMenuItem @click="setTheme('system')">
        <Monitor class="mr-2 h-4 w-4" />
        <span>跟随系统</span>
        <span v-if="theme === 'system'" class="ml-auto text-xs opacity-60">✓</span>
      </DropdownMenuItem>
      
      <DropdownMenuSeparator />
      
      <DropdownMenuLabel>皮肤</DropdownMenuLabel>
      <div class="grid grid-cols-5 gap-1 p-2">
        <button
          v-for="c in colorThemes"
          :key="c.name"
          class="h-6 w-6 rounded-full flex items-center justify-center transition-all hover:scale-110 focus:outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          :class="[c.color, colorTheme === c.name ? 'ring-2 ring-primary ring-offset-2' : '']"
          @click="setColorTheme(c.name)"
          :title="c.name"
        >
          <span class="sr-only">{{ c.name }}</span>
        </button>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
