import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Plus, MessageSquare, Settings, Heart, EyeOff, Trash2, X } from "lucide-react"
import { useAppStore } from "@/store/useAppStore"

export function Sidebar({ className, isOpen, onClose, ...props }) {
    const {
        chats,
        activeChatId,
        incognitoChat,
        createChat,
        deleteChat,
        setActiveChat,
        toggleSettings,
    } = useAppStore()

    const [hoveredId, setHoveredId] = React.useState(null)
    const [deleteConfirm, setDeleteConfirm] = React.useState(null)

    const handleNewChat = () => {
        createChat(false)
    }

    const handleNewIncognito = () => {
        createChat(true)
        onClose?.()
    }

    const handleSelectChat = (id) => {
        setActiveChat(id)
    }

    const handleDelete = (e, id) => {
        e.stopPropagation()
        if (deleteConfirm === id) {
            deleteChat(id)
            setDeleteConfirm(null)
        } else {
            setDeleteConfirm(id)
            setTimeout(() => setDeleteConfirm(null), 3000)
        }
    }

    const isIncognitoActive = incognitoChat?.id === activeChatId

    return (
        <div
            className={cn(
                "fixed left-0 top-0 z-40 h-screen w-72 transition-transform duration-300 ease-in-out",
                "bg-background/95 backdrop-blur-xl border-r border-border/50",
                isOpen ? "translate-x-0" : "-translate-x-full",
                className
            )}
            {...props}
        >
            <div className="flex h-full flex-col">
                {/* Header */}
                <div className="flex h-14 items-center justify-between px-4 border-b border-border/50">
                    <div className="flex items-center gap-2">
                        <Heart className="w-5 h-5 text-primary" />
                        <span className="font-semibold text-foreground">Clinical AI</span>
                    </div>
                    <Button variant="ghost" size="icon" className="h-8 w-8 lg:hidden" onClick={onClose}>
                        <X className="h-4 w-4" />
                    </Button>
                </div>

                {/* New Chat Buttons */}
                <div className="p-3 space-y-2">
                    <Button
                        onClick={handleNewChat}
                        className="w-full justify-start gap-2 bg-primary/10 hover:bg-primary/20 text-primary"
                        size="sm"
                    >
                        <Plus className="h-4 w-4" />
                        New Chat
                    </Button>
                    <Button
                        onClick={handleNewIncognito}
                        variant="outline"
                        className="w-full justify-start gap-2 border-purple-500/30 text-purple-400 hover:bg-purple-500/10 hover:text-purple-300"
                        size="sm"
                        disabled={!!incognitoChat}
                    >
                        <EyeOff className="h-4 w-4" />
                        {incognitoChat ? 'Incognito Active' : 'Go Incognito'}
                    </Button>
                </div>

                {/* Active Incognito */}
                {incognitoChat && (
                    <div className="px-3 pb-2">
                        <button
                            onClick={() => handleSelectChat(incognitoChat.id)}
                            className={cn(
                                "w-full flex items-center gap-2 p-2 rounded-lg text-sm transition-all",
                                "bg-gradient-to-r from-purple-500/20 to-violet-500/20 border border-purple-500/30",
                                isIncognitoActive && "ring-2 ring-purple-500/50"
                            )}
                        >
                            <EyeOff className="h-4 w-4 text-purple-400 shrink-0" />
                            <span className="truncate text-purple-300">{incognitoChat.title}</span>
                            <span className="ml-auto text-[10px] text-purple-400/70 uppercase">Not Saved</span>
                        </button>
                    </div>
                )}

                {/* Chat History */}
                <ScrollArea className="flex-1 px-3">
                    {chats.length > 0 && (
                        <>
                            <p className="px-2 text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2 mt-2">
                                Recent Chats
                            </p>
                            <div className="space-y-1">
                                {chats.map((chat) => (
                                    <div
                                        key={chat.id}
                                        onMouseEnter={() => setHoveredId(chat.id)}
                                        onMouseLeave={() => setHoveredId(null)}
                                        className="relative"
                                    >
                                        <button
                                            onClick={() => handleSelectChat(chat.id)}
                                            className={cn(
                                                "w-full flex items-center gap-2 p-2 rounded-lg text-sm transition-all",
                                                "hover:bg-white/10",
                                                activeChatId === chat.id && "bg-primary/10 text-primary"
                                            )}
                                        >
                                            <MessageSquare className="h-3.5 w-3.5 opacity-60 shrink-0" />
                                            <span className="truncate text-left flex-1">{chat.title}</span>
                                        </button>

                                        {/* Delete Button */}
                                        {hoveredId === chat.id && (
                                            <button
                                                onClick={(e) => handleDelete(e, chat.id)}
                                                className={cn(
                                                    "absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded transition-colors",
                                                    deleteConfirm === chat.id
                                                        ? "bg-red-500 text-white"
                                                        : "hover:bg-red-500/20 text-red-400"
                                                )}
                                                title={deleteConfirm === chat.id ? "Click again to confirm" : "Delete"}
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}

                    {chats.length === 0 && !incognitoChat && (
                        <div className="py-8 text-center text-muted-foreground text-sm">
                            <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-30" />
                            <p>No chats yet</p>
                            <p className="text-xs">Start a new conversation</p>
                        </div>
                    )}
                </ScrollArea>

                {/* Settings */}
                <div className="p-3 border-t border-border/50">
                    <Button
                        variant="ghost"
                        className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground"
                        size="sm"
                        onClick={toggleSettings}
                    >
                        <Settings className="h-4 w-4" />
                        Settings
                    </Button>
                </div>
            </div>
        </div>
    )
}
