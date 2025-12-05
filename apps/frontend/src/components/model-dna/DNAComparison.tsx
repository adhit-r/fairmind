import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { IconDna, IconGitCompare, IconArrowRight } from '@tabler/icons-react';
import { ModelComparison } from '@/lib/api/model-dna-service';

interface DNAComparisonProps {
    comparison: ModelComparison;
}

export default function DNAComparison({ comparison }: DNAComparisonProps) {
    const { model_1, model_2, similarity_scores, relationship, common_ancestors, divergence_points } = comparison;

    const getScoreColor = (score: number) => {
        if (score >= 0.9) return 'bg-green-500';
        if (score >= 0.7) return 'bg-blue-500';
        if (score >= 0.5) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    const getRelationshipBadge = (rel: string) => {
        switch (rel) {
            case 'identical_twins': return <Badge className="bg-purple-500">Identical Twins</Badge>;
            case 'variants': return <Badge className="bg-blue-500">Variants</Badge>;
            case 'siblings': return <Badge className="bg-green-500">Siblings</Badge>;
            case 'parent-child': return <Badge className="bg-orange-500">Parent-Child</Badge>;
            case 'child-parent': return <Badge className="bg-orange-500">Child-Parent</Badge>;
            default: return <Badge variant="outline">Unrelated</Badge>;
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="text-center">
                        <div className="font-bold text-lg">{model_1.id}</div>
                        <div className="font-mono text-xs text-muted-foreground">{model_1.dna_id.slice(0, 8)}...</div>
                    </div>
                    <IconArrowRight className="text-muted-foreground" />
                    <div className="text-center">
                        <div className="font-bold text-lg">{model_2.id}</div>
                        <div className="font-mono text-xs text-muted-foreground">{model_2.dna_id.slice(0, 8)}...</div>
                    </div>
                </div>

                <div className="flex flex-col items-end">
                    <span className="text-sm text-muted-foreground">Relationship</span>
                    {getRelationshipBadge(relationship)}
                </div>
            </div>

            <Card className="border-2 border-black shadow-brutal">
                <CardHeader className="pb-2">
                    <div className="flex justify-between items-center">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <IconGitCompare size={20} />
                            DNA Similarity Analysis
                        </CardTitle>
                        <div className="text-2xl font-bold">
                            {(similarity_scores.overall * 100).toFixed(1)}%
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-3">
                        {[
                            { label: 'Architecture', score: similarity_scores.architecture },
                            { label: 'Training Data', score: similarity_scores.data },
                            { label: 'Hyperparameters', score: similarity_scores.training },
                            { label: 'Bias Profile', score: similarity_scores.bias_profile },
                            { label: 'Performance', score: similarity_scores.performance },
                        ].map((metric) => (
                            <div key={metric.label} className="space-y-1">
                                <div className="flex justify-between text-sm">
                                    <span>{metric.label}</span>
                                    <span className="font-mono">{(metric.score * 100).toFixed(1)}%</span>
                                </div>
                                <Progress value={metric.score * 100} className="h-2" indicatorClassName={getScoreColor(metric.score)} />
                            </div>
                        ))}
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                        <div>
                            <h4 className="font-semibold text-sm mb-2">Common Ancestors</h4>
                            {common_ancestors.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {common_ancestors.map(id => (
                                        <Badge key={id} variant="secondary" className="font-mono text-xs">
                                            {id}
                                        </Badge>
                                    ))}
                                </div>
                            ) : (
                                <span className="text-sm text-muted-foreground">None found</span>
                            )}
                        </div>
                        <div>
                            <h4 className="font-semibold text-sm mb-2">Divergence Points</h4>
                            {divergence_points.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {divergence_points.map(point => (
                                        <Badge key={point} variant="destructive" className="text-xs">
                                            {point.replace('_', ' ')}
                                        </Badge>
                                    ))}
                                </div>
                            ) : (
                                <span className="text-sm text-muted-foreground">None found</span>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
