"use client";

import { useEffect, useState } from "react";

export default function QueueDisplay() {
    const [currentToken, setCurrentToken] = useState(104);
    const [waiting, setWaiting] = useState([105, 106, 107, 108]);

    // Mock real-time update
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentToken(prev => prev + 1);
            setWaiting(prev => prev.map(n => n + 1));
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen bg-black text-white flex overflow-hidden">
            {/* Main Token Display (70% width) */}
            <div className="w-[70%] flex flex-col items-center justify-center border-r border-slate-800 bg-slate-900 relative">
                <div className="absolute top-8 left-8 flex items-center gap-4">
                    <div className="h-16 w-16 bg-primary rounded-xl flex items-center justify-center">
                        <span className="font-bold text-3xl">V</span>
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight">OPD - General Medicine</h1>
                </div>

                <div className="text-center space-y-8 animate-pulse">
                    <h2 className="text-6xl font-medium text-slate-400">Now Serving</h2>
                    <div className="text-[15rem] font-bold text-primary leading-none tracking-tighter">
                        {currentToken}
                    </div>
                    <div className="text-4xl text-white bg-slate-800 px-8 py-4 rounded-full inline-block">
                        Room No. 12
                    </div>
                </div>
            </div>

            {/* Up Next List (30% width) */}
            <div className="w-[30%] bg-slate-950 flex flex-col">
                <div className="p-8 bg-primary/10 border-b border-slate-800">
                    <h2 className="text-3xl font-bold text-primary">Up Next</h2>
                </div>
                <div className="flex-1 overflow-hidden">
                    {waiting.map((token, index) => (
                        <div key={token} className="p-8 border-b border-slate-900 flex items-center gap-6">
                            <span className="h-12 w-12 rounded-full bg-slate-800 flex items-center justify-center text-xl font-bold text-slate-500">
                                {index + 1}
                            </span>
                            <span className="text-6xl font-bold text-slate-300">
                                {token}
                            </span>
                        </div>
                    ))}
                </div>
                <div className="p-6 bg-slate-900 text-center text-slate-500">
                    Vishwakarma HMS • Standard Time 11:42 AM
                </div>
            </div>
        </div>
    );
}
