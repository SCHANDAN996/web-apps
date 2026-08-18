"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Activity, Menu, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export function Navbar() {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <nav className="fixed w-full z-50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    {/* Logo */}
                    <div className="flex-shrink-0 flex items-center gap-2">
                        <div className="bg-primary/10 p-2 rounded-lg text-primary">
                            <Activity className="h-6 w-6" />
                        </div>
                        <span className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">
                            Vishwakarma<span className="text-primary">HMS</span>
                        </span>
                    </div>

                    {/* Desktop Menu */}
                    <div className="hidden md:flex space-x-8 items-center">
                        <NavLink href="#features">Features</NavLink>
                        <NavLink href="#doctors">Find Doctors</NavLink>
                        <NavLink href="#departments">Departments</NavLink>
                        <div className="flex gap-4 ml-4">
                            <Link href="/login">
                                <Button variant="ghost">Login</Button>
                            </Link>
                            <Link href="/book-appointment">
                                <Button>Book Appointment</Button>
                            </Link>
                        </div>
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="md:hidden flex items-center">
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="text-gray-700 dark:text-gray-300 hover:text-primary transition-colors"
                        >
                            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu */}
            {isOpen && (
                <div className="md:hidden bg-white dark:bg-slate-950 border-t border-gray-100 dark:border-gray-800 absolute w-full animate-fade-in shadow-lg">
                    <div className="px-4 pt-2 pb-6 space-y-2">
                        <MobileNavLink href="#features">Features</MobileNavLink>
                        <MobileNavLink href="#doctors">Find Doctors</MobileNavLink>
                        <MobileNavLink href="#departments">Departments</MobileNavLink>
                        <div className="pt-4 flex flex-col gap-3">
                            <Link href="/login" className="w-full">
                                <Button variant="outline" className="w-full justify-center">Login</Button>
                            </Link>
                            <Link href="/book-appointment" className="w-full">
                                <Button className="w-full justify-center">Book Appointment</Button>
                            </Link>
                        </div>
                    </div>
                </div>
            )}
        </nav>
    );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
    return (
        <Link
            href={href}
            className="text-gray-600 dark:text-gray-300 hover:text-primary font-medium transition-colors text-sm"
        >
            {children}
        </Link>
    );
}

function MobileNavLink({ href, children }: { href: string; children: React.ReactNode }) {
    return (
        <Link
            href={href}
            className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-200 hover:text-primary hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
        >
            {children}
        </Link>
    );
}
