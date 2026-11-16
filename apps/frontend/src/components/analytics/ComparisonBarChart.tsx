'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/card';
import { chartTheme, seriesColor } from '@/lib/chart-theme';

interface ComparisonBarChartProps {
    data: any[];
}

export function ComparisonBarChart({ data }: ComparisonBarChartProps) {
    return (
        <Card className="h-[400px] p-4 sm:p-5">
            <h3 className="mb-4 text-base font-semibold">Model Comparison</h3>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                    <CartesianGrid {...chartTheme.gridProps} />
                    <XAxis dataKey="name" {...chartTheme.axisProps} />
                    <YAxis domain={[0, 1]} {...chartTheme.axisProps} />
                    <Tooltip {...chartTheme.tooltipProps} />
                    <Legend {...chartTheme.legendProps} />
                    <Bar dataKey="demographic_parity" fill={seriesColor(0)} name="Demographic Parity" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="equal_opportunity" fill={seriesColor(2)} name="Equal Opportunity" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="overall_fairness" fill={seriesColor(3)} name="Overall Fairness" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </Card>
    );
}
