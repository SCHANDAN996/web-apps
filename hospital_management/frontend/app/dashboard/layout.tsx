"use client";

import { Button } from "@/components/ui/button";
import { Activity, BarChart3, Calendar, FileText, Home, LogOut, Settings, Users } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen bg-slate-50 dark:bg-slate-950 overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col hidden md:flex">
                <div className="h-16 flex items-center px-6 border-b border-slate-100 dark:border-slate-800">
                    <Activity className="h-6 w-6 text-primary mr-2" />
                    <span className="font-bold text-lg text-slate-900 dark:text-white">Vishwakarma</span>
                </div>

                <div className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
                    <SidebarLink href="/dashboard/doctor" icon={<Home />} label="Overview" />
                    <SidebarLink href="/dashboard/doctor/patients" icon={<Users />} label="Patients" />
                    <SidebarLink href="/dashboard/doctor/appointments" icon={<Calendar />} label="Appointments" />
                    <SidebarLink href="/dashboard/doctor/emr" icon={<FileText />} label="EMR Records" />
                    <SidebarLink href="/dashboard/reports" icon={<BarChart3 />} label="Reports" />
                    <SidebarLink href="/dashboard/settings" icon={<Settings />} label="Settings" />
                </div>

                <div className="p-4 border-t border-slate-100 dark:border-slate-800">
                    <Link href="/login">
                        <Button variant="ghost" className="w-full justify-start text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10">
                            <LogOut className="h-4 w-4 mr-2" />
                            Sign Out
                        </Button>
                    </Link>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden">
                {/* Top Header (Mobile only menu trigger would go here) */}
                <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-6 md:hidden">
                    <span className="font-bold">Menu</span>
                </header>

                <div className="flex-1 overflow-y-auto p-6">
                    {children}
                </div>
            </main>
        </div>
    );
}

function SidebarLink({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
    const pathname = usePathname();
    const isActive = pathname === href || pathname.startsWith(`${href}/`);

    return (
        <Link href={href}>
            <Button
                variant={isActive ? "secondary" : "ghost"}
                className={`w-full justify-start mb-1 ${isActive
                        ? "bg-primary/10 text-primary hover:bg-primary/20"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                    }`}
            >
                <span className="mr-3 h-5 w-5">{icon}</span>
                {label}
            </Button>
        </Link>
    );
}
