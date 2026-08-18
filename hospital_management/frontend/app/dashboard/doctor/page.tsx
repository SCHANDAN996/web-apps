import { Button } from "@/components/ui/button";
import { Activity, Clock, Users, CalendarCheck } from "lucide-react";

export default function DoctorDashboard() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Doctor&apos;s Workbench</h1>
                <div className="flex gap-2">
                    <Button variant="outline">Today: Oct 24</Button>
                    <Button>Start OPD</Button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard icon={<Users className="text-blue-500" />} label="Total Patients" value="42" subtext="+12% from yesterday" />
                <StatCard icon={<Clock className="text-orange-500" />} label="Avg Wait Time" value="18m" subtext="-2m improvement" />
                <StatCard icon={<Activity className="text-green-500" />} label="Completed" value="28" subtext="67% of daily goal" />
                <StatCard icon={<CalendarCheck className="text-purple-500" />} label="Appointments" value="14" subtext="Upcoming" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Patient Queue */}
                <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                        <h2 className="font-semibold text-slate-900 dark:text-white">Live Patient Queue</h2>
                        <span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-700 rounded-full">OPD Active</span>
                    </div>
                    <div className="divide-y divide-slate-100 dark:divide-slate-800">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                <div className="flex items-center gap-4">
                                    <div className="h-10 w-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-slate-600 dark:text-slate-400">
                                        {i < 10 ? `0${i}` : i}
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-900 dark:text-white">Patient Name {i}</p>
                                        <p className="text-sm text-slate-500">General Checkup • 24M</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-medium px-2 py-1 bg-blue-50 text-blue-700 rounded-lg">Waiting: 15m</span>
                                    <Button size="sm">Call</Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Next Up / Notices */}
                <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
                    <h2 className="font-semibold text-slate-900 dark:text-white mb-4">Quick Vitals</h2>
                    <div className="space-y-4">
                        <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-100 dark:border-slate-700">
                            <span className="text-xs text-slate-500 uppercase font-bold tracking-wider">Last BP Reading</span>
                            <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">120/80</div>
                            <span className="text-xs text-green-600">Normal Range</span>
                        </div>
                        {/* More widgets can go here */}
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatCard({ icon, label, value, subtext }: { icon: React.ReactNode, label: string, value: string, subtext: string }) {
    return (
        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <div className="h-10 w-10 rounded-lg bg-slate-50 dark:bg-slate-800 flex items-center justify-center">
                    {icon}
                </div>
                <span className="text-xs font-medium text-slate-400">Today</span>
            </div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white mb-1">{value}</div>
            <div className="text-sm text-slate-500">{label}</div>
            <div className="text-xs text-slate-400 mt-2">{subtext}</div>
        </div>
    );
}
