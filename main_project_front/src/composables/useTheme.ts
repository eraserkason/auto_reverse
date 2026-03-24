import { ref, computed } from 'vue';
import { darkTheme } from 'naive-ui';

// Simple state to track theme mode
// We default to true (light mode)
const isLightMode = ref(true);

export function useTheme() {
  const persistTheme = () => {
    localStorage.setItem('auto-reverse-theme', isLightMode.value ? 'light' : 'dark');
  };

  const toggleTheme = () => {
    isLightMode.value = !isLightMode.value;
    updateHtmlClass();
    persistTheme();
  };

  const setTheme = (nextLightMode: boolean) => {
    isLightMode.value = nextLightMode;
    updateHtmlClass();
    persistTheme();
  };

  const initTheme = () => {
    const saved = localStorage.getItem('auto-reverse-theme');
    if (saved) {
      isLightMode.value = saved === 'light';
    } else {
      isLightMode.value = true; // Hard default to light mode
    }
    updateHtmlClass();
  };

  const updateHtmlClass = () => {
    if (typeof document !== 'undefined') {
      document.documentElement.style.colorScheme = isLightMode.value ? 'light' : 'dark';
      if (isLightMode.value) {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.style.backgroundColor = '#f4f7fb';
      } else {
        document.documentElement.classList.remove('light');
        document.documentElement.classList.add('dark');
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.style.backgroundColor = '#0b1220';
      }
    }
  };

  const activeTheme = computed(() => {
    return isLightMode.value ? null : darkTheme;
  });

  return {
    isLightMode,
    activeTheme,
    toggleTheme,
    setTheme,
    initTheme
  };
}
