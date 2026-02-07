import { useAppStore } from "@/store/useAppStore"
import { Sidebar } from "./Sidebar"
import { ThemeToggle } from "./ThemeToggle"
import { ProfileMenu } from "./ProfileMenu"
import { Button } from "@/components/ui/button"
import { Menu, EyeOff, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"

export function Layout({ children }) {
    const { isSidebarOpen, toggleSidebar, incognitoChat, activeChatId, leaveIncognito } = useAppStore()

    const isIncognito = incognitoChat?.id === activeChatId

    // Immersive incognito mode - hide sidebar and show minimal header
    if (isIncognito) {
        return (
            <div className="relative min-h-screen w-full overflow-hidden font-sans incognito-mode">
                <main className="relative z-10 flex flex-col h-screen">
                    {/* Incognito Header */}
                    <header className="h-14 flex items-center justify-between px-4 md:px-6 border-b border-purple-500/20 bg-purple-900/10 backdrop-blur-lg sticky top-0 z-30">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/20 border border-purple-500/30">
                                <EyeOff className="w-4 h-4 text-purple-400" />
                                <span className="text-sm text-purple-300 font-medium">Incognito Mode</span>
                            </div>
                            <span className="text-xs text-purple-400/60">Nothing is saved</span>
                        </div>

                        <Button
                            onClick={leaveIncognito}
                            variant="outline"
                            size="sm"
                            className="border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300 gap-2"
                        >
                            <LogOut className="h-4 w-4" />
                            Leave Incognito
                        </Button>
                    </header>

                    {/* Main Content */}
                    <div className="flex-1 overflow-hidden relative">
                        {children}
                    </div>
                </main>
            </div>
        )
    }

    // Normal mode
    return (
        <div className="relative min-h-screen w-full overflow-hidden font-sans mesh-gradient">
            <Sidebar isOpen={isSidebarOpen} onClose={() => toggleSidebar()} />

            <main
                className={cn(
                    "relative z-10 flex flex-col h-screen transition-all duration-300 ease-in-out",
                    isSidebarOpen ? "ml-72" : "ml-0"
                )}
            >
                {/* Header */}
                <header className="h-14 flex items-center justify-between px-4 md:px-6 border-b border-border/50 bg-background/60 backdrop-blur-lg sticky top-0 z-30">
                    <div className="flex items-center gap-3">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={toggleSidebar}
                            className="h-9 w-9 text-muted-foreground hover:text-foreground"
                        >
                            <Menu className="h-5 w-5" />
                        </Button>
                        <span className="text-sm font-medium text-foreground hidden md:block">
                            Clinical Assistant
                        </span>
                    </div>

                    <div className="flex items-center gap-2">
                        <ThemeToggle />
                        <ProfileMenu />
                    </div>
                </header>

                {/* Main Content */}
                <div className="flex-1 overflow-hidden relative">
                    {children}
                </div>
            </main>
        </div>
    )
}
