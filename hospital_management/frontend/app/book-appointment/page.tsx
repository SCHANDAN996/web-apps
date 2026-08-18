"use client";

import { Button } from "@/components/ui/button";
import { Calendar, Clock, User, Stethoscope } from "lucide-react";
import { useState } from "react";

export default function BookAppointment() {
    const [step, setStep] = useState(1);

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pt-24 pb-12 px-4">
            <div className="max-w-3xl mx-auto">
                <div className="text-center mb-10 animate-fade-in">
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Book Your Appointment</h1>
                    <p className="text-slate-600 dark:text-slate-400">Skip the queue. Get confirmed consultation in 3 easy steps.</p>
                </div>

                {/* Progress Steps */}
                <div className="flex justify-between mb-8 relative">
                    <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-200 dark:bg-slate-800 -z-10"></div>
                    {[1, 2, 3].map((i) => (
                        <div key={i} className={`h-10 w-10 rounded-full flex items-center justify-center font-bold transition-colors ${step >= i ? 'bg-primary text-white' : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-400'}`}>
                            {i}
                        </div>
                    ))}
                </div>

                <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-800 p-8 animate-fade-in">
                    {step === 1 && (
                        <div className="space-y-6">
                            <h2 className="text-xl font-semibold flex items-center gap-2">
                                <Stethoscope className="text-primary" /> Select Department & Doctor
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <select className="w-full h-12 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 focus:ring-2 focus:ring-primary outline-none">
                                    <option>Select Department</option>
                                    <option>Cardiology</option>
                                    <option>Neurology</option>
                                    <option>Orthopedics</option>
                                    <option>General Medicine</option>
                                </select>
                                <select className="w-full h-12 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 focus:ring-2 focus:ring-primary outline-none">
                                    <option>Select Doctor</option>
                                    <option>Dr. Sharma (Cardio)</option>
                                    <option>Dr. Verma (Neuro)</option>
                                </select>
                            </div>
                            <Button onClick={() => setStep(2)} className="w-full h-12 text-lg">Next Step</Button>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-6 animate-fade-in">
                            <h2 className="text-xl font-semibold flex items-center gap-2">
                                <Calendar className="text-primary" /> Select Date & Time
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <input type="date" className="w-full h-12 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 focus:ring-2 focus:ring-primary outline-none" />
                                <div className="grid grid-cols-3 gap-2">
                                    {["10:00", "10:30", "11:00", "11:30", "12:00", "12:30"].map((time) => (
                                        <button key={time} className="py-2 rounded-lg border border-slate-200 hover:border-primary hover:bg-primary/5 text-sm transition-colors focus:ring-1 ring-primary">
                                            {time}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex gap-4">
                                <Button variant="outline" onClick={() => setStep(1)} className="w-1/2 h-12 text-lg">Back</Button>
                                <Button onClick={() => setStep(3)} className="w-1/2 h-12 text-lg">Next Step</Button>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-6 animate-fade-in">
                            <h2 className="text-xl font-semibold flex items-center gap-2">
                                <User className="text-primary" /> Patient Details
                            </h2>
                            <div className="space-y-4">
                                <input type="text" placeholder="Full Name" className="w-full h-12 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 focus:ring-2 focus:ring-primary outline-none" />
                                <div className="grid grid-cols-2 gap-4">
                                    <input type="tel" placeholder="Mobile Number" className="w-full h-12 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 focus:ring-2 focus:ring-primary outline-none" />
                                    <input type="number" placeholder="Age" className="w-full h-12 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 focus:ring-2 focus:ring-primary outline-none" />
                                </div>
                            </div>
                            <div className="flex gap-4">
                                <Button variant="outline" onClick={() => setStep(2)} className="w-1/2 h-12 text-lg">Back</Button>
                                <Button className="w-1/2 h-12 text-lg bg-green-600 hover:bg-green-700">Confirm Booking</Button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
