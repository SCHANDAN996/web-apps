"use client";

import { Button } from "@/components/ui/button";
import { Beaker, FilePlus, Search } from "lucide-react";

export default function LabDashboard() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Laboratory Management</h1>
                <Button>
                    <FilePlus className="mr-2 h-4 w-4" /> Add Test Request
                </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 dark:bg-slate-800 p-4 rounded-xl border border-blue-100 dark:border-slate-700 flex items-center gap-4">
                    <div className="h-12 w-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600">
                        <Beaker className="h-6 w-6" />
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-900 dark:text-white">24</div>
                        <div className="text-sm text-slate-500">Pending Tests</div>
                    </div>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                    <h2 className="font-semibold text-slate-900 dark:text-white">Sample Collection & Results</h2>
                    <div className="relative w-64">
                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                        <input type="text" placeholder="Search Patient ID..." className="w-full pl-9 h-9 rounded-lg border border-slate-200 dark:border-slate-700 text-sm focus:ring-1 focus:ring-primary outline-none" />
                    </div>
                </div>

                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 uppercase text-xs">
                        <tr>
                            <th className="px-6 py-3">Req ID</th>
                            <th className="px-6 py-3">Patient</th>
                            <th className="px-6 py-3">Test Name</th>
                            <th className="px-6 py-3">Referred By</th>
                            <th className="px-6 py-3">Status</th>
                            <th className="px-6 py-3">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {[1, 2, 3, 4].map((i) => (
                            <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                                <td className="px-6 py-4 font-mono text-xs text-slate-400">#LAB-00{i}</td>
                                <td className="px-6 py-4 font-medium text-slate-900 dark:text-white py-4">Suresh Raina</td>
                                <td className="px-6 py-4">CBC (Complete Blood Count)</td>
                                <td className="px-6 py-4">Dr. Sharma</td>
                                <td className="px-6 py-4">
                                    {i === 1 ? <span className="text-xs font-medium px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full">Sample Collected</span> :
                                        i === 2 ? <span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-700 rounded-full">Processing</span> :
                                            <span className="text-xs font-medium px-2 py-1 bg-gray-100 text-gray-700 rounded-full">Pending</span>
                                    }
                                </td>
                                <td className="px-6 py-4">
                                    <Button size="sm" variant={i === 1 ? "default" : "outline"}>
                                        {i === 1 ? "Enter Result" : "View"}
                                    </Button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
