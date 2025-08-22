import { createContext, useState, useContext, useMemo, useEffect } from 'react';
// Correctly import ReactNode as a type
import type { ReactNode } from 'react';

type Theme = 'light' | 'dark';
interface ThemeContextType {
 theme: Theme;
 toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
 const [theme, setTheme] = useState<Theme>('light');

 const toggleTheme = () => {
  setTheme(prevTheme => (prevTheme === 'dark' ? 'light' : 'dark'));
 };

 // useMemo is good practice here to prevent re-rendering consumers when the value hasn't changed
 const value = useMemo(() => ({ theme, toggleTheme }), [theme]);
 
 useEffect(() => {
   const root = window.document.documentElement;
   if (theme === 'dark') {
     root.classList.add('dark');
   } else {
     root.classList.remove('dark');
   }
 }, [theme]);

 // Correct syntax for the provider component
 return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = (): ThemeContextType => {
 const context = useContext(ThemeContext);
 if (!context) {
  throw new Error('useTheme must be used within a ThemeProvider');
 }
 return context;
};