"use client";

import { Activity, CreditCard, TrendingUp, Users } from "lucide-react";

export default function AdminDashboard() {
    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Hospital Administration</h1>

            {/* Kpi Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <KpiCard title="Total Revenue" value="₹ 4.2 L" change="+12%" icon={<CreditCard className="text-white" />} color="bg-gradient-to-br from-green-500 to-emerald-600" />
                <KpiCard title="Active Patients" value="128" change="+4" icon={<Users className="text-white" />} color="bg-gradient-to-br from-blue-500 to-indigo-600" />
                <KpiCard title="Bed Occupancy" value="85%" change="-2%" icon={<Activity className="text-white" />} color="bg-gradient-to-br from-orange-500 to-red-600" />
                <KpiCard title="Avg. Waiting" value="12m" change="Good" icon={<TrendingUp className="text-white" />} color="bg-gradient-to-br from-purple-500 to-pink-600" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Live Operations */}
                <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                    <h3 className="font-bold text-slate-900 dark:text-white mb-4">Department Load</h3>
                    <div className="space-y-4">
                        <ProgressBar label="OPD (General)" value={78} color="bg-blue-500" />
                        <ProgressBar label="Emergency" value={45} color="bg-red-500" />
                        <ProgressBar label="Laboratory" value={90} color="bg-purple-500" />
                        <ProgressBar label="Pharmacy" value={60} color="bg-green-500" />
                    </div>
                </div>
            </div>
        </div>
    );
}

function KpiCard({ title, value, change, icon, color }: { title: string, value: string, change: string, icon: React.ReactNode, color: string }) {
    return (
        <div className={`p-6 rounded-2xl shadow-lg ${color} text-white`}>
            <div className="flex justify-between items-start mb-4">
                <div>
                    <p className="text-white/80 text-sm font-medium">{title}</p>
                    <h3 className="text-3xl font-bold mt-1">{value}</h3>
                </div>
                <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                    {icon}
                </div>
            </div>
            <div className="flex items-center gap-2 text-sm bg-black/10 w-fit px-2 py-1 rounded-md">
                <span>{change}</span>
                <span className="opacity-70">vs yesterday</span>
            </div>
        </div>
    );
}

function ProgressBar({ label, value, color }: { label: string, value: number, color: string }) {
    return (
        <div>
            <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-slate-700 dark:text-slate-300">{label}</span>
                <span className="text-slate-500">{value}%</span>
            </div>
            <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                <div className={`h-full ${color} rounded-full`} style={{ width: `${value}%` }}></div>
            </div>
        </div>
    );
}
