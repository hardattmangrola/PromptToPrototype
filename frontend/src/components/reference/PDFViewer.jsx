import * as React from "react"
import { motion } from "framer-motion"
import { X, FileX2, ExternalLink, ZoomIn, ZoomOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAppStore } from "@/store/useAppStore"
import { cn } from "@/lib/utils"

/**
 * PDFViewer Component
 * Displays PDF with error handling and highlight support.
 * Falls back to a graceful error card if PDF fails to load.
 */
export function PDFViewer({ url, page = 1 }) {
    const { closePDF, activeCitation } = useAppStore()
    const [hasError, setHasError] = React.useState(false)
    const [scale, setScale] = React.useState(1)
    const iframeRef = React.useRef(null)

    React.useEffect(() => {
        setHasError(false)
    }, [url])

    // Format URL for iframe - Google Docs Viewer as fallback for cross-origin PDFs
    const viewerUrl = React.useMemo(() => {
        if (!url) return null
        // For local PDFs, use direct embed
        if (url.startsWith('/') || url.startsWith('blob:')) {
            return url
        }
        // For remote PDFs, use Google Docs Viewer
        return `https://docs.google.com/viewer?url=${encodeURIComponent(url)}&embedded=true`
    }, [url])

    if (!url) return null

    return (
        <div className="h-full flex flex-col bg-background/50 backdrop-blur-sm">
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-border/50 glass-panel">
                <div className="flex items-center gap-2 text-sm text-muted-foreground overflow-hidden">
                    <span className="truncate max-w-[200px]">
                        {activeCitation?.source || "Document Viewer"}
                    </span>
                    {page > 1 && (
                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                            Page {page}
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-1">
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setScale(s => Math.max(0.5, s - 0.25))}
                    >
                        <ZoomOut className="h-4 w-4" />
                    </Button>
                    <span className="text-xs text-muted-foreground w-12 text-center">
                        {Math.round(scale * 100)}%
                    </span>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setScale(s => Math.min(2, s + 0.25))}
                    >
                        <ZoomIn className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={closePDF}
                    >
                        <X className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* PDF Content */}
            <div className="flex-1 overflow-auto p-2">
                {hasError ? (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="h-full flex items-center justify-center"
                    >
                        <div className="glass-panel rounded-xl p-8 text-center max-w-sm">
                            <FileX2 className="w-12 h-12 text-destructive/50 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-foreground mb-2">
                                Document Not Found
                            </h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                The referenced document could not be loaded. It may have been moved or is unavailable.
                            </p>
                            <div className="flex gap-2 justify-center">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setHasError(false)}
                                >
                                    Retry
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={closePDF}
                                >
                                    Close
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                ) : (
                    <div
                        className="w-full h-full rounded-lg overflow-hidden bg-white dark:bg-slate-800"
                        style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}
                    >
                        {viewerUrl ? (
                            <iframe
                                ref={iframeRef}
                                src={viewerUrl}
                                className="w-full h-full border-0"
                                title="PDF Viewer"
                                onError={() => setHasError(true)}
                            />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                                <p className="text-sm">No document selected</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
