"use client";

import { Button } from "@/components/ui/button";
import { FileText, Save, Stethoscope, Pill, History } from "lucide-react";
import { useState } from "react";

export default function DoctorEMR() {
    const [activeTab, setActiveTab] = useState<'diagnosis' | 'prescription' | 'history'>('diagnosis');

    return (
        <div className="flex h-[calc(100vh-8rem)] gap-6">
            {/* Patient Sidebar */}
            <div className="w-80 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 flex flex-col gap-6">
                <div className="text-center">
                    <div className="h-20 w-20 bg-slate-100 dark:bg-slate-800 rounded-full mx-auto mb-4 flex items-center justify-center text-2xl font-bold text-slate-500">
                        JD
                    </div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">John Doe</h2>
                    <p className="text-sm text-slate-500">Male • 32 Years • PID: 10234</p>
                </div>

                <div className="space-y-4">
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <span className="text-xs text-blue-600 font-bold uppercase">Allergies</span>
                        <p className="text-sm font-medium">Penicillin, Peanuts</p>
                    </div>
                    <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <span className="text-xs text-red-600 font-bold uppercase">Chronic Conditions</span>
                        <p className="text-sm font-medium">Hypertension</p>
                    </div>
                </div>

                <div className="mt-auto">
                    <Button className="w-full" variant="outline">View Full History</Button>
                </div>
            </div>

            {/* Main EMR Area */}
            <div className="flex-1 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden">
                {/* Tabs */}
                <div className="flex border-b border-slate-200 dark:border-slate-800">
                    <button
                        onClick={() => setActiveTab('diagnosis')}
                        className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activeTab === 'diagnosis' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800'}`}
                    >
                        <Stethoscope className="h-4 w-4" /> Diagnosis & Vitals
                    </button>
                    <button
                        onClick={() => setActiveTab('prescription')}
                        className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activeTab === 'prescription' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800'}`}
                    >
                        <Pill className="h-4 w-4" /> Prescription
                    </button>
                    <button
                        onClick={() => setActiveTab('history')}
                        className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activeTab === 'history' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-800'}`}
                    >
                        <History className="h-4 w-4" /> Past Visits
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 flex-1 overflow-y-auto">
                    {activeTab === 'diagnosis' && (
                        <div className="space-y-6 animate-fade-in">
                            <div className="grid grid-cols-4 gap-4">
                                <InputGroup label="BP (mmHg)" placeholder="120/80" />
                                <InputGroup label="Pulse (bpm)" placeholder="72" />
                                <InputGroup label="Temp (°F)" placeholder="98.6" />
                                <InputGroup label="SpO2 (%)" placeholder="99" />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Chief Complaints</label>
                                <textarea className="w-full h-32 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 p-4 outline-none focus:ring-2 focus:ring-primary" placeholder="Enter patient complaints..."></textarea>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Provisional Diagnosis</label>
                                <input type="text" className="w-full h-12 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-4 outline-none focus:ring-2 focus:ring-primary" placeholder="e.g. Viral Fever" />
                            </div>
                        </div>
                    )}

                    {activeTab === 'prescription' && (
                        <div className="space-y-6 animate-fade-in">
                            <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                                <h3 className="font-semibold mb-4">Add Medicine</h3>
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                                    <input type="text" placeholder="Medicine Name" className="col-span-2 h-10 rounded-lg border border-slate-200 px-3 text-sm" />
                                    <select className="h-10 rounded-lg border border-slate-200 px-3 text-sm">
                                        <option>1-0-1</option>
                                        <option>1-1-1</option>
                                        <option>0-1-0</option>
                                    </select>
                                    <input type="text" placeholder="Duration (Days)" className="h-10 rounded-lg border border-slate-200 px-3 text-sm" />
                                </div>
                                <Button size="sm" variant="secondary">Add to List</Button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer actions */}
                <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                    <Button variant="ghost">Cancel</Button>
                    <Button className="bg-primary hover:bg-primary/90 text-white">
                        <Save className="mr-2 h-4 w-4" /> Save Record
                    </Button>
                </div>
            </div>
        </div>
    );
}

function InputGroup({ label, placeholder }: { label: string, placeholder: string }) {
    return (
        <div className="space-y-1">
            <label className="text-xs font-medium text-slate-500 uppercase">{label}</label>
            <input type="text" placeholder={placeholder} className="w-full h-10 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-3 outline-none focus:ring-2 focus:ring-primary" />
        </div>
    );
}
