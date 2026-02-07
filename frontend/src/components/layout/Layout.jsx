import { useAppStore } from "@/store/useAppStore"
import { Sidebar } from "./Sidebar"
import { ThemeToggle } from "./ThemeToggle"
import { ProfileMenu } from "./ProfileMenu"
import { Button } from "@/components/ui/button"
import { Menu } from "lucide-react"
import { cn } from "@/lib/utils"

export function Layout({ children }) {
    const { isSidebarOpen, toggleSidebar } = useAppStore()

    return (
        <div className="relative min-h-screen w-full overflow-hidden font-sans mesh-gradient">
            <Sidebar isOpen={isSidebarOpen} />

            <main
                className={cn(
                    "relative z-10 flex flex-col h-screen transition-all duration-300 ease-in-out",
                    isSidebarOpen ? "ml-64" : "ml-0"
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
