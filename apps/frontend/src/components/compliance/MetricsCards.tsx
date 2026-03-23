'use client';

import { Card, CardContent } from '@/components/ui/card';
import { BarChart3, Users2, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricsCardsProps {
  totalEvents: number;
  activeUsers: number;
  topAction?: { action: string; count: number };
  isLoading?: boolean;
}

export function MetricsCards({
  totalEvents,
  activeUsers,
  topAction,
  isLoading = false
}: MetricsCardsProps) {
  const StatCard = ({ title, value, icon: Icon, subtext }: any) => (
    <Card className="border-4 border-black shadow-brutal hover:shadow-brutal-lg transition-all h-full">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <p className="text-xs font-bold uppercase text-gray-600 mb-2">{title}</p>
            <p className="text-4xl font-bold tracking-tight">{isLoading ? '-' : value}</p>
            {subtext && <p className="text-xs text-gray-500 mt-2">{subtext}</p>}
          </div>
          <div className="p-3 border-2 border-black bg-orange-500 shadow-brutal">
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard
        title="Total Events"
        value={totalEvents}
        icon={BarChart3}
        subtext="Last 30 days"
      />
      <StatCard
        title="Active Users"
        value={activeUsers}
        icon={Users2}
        subtext="Unique users"
      />
      <StatCard
        title="Top Action"
        value={topAction?.count || 0}
        icon={TrendingUp}
        subtext={topAction?.action || 'No data'}
      />
    </div>
  );
}
