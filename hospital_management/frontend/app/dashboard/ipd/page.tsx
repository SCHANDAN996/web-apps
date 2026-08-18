"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export default function IPDDashboard() {
    // Mock data for wards
    const [selectedWard, setSelectedWard] = useState("General Ward A");

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">IPD Bed Management</h1>
                <div className="flex gap-2">
                    {["General Ward A", "General Ward B", "ICU", "Private Rooms"].map((ward) => (
                        <Button
                            key={ward}
                            variant={selectedWard === ward ? "default" : "outline"}
                            onClick={() => setSelectedWard(ward)}
                            size="sm"
                        >
                            {ward}
                        </Button>
                    ))}
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <h2 className="text-lg font-semibold mb-6 flex justify-between items-center">
                    <span>{selectedWard} Layout</span>
                    <div className="flex gap-4 text-xs font-medium">
                        <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-full bg-green-500"></span> Available</span>
                        <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-full bg-red-500"></span> Occupied</span>
                        <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-full bg-yellow-500"></span> Maintenance</span>
                    </div>
                </h2>

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {Array.from({ length: 24 }).map((_, i) => {
                        // Mock status logic
                        const status = i % 3 === 0 ? 'occupied' : i % 7 === 0 ? 'maintenance' : 'available';
                        const color = status === 'occupied' ? 'bg-red-500/10 border-red-500 text-red-600' :
                            status === 'maintenance' ? 'bg-yellow-500/10 border-yellow-500 text-yellow-600' :
                                'bg-green-500/10 border-green-500 text-green-600 hover:bg-green-500/20 cursor-pointer';

                        return (
                            <div key={i} className={`h-24 rounded-xl border-2 ${color} flex flex-col items-center justify-center transition-all relative group`}>
                                <span className="font-bold text-lg">Bed {i + 1}</span>
                                <span className="text-xs uppercase font-medium">{status}</span>

                                {status === 'occupied' && (
                                    <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm rounded-lg opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                                        <Button size="sm" variant="secondary" className="h-8 text-xs">View Patient</Button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
