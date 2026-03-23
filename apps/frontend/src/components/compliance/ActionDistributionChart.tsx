'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';

interface ActionDistributionChartProps {
  data: Array<{ action: string; count: number }>;
  onActionClick?: (action: string) => void;
  isLoading?: boolean;
}

const COLORS = ['#FF6B35', '#00796B', '#F57C00', '#C62828', '#6A1B9A'];

export function ActionDistributionChart({
  data,
  onActionClick,
  isLoading = false
}: ActionDistributionChartProps) {
  return (
    <Card className="border-4 border-black shadow-brutal">
      <CardHeader className="border-b-4 border-black">
        <CardTitle className="text-lg font-bold tracking-tight">ACTION DISTRIBUTION</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        {isLoading ? (
          <div className="h-80 flex items-center justify-center text-gray-500">
            Loading chart...
          </div>
        ) : data.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-gray-500">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ action, count }) => `${action}: ${count}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
                onClick={(entry: any) => onActionClick?.(entry.action)}
                style={{ cursor: 'pointer' }}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '2px solid #000',
                  boxShadow: '6px 6px 0 rgba(0, 0, 0, 0.15)',
                }}
                formatter={(value: any) => `${value} events`}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
        {data.length > 0 && (
          <p className="text-xs text-gray-500 mt-4 text-center">
            Click on a slice to filter the audit log table
          </p>
        )}
      </CardContent>
    </Card>
  );
}
