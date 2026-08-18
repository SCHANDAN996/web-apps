"use client";

import { Button } from "@/components/ui/button";
import { Plus, Search } from "lucide-react";

export default function ReceptionDashboard() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Reception Desk</h1>
                <Button>
                    <Plus className="mr-2 h-4 w-4" /> New Patient Registration
                </Button>
            </div>

            {/* Search Bar */}
            <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <div className="relative">
                    <Search className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search by Patient Name, ID, or Mobile Number..."
                        className="w-full pl-10 h-11 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                    />
                </div>
            </div>

            {/* Recent Registrations Table */}
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-200 dark:border-slate-800">
                    <h2 className="font-semibold text-slate-900 dark:text-white">Recent Registrations</h2>
                </div>
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 uppercase text-xs">
                        <tr>
                            <th className="px-6 py-3">Patient ID</th>
                            <th className="px-6 py-3">Name</th>
                            <th className="px-6 py-3">Age/Gender</th>
                            <th className="px-6 py-3">Contact</th>
                            <th className="px-6 py-3">Department</th>
                            <th className="px-6 py-3">Status</th>
                            <th className="px-6 py-3">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {[1, 2, 3].map((i) => (
                            <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                                <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">UHID-{2000 + i}</td>
                                <td className="px-6 py-4">Amit Kumar</td>
                                <td className="px-6 py-4">2{i} / M</td>
                                <td className="px-6 py-4">+91 9876543210</td>
                                <td className="px-6 py-4">Cardiology</td>
                                <td className="px-6 py-4"><span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">Checked In</span></td>
                                <td className="px-6 py-4"><Button variant="ghost" size="sm">View</Button></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
