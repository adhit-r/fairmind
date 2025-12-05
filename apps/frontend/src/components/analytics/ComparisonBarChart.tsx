'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/card';

interface ComparisonBarChartProps {
    data: any[];
}

export function ComparisonBarChart({ data }: ComparisonBarChartProps) {
    return (
        <Card className="p-6 h-[400px] border-2 border-black shadow-brutal">
            <h3 className="text-lg font-bold mb-4">Model Comparison</h3>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip
                        contentStyle={{ border: '2px solid black', borderRadius: '0px' }}
                    />
                    <Legend />
                    <Bar dataKey="demographic_parity" fill="#8884d8" name="Demographic Parity" />
                    <Bar dataKey="equal_opportunity" fill="#82ca9d" name="Equal Opportunity" />
                    <Bar dataKey="overall_fairness" fill="#000000" name="Overall Fairness" />
                </BarChart>
            </ResponsiveContainer>
        </Card>
    );
}
