'use client';

import { useState, useEffect } from 'react';
import { analyticsService } from '@/lib/api/analytics-service';
import { TrendLineChart } from '@/components/analytics/TrendLineChart';
import { ComparisonBarChart } from '@/components/analytics/ComparisonBarChart';
import { BiasHeatmap } from '@/components/analytics/BiasHeatmap';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import { useModels } from '@/lib/api/hooks/useModels';
import { toast } from 'sonner';
import { IconBrain } from '@tabler/icons-react';

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [trends, setTrends] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [heatmap, setHeatmap] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState<string>('');

  const { data: models, loading: modelsLoading } = useModels();

  // Set default model when models are loaded
  useEffect(() => {
    if (models.length > 0 && !selectedModel) {
      setSelectedModel(models[0].id);
    }
  }, [models, selectedModel]);

  useEffect(() => {
    const fetchData = async () => {
      if (!selectedModel) {
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        // For comparison, we'll just compare the selected model with itself for now if no others,
        // or pick top 3 models if available.
        const comparisonIds = models.length > 0
          ? models.slice(0, 3).map(m => m.id)
          : [selectedModel];

        const [trendsRes, comparisonRes, heatmapRes] = await Promise.all([
          analyticsService.getTrends(selectedModel),
          analyticsService.compareModels(comparisonIds),
          analyticsService.getHeatmap(selectedModel)
        ]);

        if (trendsRes.success && trendsRes.data) setTrends(trendsRes.data);
        if (comparisonRes.success && comparisonRes.data) setComparison(comparisonRes.data);
        if (heatmapRes.success && heatmapRes.data) setHeatmap(heatmapRes.data);

      } catch (error) {
        console.error("Failed to fetch analytics:", error);
        toast.error("Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedModel, models]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 p-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold">Advanced Analytics</h1>
          <p className="text-muted-foreground mt-2">Deep dive into model fairness and performance trends.</p>
        </div>
        <Select value={selectedModel} onValueChange={setSelectedModel} disabled={modelsLoading || models.length === 0}>
          <SelectTrigger className="w-[250px] border-2 border-black">
            <SelectValue placeholder={modelsLoading ? "Loading models..." : "Select Model"} />
          </SelectTrigger>
          <SelectContent>
            {models.length === 0 ? (
              <SelectItem value="none" disabled>No models available</SelectItem>
            ) : (
              models.map(model => (
                <SelectItem key={model.id} value={model.id}>{model.name} ({model.version})</SelectItem>
              ))
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {trends && <TrendLineChart data={trends.trends} />}
        {comparison && <ComparisonBarChart data={comparison.comparison} />}
      </div>

      <div className="w-full">
        {heatmap && <BiasHeatmap data={heatmap.heatmap_data} />}
      </div>
    </div>
  );
}
