import { Button } from "@/components/ui/button";
import { ArrowRight, Activity, Calendar, Shield, Users } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden bg-slate-50 dark:bg-slate-950">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center lg:text-left flex flex-col lg:flex-row items-center gap-12">
          {/* Text Content */}
          <div className="lg:w-1/2 space-y-8 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              #1 Digital Health Platform
            </div>
            <h1 className="text-4xl lg:text-7xl font-bold tracking-tight text-slate-900 dark:text-white">
              Healthcare <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-teal-600">
                Reimagined
              </span>
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
              Experience the future of hospital management. From instant appointments to real-time health tracking, Vishwakarma brings world-class care to your fingertips.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Link href="/book-appointment">
                <Button size="lg" className="h-12 px-8 text-base shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all">
                  Book Appointment <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link href="/doctors">
                <Button variant="outline" size="lg" className="h-12 px-8 text-base bg-white/50 backdrop-blur-sm">
                  Find a Doctor
                </Button>
              </Link>
            </div>
          </div>

          {/* Hero Visual */}
          <div className="lg:w-1/2 relative">
            <div className="relative h-[400px] w-full lg:h-[600px] bg-gradient-to-br from-primary/20 to-teal-500/20 rounded-[2rem] p-8 border border-white/20 backdrop-blur-3xl shadow-2xl animate-fade-in">
              {/* Abstract Medical UI Representation */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-6 w-[80%] max-w-sm border border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-4 mb-6">
                  <div className="h-12 w-12 bg-primary/10 rounded-full flex items-center justify-center text-primary">
                    <Activity className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">Health Status</h3>
                    <p className="text-sm text-green-500">Excellent</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[75%] rounded-full"></div>
                  </div>
                  <div className="flex justify-between text-sm text-slate-500">
                    <span>Heart Rate</span>
                    <span className="font-medium text-slate-900 dark:text-white">72 BPM</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">Why Choose Vishwakarma?</h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              Our integrated platform focuses on patient experience, clinical excellence, and operational efficiency.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Calendar className="h-8 w-8 text-primary" />}
              title="Instant Booking"
              description="Book appointments in less than 60 seconds with our smart scheduling system."
            />
            <FeatureCard
              icon={<Shield className="h-8 w-8 text-primary" />}
              title="Secure Records"
              description="Your medical history is encrypted and safe, accessible only to you and your doctors."
            />
            <FeatureCard
              icon={<Users className="h-8 w-8 text-primary" />}
              title="Top Specialists"
              description="Connect with India's leading medical experts across 30+ specialities."
            />
          </div>
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-8 rounded-2xl bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 hover:shadow-lg transition-shadow group">
      <div className="mb-4 bg-white dark:bg-slate-900 p-4 rounded-xl inline-block shadow-sm group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2 text-slate-900 dark:text-white">{title}</h3>
      <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}
