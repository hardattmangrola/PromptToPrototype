import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, Paperclip, FileText, X, Upload, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useAppStore } from "@/store/useAppStore"
import { useDocumentUpload } from "@/hooks/use-document-upload"

export function HeroSearch({ onSendMessage }) {
    const { interactionMode } = useAppStore()
    const { uploadDocument, clearDocument, uploading, uploadedDocument, error: uploadError } = useDocumentUpload()

    const [query, setQuery] = React.useState("")
    const [isDragOver, setIsDragOver] = React.useState(false)
    const fileInputRef = React.useRef(null)
    const inputRef = React.useRef(null)

    const isLanding = interactionMode === 'landing'

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!query.trim()) return
        onSendMessage?.(query)
        setQuery("")
    }

    const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true) }
    const handleDragLeave = (e) => { e.preventDefault(); setIsDragOver(false) }

    const handleDrop = async (e) => {
        e.preventDefault()
        setIsDragOver(false)
        const file = e.dataTransfer.files?.[0]
        if (file?.name.toLowerCase().endsWith('.pdf')) {
            await uploadDocument(file)
        }
    }

    const handleFileSelect = async (e) => {
        const file = e.target.files?.[0]
        if (file) await uploadDocument(file)
    }

    const quickActions = ["Check symptoms", "Medication info", "Lab results"]

    return (
        <div className={cn(
            "w-full transition-all duration-500 ease-out",
            isLanding ? "flex flex-col items-center justify-center min-h-[60vh] px-4" : "fixed bottom-0 left-0 right-0 p-4 z-40"
        )}>
            {/* Title */}
            <AnimatePresence>
                {isLanding && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10, transition: { duration: 0.15 } }}
                        className="text-center mb-6"
                    >
                        <h1 className="text-3xl font-semibold text-foreground mb-2">How can I help you today?</h1>
                        <p className="text-muted-foreground">Ask any health-related question</p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Uploaded Document Badge */}
            {uploadedDocument && (
                <motion.div
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-3 flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm"
                >
                    <FileText className="w-4 h-4" />
                    <span className="max-w-[200px] truncate">{uploadedDocument.filename}</span>
                    <span className="text-xs text-muted-foreground">({uploadedDocument.chunk_count} chunks)</span>
                    <button onClick={clearDocument} className="hover:bg-primary/20 rounded-full p-0.5">
                        <X className="w-3.5 h-3.5" />
                    </button>
                </motion.div>
            )}

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
                        <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileSelect} accept=".pdf" />

                        <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-9 w-9 shrink-0 text-muted-foreground hover:text-foreground"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploading}
                        >
                            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Paperclip className="h-4 w-4" />}
                        </Button>

                        <input
                            ref={inputRef}
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder={uploadedDocument ? `Ask about ${uploadedDocument.filename}...` : "Ask a question..."}
                            className="flex-1 px-2 bg-transparent border-0 outline-none text-foreground placeholder:text-muted-foreground/50 text-sm py-2"
                        />

                        <Button type="submit" size="icon" disabled={!query.trim()} className="h-9 w-9 shrink-0 rounded-xl">
                            <Search className="h-4 w-4" />
                        </Button>
                    </form>

                    {uploadError && (
                        <p className="px-4 pb-2 text-xs text-destructive">{uploadError}</p>
                    )}
                </motion.div>
            </motion.div>

            {/* Quick Actions */}
            <AnimatePresence>
                {isLanding && !uploadedDocument && (
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

                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="px-3 py-1.5 rounded-full text-sm text-primary border border-primary/30 bg-primary/5 hover:bg-primary/10 transition-colors flex items-center gap-1.5"
                        >
                            <Upload className="w-3.5 h-3.5" />
                            Upload PDF
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
