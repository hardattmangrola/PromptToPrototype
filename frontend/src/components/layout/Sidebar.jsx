import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Plus, MessageSquare, Settings, Heart } from "lucide-react"

export function Sidebar({ className, isOpen, ...props }) {
    return (
        <div
            className={cn(
                "fixed left-0 top-0 z-40 h-screen w-64 transition-transform duration-300 ease-in-out",
                "bg-background/80 backdrop-blur-lg border-r border-border/50",
                isOpen ? "translate-x-0" : "-translate-x-full",
                className
            )}
            {...props}
        >
            <div className="flex h-full flex-col">
                {/* Logo */}
                <div className="flex h-14 items-center px-5 border-b border-border/50">
                    <Heart className="w-5 h-5 text-primary mr-2" />
                    <span className="font-semibold text-foreground">Clinical AI</span>
                </div>

                {/* New Chat */}
                <div className="px-3 py-3">
                    <Button className="w-full justify-start gap-2" size="sm">
                        <Plus className="h-4 w-4" />
                        New Chat
                    </Button>
                </div>

                {/* History */}
                <ScrollArea className="flex-1 px-3">
                    <p className="px-2 text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                        Recent
                    </p>
                    <div className="space-y-0.5">
                        {["General checkup questions", "Medication side effects", "Lab results explained"].map((item, i) => (
                            <Button
                                key={i}
                                variant="ghost"
                                className="w-full justify-start text-sm font-normal text-muted-foreground hover:text-foreground h-9 px-2"
                            >
                                <MessageSquare className="mr-2 h-3.5 w-3.5 opacity-60" />
                                <span className="truncate">{item}</span>
                            </Button>
                        ))}
                    </div>
                </ScrollArea>

                {/* Settings */}
                <div className="p-3 border-t border-border/50">
                    <Button variant="ghost" className="w-full justify-start gap-2 text-muted-foreground" size="sm">
                        <Settings className="h-4 w-4" />
                        Settings
                    </Button>
                </div>
            </div>
        </div>
    )
}
