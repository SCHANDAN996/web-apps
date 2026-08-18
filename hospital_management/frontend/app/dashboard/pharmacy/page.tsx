import { Button } from "@/components/ui/button";
import { Plus, Search, ShoppingCart, Trash2 } from "lucide-react";

export default function PharmacyPOS() {
    return (
        <div className="h-[calc(100vh-8rem)] flex gap-6">
            {/* Left: Product List */}
            <div className="flex-1 flex flex-col gap-4">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Pharmacy POS</h1>

                {/* Search */}
                <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                    <div className="relative">
                        <Search className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
                        <input type="text" placeholder="Search medicines by name or generic..." className="w-full pl-10 h-11 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 focus:ring-2 focus:ring-primary outline-none" />
                    </div>
                </div>

                {/* Medicines Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto pb-4">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                        <div key={i} className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-primary cursor-pointer transition-colors group">
                            <div className="flex justify-between items-start mb-2">
                                <div className="h-10 w-10 bg-blue-50 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600 font-bold text-xs">
                                    TAB
                                </div>
                                <span className="text-xs font-mono text-slate-400">#MED00{i}</span>
                            </div>
                            <h3 className="font-semibold text-slate-900 dark:text-white">Paracetamol 500mg</h3>
                            <p className="text-xs text-slate-500 mb-3">Batch: A202 • Exp: 2027</p>
                            <div className="flex items-center justify-between">
                                <span className="font-bold text-lg">₹ 24.00</span>
                                <Button size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"><Plus className="h-4 w-4" /></Button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right: Cart */}
            <div className="w-96 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col shadow-xl">
                <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
                    <ShoppingCart className="text-primary" />
                    <h2 className="font-bold text-lg">Current Bill</h2>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                    {[1, 2].map((i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                            <div>
                                <h4 className="font-medium text-sm">Paracetamol 500mg</h4>
                                <div className="text-xs text-slate-500">2 strips x ₹ 24</div>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="font-bold text-sm">₹ 48</span>
                                <button className="text-red-400 hover:text-red-500"><Trash2 className="h-4 w-4" /></button>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="p-6 bg-slate-50 dark:bg-slate-800/20 border-t border-slate-100 dark:border-slate-800 space-y-4">
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Subtotal</span>
                        <span>₹ 96.00</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Tax (18%)</span>
                        <span>₹ 17.28</span>
                    </div>
                    <div className="flex justify-between text-xl font-bold border-t border-slate-200 dark:border-slate-700 pt-4">
                        <span>Total</span>
                        <span>₹ 113.28</span>
                    </div>
                    <Button className="w-full h-12 text-lg">Checkout & Print</Button>
                </div>
            </div>
        </div>
    );
}
