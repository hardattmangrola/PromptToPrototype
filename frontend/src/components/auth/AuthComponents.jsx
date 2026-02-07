import * as React from "react"
import { motion } from "framer-motion"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

/**
 * Shared layout for all auth pages (Login, Register, DoctorLogin)
 */
export function AuthLayout({ children, showBack, onBack }) {
    return (
        <div className="min-h-screen flex flex-col mesh-gradient">
            {/* Header */}
            <div className="flex items-center justify-between p-4">
                {showBack ? (
                    <Button variant="ghost" size="sm" onClick={onBack}>
                        <ArrowLeft className="w-4 h-4 mr-2" />Back
                    </Button>
                ) : <div />}
                <ThemeToggle />
            </div>

            {/* Content */}
            <div className="flex-1 flex items-center justify-center p-6">
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                    className="w-full max-w-sm"
                >
                    {children}
                </motion.div>
            </div>
        </div>
    )
}

/**
 * Auth page header with icon and title
 */
export function AuthHeader({ icon: Icon, title, subtitle, iconClass = "bg-primary/10 text-primary" }) {
    return (
        <div className="text-center mb-6">
            <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4 ${iconClass}`}>
                <Icon className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
        </div>
    )
}

/**
 * Form field with label
 */
export function FormField({ label, type = "text", placeholder, value, onChange, required, className = "" }) {
    return (
        <div>
            <label className="text-sm font-medium text-foreground/80 block mb-1.5">{label}</label>
            <input
                type={type}
                placeholder={placeholder}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                required={required}
                className={`flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
            />
        </div>
    )
}

/**
 * Loading button
 */
export function LoadingButton({ loading, children, ...props }) {
    return (
        <Button disabled={loading} {...props}>
            {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : children}
        </Button>
    )
}

/**
 * Divider with text
 */
export function Divider({ text = "or" }) {
    return (
        <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs">
                <span className="bg-card px-2 text-muted-foreground">{text}</span>
            </div>
        </div>
    )
}
