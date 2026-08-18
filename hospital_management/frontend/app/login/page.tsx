"use client";

import { Button } from "@/components/ui/button";
import { Activity, Lock, Mail, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export default function LoginPage() {
    const [role, setRole] = useState<'doctor' | 'receptionist' | 'admin'>('doctor');

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4 relative overflow-hidden">
            {/* Background Decor */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

            <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800 p-8 relative z-10 animate-fade-in">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center h-12 w-12 rounded-xl bg-primary/10 text-primary mb-4">
                        <Activity className="h-6 w-6" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Welcome Back</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-2">Sign in to Vishwakarma HMS</p>
                </div>

                {/* Role Selector */}
                <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl mb-8">
                    {(['doctor', 'receptionist', 'admin'] as const).map((r) => (
                        <button
                            key={r}
                            onClick={() => setRole(r)}
                            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all capitalize ${role === r
                                    ? 'bg-white dark:bg-slate-700 text-primary shadow-sm'
                                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                                }`}
                        >
                            {r}
                        </button>
                    ))}
                </div>

                <form className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-2.5 h-5 w-5 text-slate-400" />
                            <input
                                type="email"
                                className="w-full pl-10 h-10 rounded-lg border border-slate-200 dark:border-slate-700 bg-transparent focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                                placeholder="name@hospital.com"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-2.5 h-5 w-5 text-slate-400" />
                            <input
                                type="password"
                                className="w-full pl-10 h-10 rounded-lg border border-slate-200 dark:border-slate-700 bg-transparent focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" className="rounded border-slate-300 text-primary focus:ring-primary" />
                            <span className="text-slate-600 dark:text-slate-400">Remember me</span>
                        </label>
                        <a href="#" className="text-primary hover:underline">Forgot password?</a>
                    </div>

                    <Link href={`/dashboard/${role}`}>
                        <Button className="w-full mt-4" size="lg">
                            Sign In <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </Link>
                </form>

                <div className="mt-6 text-center text-sm text-slate-500">
                    Don't have an account? <span className="text-slate-400">Contact IT Admin</span>
                </div>
            </div>
        </div>
    );
}
