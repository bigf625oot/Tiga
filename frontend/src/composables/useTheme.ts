import { ref, watch, computed } from 'vue';

export type Theme = 'light' | 'dark' | 'system';
export type ColorTheme = 'blue' | 'green' | 'orange' | 'purple' | 'red';

// State
const theme = ref<Theme>((localStorage.getItem('theme') as Theme) || 'system');
const colorTheme = ref<ColorTheme>((localStorage.getItem('color-theme') as ColorTheme) || 'blue');
const systemPreference = ref<'light' | 'dark'>(
  window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
);

// Media Query Listener
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
const handleSystemChange = (e: MediaQueryListEvent) => {
  systemPreference.value = e.matches ? 'dark' : 'light';
  if (theme.value === 'system') {
    applyTheme();
  }
};
mediaQuery.addEventListener('change', handleSystemChange);

// Application Logic
const applyTheme = () => {
  const root = document.documentElement;
  root.classList.remove('light', 'dark');
  
  const effectiveTheme = theme.value === 'system' ? systemPreference.value : theme.value;
  
  root.classList.add(effectiveTheme);
  root.setAttribute('data-theme', effectiveTheme);
  root.setAttribute('data-color-theme', colorTheme.value);
};

// Watchers
watch(theme, (val) => {
  localStorage.setItem('theme', val);
  applyTheme();
}, { immediate: true });

watch(colorTheme, (val) => {
  localStorage.setItem('color-theme', val);
  applyTheme();
}, { immediate: true });

export function useTheme() {
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme;
  };

  const setColorTheme = (newColorTheme: ColorTheme) => {
    colorTheme.value = newColorTheme;
  };

  // Computed for legacy compatibility (read-only)
  const isLightMode = computed(() => {
    return theme.value === 'light' || (theme.value === 'system' && systemPreference.value === 'light');
  });

  // Legacy toggle (cycles light -> dark -> light)
  const toggleTheme = () => {
    setTheme(isLightMode.value ? 'dark' : 'light');
  };

  return {
    theme,
    colorTheme,
    setTheme,
    setColorTheme,
    isLightMode, // exposed as computed ref
    toggleTheme
  };
}
