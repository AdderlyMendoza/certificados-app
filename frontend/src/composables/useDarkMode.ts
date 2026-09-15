import { useDark, useToggle } from '@vueuse/core'

// Modo oscuro persistente (clase 'dark' en <html>)
export function useDarkMode() {
  const isDark = useDark({ selector: 'html', attribute: 'class', valueDark: 'dark', valueLight: '' })
  const toggleDark = useToggle(isDark)
  return { isDark, toggleDark }
}
