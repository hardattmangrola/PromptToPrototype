import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAppStore } from "@/store/useAppStore"
import { cn } from "@/lib/utils"

/**
 * ThemeToggle - Standalone dark/light mode toggle button.
 * Can be used anywhere in the app including auth pages.
 */
export function ThemeToggle({ className, variant = "ghost" }) {
    const { isDarkMode, toggleDarkMode } = useAppStore()

    // Initialize dark mode from localStorage or system preference
    React.useEffect(() => {
        const stored = localStorage.getItem("theme")
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches

        if (stored === "dark" || (!stored && prefersDark)) {
            document.documentElement.classList.add("dark")
            useAppStore.setState({ isDarkMode: true })
        }
    }, [])

    const handleToggle = () => {
        const newMode = !isDarkMode
        if (newMode) {
            document.documentElement.classList.add("dark")
            localStorage.setItem("theme", "dark")
        } else {
            document.documentElement.classList.remove("dark")
            localStorage.setItem("theme", "light")
        }
        toggleDarkMode()
    }

    return (
        <Button
            variant={variant}
            size="icon"
            onClick={handleToggle}
            className={cn(
                "h-9 w-9 rounded-full transition-all duration-300",
                className
            )}
            aria-label="Toggle theme"
        >
            <Sun className={cn(
                "h-4 w-4 transition-all",
                isDarkMode ? "scale-0 rotate-90" : "scale-100 rotate-0"
            )} />
            <Moon className={cn(
                "absolute h-4 w-4 transition-all",
                isDarkMode ? "scale-100 rotate-0" : "scale-0 -rotate-90"
            )} />
        </Button>
    )
}
