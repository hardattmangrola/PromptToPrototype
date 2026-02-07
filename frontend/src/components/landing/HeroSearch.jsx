import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, Paperclip, FileText, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useAppStore } from "@/store/useAppStore"

export function HeroSearch({ onSendMessage }) {
    const { interactionMode } = useAppStore()
    const [query, setQuery] = React.useState("")
    const [isDragOver, setIsDragOver] = React.useState(false)
    const [selectedFile, setSelectedFile] = React.useState(null)
    const fileInputRef = React.useRef(null)
    const inputRef = React.useRef(null)

    const isLanding = interactionMode === 'landing'

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!query.trim() && !selectedFile) return
        onSendMessage?.(query, selectedFile)
        setQuery("")
        setSelectedFile(null)
    }

    const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true) }
    const handleDragLeave = (e) => { e.preventDefault(); setIsDragOver(false) }
    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragOver(false)
        if (e.dataTransfer.files?.[0]) setSelectedFile(e.dataTransfer.files[0])
    }
    const handleFileSelect = (e) => {
        if (e.target.files?.[0]) setSelectedFile(e.target.files[0])
    }

    const quickActions = [
        "Check symptoms",
        "Medication info",
        "Lab results"
    ]

    return (
        <div className={cn(
            "w-full transition-all duration-500 ease-out",
            isLanding
                ? "flex flex-col items-center justify-center min-h-[60vh] px-4"
                : "fixed bottom-0 left-0 right-0 p-4 z-40"
        )}>
            {/* Title - Landing only */}
            <AnimatePresence>
                {isLanding && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10, transition: { duration: 0.15 } }}
                        className="text-center mb-6"
                    >
                        <h1 className="text-3xl font-semibold text-foreground mb-2">
                            How can I help you today?
                        </h1>
                        <p className="text-muted-foreground">
                            Ask any health-related question
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Search Box */}
            <motion.div
                layout
                layoutId="search-container"
                className={cn("w-full max-w-2xl mx-auto", !isLanding && "max-w-3xl")}
                transition={{ type: "spring", stiffness: 400, damping: 35 }}
            >
                <motion.div
                    className={cn(
                        "glass-panel rounded-2xl transition-shadow",
                        isDragOver && "ring-2 ring-primary/50",
                        !isLanding && "shadow-xl"
                    )}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                >
                    <form onSubmit={handleSubmit} className="relative flex items-center p-2">
                        <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileSelect} accept=".pdf,.txt,.docx" />

                        <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-9 w-9 shrink-0 text-muted-foreground hover:text-foreground"
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <Paperclip className="h-4 w-4" />
                        </Button>

                        <div className="flex-1 flex flex-col px-2">
                            <AnimatePresence>
                                {selectedFile && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="flex items-center gap-2 text-xs text-primary bg-primary/5 w-fit px-2 py-1 rounded mb-1"
                                    >
                                        <FileText className="h-3 w-3" />
                                        <span className="max-w-[150px] truncate">{selectedFile.name}</span>
                                        <button type="button" onClick={() => setSelectedFile(null)} className="hover:bg-primary/10 rounded-full p-0.5">
                                            <X className="h-3 w-3" />
                                        </button>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <input
                                ref={inputRef}
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Ask a question..."
                                className="w-full bg-transparent border-0 outline-none text-foreground placeholder:text-muted-foreground/50 text-sm py-2"
                            />
                        </div>

                        <Button
                            type="submit"
                            size="icon"
                            disabled={!query.trim() && !selectedFile}
                            className="h-9 w-9 shrink-0 rounded-xl"
                        >
                            <Search className="h-4 w-4" />
                        </Button>
                    </form>
                </motion.div>
            </motion.div>

            {/* Quick Actions - Landing only */}
            <AnimatePresence>
                {isLanding && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1, transition: { delay: 0.1 } }}
                        exit={{ opacity: 0 }}
                        className="mt-5 flex flex-wrap justify-center gap-2"
                    >
                        {quickActions.map((action) => (
                            <button
                                key={action}
                                onClick={() => { setQuery(action); inputRef.current?.focus() }}
                                className="px-3 py-1.5 rounded-full text-sm text-muted-foreground border border-border/50 bg-background/50 hover:bg-muted/50 transition-colors"
                            >
                                {action}
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
