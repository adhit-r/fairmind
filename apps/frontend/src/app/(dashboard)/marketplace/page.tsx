'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
    IconSearch,
    IconFilter,
    IconStar,
    IconDownload,
    IconShieldCheck,
    IconBrain,
    IconTag
} from '@tabler/icons-react';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '@/components/ui/select';
import { marketplaceService, MarketplaceModel } from '@/services/marketplace-service';
import { toast } from 'sonner';

export default function MarketplacePage() {
    const router = useRouter();
    const [models, setModels] = useState<MarketplaceModel[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedFramework, setSelectedFramework] = useState<string>('all');
    const [selectedTask, setSelectedTask] = useState<string>('all');

    useEffect(() => {
        fetchModels();
    }, [searchQuery, selectedFramework, selectedTask]);

    const fetchModels = async () => {
        try {
            setLoading(true);
            const params: any = {};
            if (searchQuery) params.q = searchQuery;
            if (selectedFramework !== 'all') params.framework = selectedFramework;
            if (selectedTask !== 'all') params.task = selectedTask;

            const response = await marketplaceService.listModels(params);
            setModels(response.models);
        } catch (error) {
            console.error('Error fetching models:', error);
            toast.error('Failed to load models');
        } finally {
            setLoading(false);
        }
    };

    const getBiasScoreColor = (score: number) => {
        if (score >= 0.9) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100';
        if (score >= 0.7) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100';
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100';
    };

    return (
        <div className="space-y-6 p-6">
            <div className="flex flex-col space-y-2">
                <h1 className="text-3xl font-bold tracking-tight">Model Marketplace</h1>
                <p className="text-muted-foreground">
                    Discover, share, and evaluate models with verified fairness metrics.
                </p>
            </div>

            {/* Search and Filters */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <IconSearch className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search models, authors, or descriptions..."
                        className="pl-9"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <Select value={selectedFramework} onValueChange={setSelectedFramework}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Framework" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Frameworks</SelectItem>
                        <SelectItem value="PyTorch">PyTorch</SelectItem>
                        <SelectItem value="TensorFlow">TensorFlow</SelectItem>
                        <SelectItem value="JAX">JAX</SelectItem>
                    </SelectContent>
                </Select>
                <Select value={selectedTask} onValueChange={setSelectedTask}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Task" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Tasks</SelectItem>
                        <SelectItem value="Text Generation">Text Generation</SelectItem>
                        <SelectItem value="Image Classification">Image Classification</SelectItem>
                        <SelectItem value="Fill-Mask">Fill-Mask</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Model Grid */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <Card key={i} className="animate-pulse h-[300px]" />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {models.map((model) => (
                        <Card
                            key={model.model_id}
                            className="flex flex-col hover:shadow-lg transition-shadow cursor-pointer"
                            onClick={() => router.push(`/marketplace/${model.model_id}`)}
                        >
                            <CardHeader>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <CardTitle className="text-xl">{model.name}</CardTitle>
                                        <CardDescription className="mt-1">by {model.author}</CardDescription>
                                    </div>
                                    <Badge variant="outline" className={getBiasScoreColor(model.bias_card.overall_score)}>
                                        <IconShieldCheck className="mr-1 h-3 w-3" />
                                        {Math.round(model.bias_card.overall_score * 100)}% Fair
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="flex-1">
                                <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                                    {model.description}
                                </p>
                                <div className="flex flex-wrap gap-2 mb-4">
                                    <Badge variant="secondary" className="text-xs">
                                        <IconBrain className="mr-1 h-3 w-3" />
                                        {model.framework}
                                    </Badge>
                                    <Badge variant="secondary" className="text-xs">
                                        <IconTag className="mr-1 h-3 w-3" />
                                        {model.task}
                                    </Badge>
                                </div>
                                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                                    <div className="flex items-center">
                                        <IconStar className="mr-1 h-4 w-4 text-yellow-500" />
                                        {model.reviews.length > 0
                                            ? (model.reviews.reduce((a, b) => a + b.rating, 0) / model.reviews.length).toFixed(1)
                                            : 'N/A'}
                                    </div>
                                    <div className="flex items-center">
                                        <IconDownload className="mr-1 h-4 w-4" />
                                        {model.download_count}
                                    </div>
                                </div>
                            </CardContent>
                            <CardFooter className="bg-muted/50 p-4">
                                <Button className="w-full" variant="neutral">
                                    View Details
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            )}

            {!loading && models.length === 0 && (
                <div className="text-center py-12">
                    <p className="text-muted-foreground">No models found matching your criteria.</p>
                </div>
            )}
        </div>
    );
}
