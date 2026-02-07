import * as React from "react"
import ReactMarkdown from "react-markdown"
import rehypeRaw from "rehype-raw"
import remarkGfm from "remark-gfm"
import { useAppStore } from "@/store/useAppStore"

/**
 * Memoized Markdown Renderer for streaming performance.
 * Handles citation badges [n] as clickable pills.
 */
export const MarkdownRenderer = React.memo(function MarkdownRenderer({
    content,
    citations = []
}) {
    const { setActiveCitation } = useAppStore()

    // Transform citation patterns [1], [2] etc. into clickable elements
    const processedContent = React.useMemo(() => {
        if (!content) return ""
        // Replace [n] with a custom marker for post-processing
        return content.replace(/\[(\d+)\]/g, '<cite-ref data-id="$1">[$1]</cite-ref>')
    }, [content])

    const handleCitationClick = (citationId) => {
        const citation = citations.find(c => c.id === parseInt(citationId))
        if (citation) {
            setActiveCitation({
                url: citation.url || "/sample.pdf",
                page: citation.page || 1,
                source: citation.source
            })
        }
    }

    return (
        <div className="prose prose-slate dark:prose-invert max-w-none prose-p:my-2 prose-headings:my-3 prose-li:my-1">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                    // Custom table styling
                    table: ({ children }) => (
                        <div className="overflow-x-auto my-4">
                            <table className="min-w-full divide-y divide-border text-sm">
                                {children}
                            </table>
                        </div>
                    ),
                    thead: ({ children }) => (
                        <thead className="bg-muted/50">{children}</thead>
                    ),
                    th: ({ children }) => (
                        <th className="px-3 py-2 text-left font-medium text-foreground">
                            {children}
                        </th>
                    ),
                    td: ({ children }) => (
                        <td className="px-3 py-2 border-t border-border">{children}</td>
                    ),
                    // Citation badge handling
                    'cite-ref': ({ 'data-id': dataId, children }) => (
                        <button
                            onClick={() => handleCitationClick(dataId)}
                            className="citation-pill mx-0.5"
                        >
                            {children}
                        </button>
                    ),
                    // Code blocks
                    code: ({ inline, children, ...props }) => {
                        if (inline) {
                            return (
                                <code className="px-1.5 py-0.5 rounded bg-muted text-sm font-mono" {...props}>
                                    {children}
                                </code>
                            )
                        }
                        return (
                            <pre className="bg-muted/50 rounded-lg p-4 overflow-x-auto">
                                <code className="text-sm font-mono" {...props}>
                                    {children}
                                </code>
                            </pre>
                        )
                    },
                    // Strong emphasis
                    strong: ({ children }) => (
                        <strong className="font-semibold text-foreground">{children}</strong>
                    ),
                    // Links
                    a: ({ href, children }) => (
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline"
                        >
                            {children}
                        </a>
                    ),
                }}
            >
                {processedContent}
            </ReactMarkdown>
        </div>
    )
})
