import { useCallback, useEffect, useState } from "react";

export type ThemeMode = "light" | "beige" | "midnight" | "charcoal";

const THEME_KEY = "bodhi-theme";

export function getStoredTheme(): ThemeMode {
  try {
    const v = localStorage.getItem(THEME_KEY);
    if (v === "light" || v === "beige" || v === "midnight" || v === "charcoal") return v;
  } catch { /* ignore */ }
  return "midnight";
}

function applyTheme(mode: ThemeMode) {
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem(THEME_KEY, mode);
}

export function useTheme() {
  const [theme, setThemeState] = useState<ThemeMode>(getStoredTheme);

  // Apply on mount
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = useCallback((mode: ThemeMode) => {
    setThemeState(mode);
    applyTheme(mode);
  }, []);

  return { theme, setTheme };
}
