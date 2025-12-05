import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { IconDna, IconBinary, IconDatabase, IconAdjustments } from '@tabler/icons-react';
import { ModelDNA } from '@/lib/api/model-dna-service';

interface DNAProfileProps {
    dna: ModelDNA;
}

export default function DNAProfile({ dna }: DNAProfileProps) {
    return (
        <Card className="border-2 border-black shadow-brutal h-full">
            <CardHeader>
                <div className="flex justify-between items-start">
                    <CardTitle className="flex items-center gap-2">
                        <IconDna className="text-purple-600" />
                        Model DNA Profile
                    </CardTitle>
                    <Badge variant="outline" className="font-mono">
                        Gen {dna.generation}
                    </Badge>
                </div>
                <div className="font-mono text-xs text-muted-foreground bg-gray-100 p-2 rounded mt-2 break-all">
                    {dna.dna_id}
                </div>
            </CardHeader>

            <CardContent className="space-y-6">
                {/* Genes */}
                <div className="space-y-3">
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">Genetic Markers</h3>

                    <div className="flex items-center gap-3 p-2 bg-purple-50 rounded-lg border border-purple-100">
                        <div className="p-2 bg-purple-100 rounded text-purple-700">
                            <IconBinary size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-purple-900">Architecture Genes</div>
                            <div className="text-xs font-mono text-purple-700 truncate">{dna.architecture_genes}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 p-2 bg-blue-50 rounded-lg border border-blue-100">
                        <div className="p-2 bg-blue-100 rounded text-blue-700">
                            <IconDatabase size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-blue-900">Data Lineage Genes</div>
                            <div className="text-xs font-mono text-blue-700 truncate">{dna.data_genes}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 p-2 bg-orange-50 rounded-lg border border-orange-100">
                        <div className="p-2 bg-orange-100 rounded text-orange-700">
                            <IconAdjustments size={18} />
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-orange-900">Training Genes</div>
                            <div className="text-xs font-mono text-orange-700 truncate">{dna.training_genes}</div>
                        </div>
                    </div>
                </div>

                {/* Bias Profile */}
                <div className="space-y-3">
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">Bias Profile</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-gray-50 rounded border">
                            <div className="text-xs text-muted-foreground">Overall Score</div>
                            <div className={`text-xl font-bold ${dna.bias_profile.overall_bias_score < 0.1 ? 'text-green-600' : 'text-red-600'
                                }`}>
                                {dna.bias_profile.overall_bias_score.toFixed(3)}
                            </div>
                        </div>
                        <div className="p-3 bg-gray-50 rounded border">
                            <div className="text-xs text-muted-foreground">Detected Biases</div>
                            <div className="text-xl font-bold">
                                {dna.bias_profile.detected_biases.length}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Ancestry */}
                <div className="space-y-3">
                    <h3 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">Ancestry</h3>
                    <div className="text-sm">
                        <span className="text-muted-foreground">Direct Ancestors: </span>
                        <span className="font-medium">{dna.ancestors.length} models</span>
                    </div>
                    {dna.ancestors.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {dna.ancestors.slice(0, 5).map(id => (
                                <Badge key={id} variant="secondary" className="text-xs font-mono">
                                    {id}
                                </Badge>
                            ))}
                            {dna.ancestors.length > 5 && (
                                <Badge variant="outline" className="text-xs">
                                    +{dna.ancestors.length - 5} more
                                </Badge>
                            )}
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
