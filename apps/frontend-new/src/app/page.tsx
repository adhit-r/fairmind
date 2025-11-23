'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import ComparisonTable from '@/components/ComparisonTable'

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="py-20 px-4 text-center bg-orange-50 border-b-2 border-black">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 text-black">
            FairMind
          </h1>
          <p className="text-xl md:text-2xl text-gray-700 mb-8">
            Ensuring Fairness and Transparency in AI Models
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/dashboard">
              <Button size="lg" className="text-lg px-8">
                Go to Dashboard
              </Button>
            </Link>
            <Link href="https://github.com/adhit-r/fairmind" target="_blank">
              <Button variant="neutral" size="lg" className="text-lg px-8">
                View on GitHub
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto">
          <ComparisonTable />
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-gray-500 border-t-2 border-black mt-12">
        <p>© {new Date().getFullYear()} FairMind. All rights reserved.</p>
      </footer>
    </main>
  )
}
