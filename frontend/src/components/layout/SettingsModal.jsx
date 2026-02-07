import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Moon, Sun, Trash2, Download, Info } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAppStore } from "@/store/useAppStore"
import { cn } from "@/lib/utils"

export function SettingsModal() {
    const { settingsOpen, toggleSettings, isDarkMode, toggleDarkMode, clearAllChats, chats } = useAppStore()

    const handleClearChats = () => {
        if (window.confirm('Are you sure you want to delete all chats? This cannot be undone.')) {
            clearAllChats()
        }
    }

    const handleExport = () => {
        const data = JSON.stringify(chats, null, 2)
        const blob = new Blob([data], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `clinical-ai-chats-${new Date().toISOString().split('T')[0]}.json`
        a.click()
        URL.revokeObjectURL(url)
    }

    return (
        <AnimatePresence>
            {settingsOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={toggleSettings}
                        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 w-full max-w-md"
                    >
                        <div className="glass-panel rounded-2xl border border-white/20 shadow-2xl overflow-hidden">
                            {/* Header */}
                            <div className="flex items-center justify-between p-4 border-b border-white/10">
                                <h2 className="text-lg font-semibold text-foreground">Settings</h2>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={toggleSettings}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>

                            {/* Content */}
                            <div className="p-4 space-y-4">
                                {/* Appearance */}
                                <div className="space-y-3">
                                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                        Appearance
                                    </h3>
                                    <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10">
                                        <div className="flex items-center gap-3">
                                            {isDarkMode ? (
                                                <Moon className="h-5 w-5 text-primary" />
                                            ) : (
                                                <Sun className="h-5 w-5 text-amber-500" />
                                            )}
                                            <span className="text-sm text-foreground">
                                                {isDarkMode ? 'Dark Mode' : 'Light Mode'}
                                            </span>
                                        </div>
                                        <button
                                            onClick={toggleDarkMode}
                                            className={cn(
                                                "relative w-12 h-6 rounded-full transition-colors",
                                                isDarkMode ? "bg-primary" : "bg-muted"
                                            )}
                                        >
                                            <span
                                                className={cn(
                                                    "absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform",
                                                    isDarkMode && "translate-x-6"
                                                )}
                                            />
                                        </button>
                                    </div>
                                </div>

                                {/* Data */}
                                <div className="space-y-3">
                                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                        Data
                                    </h3>
                                    <div className="space-y-2">
                                        <button
                                            onClick={handleExport}
                                            className="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-left"
                                        >
                                            <Download className="h-5 w-5 text-primary" />
                                            <div>
                                                <p className="text-sm text-foreground">Export Chat History</p>
                                                <p className="text-xs text-muted-foreground">Download all chats as JSON</p>
                                            </div>
                                        </button>
                                        <button
                                            onClick={handleClearChats}
                                            className="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-red-500/20 hover:bg-red-500/10 transition-colors text-left"
                                        >
                                            <Trash2 className="h-5 w-5 text-red-500" />
                                            <div>
                                                <p className="text-sm text-red-500">Clear All Chats</p>
                                                <p className="text-xs text-muted-foreground">
                                                    {chats.length} chat{chats.length !== 1 ? 's' : ''} will be deleted
                                                </p>
                                            </div>
                                        </button>
                                    </div>
                                </div>

                                {/* About */}
                                <div className="space-y-3">
                                    <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                                        About
                                    </h3>
                                    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10">
                                        <Info className="h-5 w-5 text-muted-foreground" />
                                        <div>
                                            <p className="text-sm text-foreground">Clinical AI v1.0</p>
                                            <p className="text-xs text-muted-foreground">Healthcare RAG Assistant</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    )
}
