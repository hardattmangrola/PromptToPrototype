import * as React from "react"
import { useAuth } from "@/auth/AuthProvider"
import { Button } from "@/components/ui/button"
import { AuthLayout, AuthHeader, FormField, LoadingButton, Divider } from "@/components/auth/AuthComponents"
import { AnimatePresence, motion } from "framer-motion"
import { Stethoscope, ArrowRight, ArrowLeft, Shield, CheckCircle2 } from "lucide-react"

export function DoctorLoginPage({ onNavigate, onLoginSuccess }) {
    const { loginAsDoctor, enterDemoMode } = useAuth()
    const [step, setStep] = React.useState(1)
    const [nmc, setNmc] = React.useState("")
    const [form, setForm] = React.useState({ email: "", password: "" })
    const [error, setError] = React.useState("")
    const [loading, setLoading] = React.useState(false)

    const verifyNMC = async () => {
        setLoading(true)
        setError("")
        await new Promise(r => setTimeout(r, 1000))
        if (nmc.length >= 6) setStep(2)
        else setError("Enter valid 6+ digit NMC number")
        setLoading(false)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError("")
        try {
            await loginAsDoctor(form.email, form.password, nmc)
            onLoginSuccess?.()
        } catch (err) {
            setError(err.message || "Failed to login")
        } finally {
            setLoading(false)
        }
    }

    // Steps indicator
    const Steps = () => (
        <div className="flex items-center justify-center gap-2 mb-5">
            {[1, 2].map((s) => (
                <React.Fragment key={s}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium ${step >= s ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'}`}>
                        {step > s ? <CheckCircle2 className="w-3.5 h-3.5" /> : s}
                    </div>
                    {s < 2 && <div className={`w-8 h-0.5 ${step > 1 ? 'bg-primary' : 'bg-border'}`} />}
                </React.Fragment>
            ))}
        </div>
    )

    return (
        <AuthLayout showBack onBack={() => onNavigate?.('login')}>
            <AuthHeader icon={Stethoscope} title="Doctor Portal" subtitle="Verify your medical license" />
            <Steps />

            <motion.div key={step} initial={{ opacity: 0, x: step === 1 ? -10 : 10 }} animate={{ opacity: 1, x: 0 }} className="glass-panel rounded-2xl p-6">
                {step === 1 ? (
                    <div className="space-y-4">
                        <div className="flex items-start gap-2 p-3 bg-muted/50 rounded-lg text-sm">
                            <Shield className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                            <p className="text-muted-foreground">Enter your NMC registration number.</p>
                        </div>
                        <FormField label="NMC Number" placeholder="123456" value={nmc} onChange={(v) => setNmc(v.replace(/\D/g, ''))} className="font-mono tracking-wider" />
                        <AnimatePresence>
                            {error && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-sm text-destructive text-center">{error}</motion.p>}
                        </AnimatePresence>
                        <LoadingButton loading={loading} onClick={verifyNMC} className="w-full h-10" disabled={nmc.length < 6}>
                            Verify <ArrowRight className="w-4 h-4 ml-2" />
                        </LoadingButton>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg text-sm">
                            <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                            <p className="text-green-700 dark:text-green-300">NMC #{nmc} verified</p>
                        </div>
                        <FormField label="Email" type="email" placeholder="doctor@hospital.com" value={form.email} onChange={(v) => setForm(f => ({ ...f, email: v }))} required />
                        <FormField label="Password" type="password" placeholder="••••••••" value={form.password} onChange={(v) => setForm(f => ({ ...f, password: v }))} required />
                        <AnimatePresence>
                            {error && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-sm text-destructive text-center">{error}</motion.p>}
                        </AnimatePresence>
                        <LoadingButton loading={loading} type="submit" className="w-full h-10">Sign In</LoadingButton>
                        <Button type="button" variant="ghost" className="w-full" onClick={() => { setStep(1); setError("") }}>
                            <ArrowLeft className="w-4 h-4 mr-2" />Different Number
                        </Button>
                    </form>
                )}
                <Divider />
                <Button variant="outline" className="w-full h-10" onClick={() => { enterDemoMode?.('doctor'); onLoginSuccess?.() }}>Demo Doctor Mode</Button>
            </motion.div>
        </AuthLayout>
    )
}
