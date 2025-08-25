"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Progress } from "@/components/ui/common/progress"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/common/tabs"
import { 
  Trophy, 
  Target, 
  TrendingUp, 
  Users, 
  Shield, 
  Bot,
  BarChart3,
  Star,
  Award,
  Zap,
  ArrowRight,
  Calendar,
  Clock,
  CheckCircle,
  AlertTriangle,
  Info,
  Medal,
  Crown,
  Flame
} from "lucide-react"
import { fairmindAPI } from "@/lib/fairmind-api"
import { useAuth } from "@/contexts/auth-context"

interface GovernanceScore {
  overall: number
  categories: {
    bias_detection: number
    security_testing: number
    compliance: number
    documentation: number
  }
  trends: {
    weekly_change: number
    monthly_change: number
  }
  rank: {
    organization: number
    industry: number
    global: number
  }
}

interface Achievement {
  id: string
  title: string
  description: string
  category: 'bias_detection' | 'security' | 'compliance' | 'documentation' | 'simulation'
  difficulty: 'bronze' | 'silver' | 'gold' | 'platinum'
  earned: boolean
  earnedAt?: string
  progress?: number
  target?: number
  reward: {
    points: number
    badge: string
  }
}

interface Challenge {
  id: string
  title: string
  description: string
  duration: 'weekly' | 'monthly' | 'quarterly'
  endDate: string
  objectives: {
    type: string
    target: number
    current: number
    description: string
  }[]
  rewards: {
    points: number
    badge: string
    recognition: string
  }
  progress: number
  status: 'active' | 'completed' | 'expired'
}

interface LeaderboardEntry {
  rank: number
  user: {
    name: string
    avatar?: string
  }
  organization: string
  score: number
  metrics: {
    simulations_completed: number
    average_score: number
    improvements_made: number
  }
  trend: 'up' | 'down' | 'stable'
}

export function GamifiedSimulationDashboard() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [governanceScore, setGovernanceScore] = useState<GovernanceScore>({
    overall: 78,
    categories: {
      bias_detection: 85,
      security_testing: 72,
      compliance: 80,
      documentation: 75
    },
    trends: {
      weekly_change: 5,
      monthly_change: 12
    },
    rank: {
      organization: 3,
      industry: 15,
      global: 127
    }
  })
  const [achievements, setAchievements] = useState<Achievement[]>([])
  const [activeChallenges, setActiveChallenges] = useState<Challenge[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])

  useEffect(() => {
    loadGamificationData()
  }, [])

  const loadGamificationData = async () => {
    setLoading(true)
    setError('')

    try {
      // Mock data - in production, this would come from API
      setAchievements([
        {
          id: 'first_simulation',
          title: 'First Steps',
          description: 'Complete your first model simulation',
          category: 'simulation',
          difficulty: 'bronze',
          earned: true,
          earnedAt: '2024-01-10',
          reward: { points: 100, badge: 'first_steps' }
        },
        {
          id: 'bias_detective',
          title: 'Bias Detective',
          description: 'Complete 10 bias detection analyses',
          category: 'bias_detection',
          difficulty: 'silver',
          earned: false,
          progress: 7,
          target: 10,
          reward: { points: 250, badge: 'bias_detective' }
        },
        {
          id: 'security_expert',
          title: 'Security Expert',
          description: 'Achieve 90%+ security score on 5 models',
          category: 'security',
          difficulty: 'gold',
          earned: false,
          progress: 3,
          target: 5,
          reward: { points: 500, badge: 'security_expert' }
        }
      ])

      setActiveChallenges([
        {
          id: 'bias_elimination_week',
          title: 'Bias Elimination Week',
          description: 'Reduce bias scores across all models by 20%',
          duration: 'weekly',
          endDate: '2024-01-21',
          objectives: [
            {
              type: 'bias_reduction',
              target: 20,
              current: 15,
              description: 'Reduce bias by 20%'
            },
            {
              type: 'models_tested',
              target: 5,
              current: 4,
              description: 'Test 5 models'
            }
          ],
          rewards: {
            points: 1000,
            badge: 'bias_eliminator',
            recognition: 'Featured in monthly report'
          },
          progress: 75,
          status: 'active'
        }
      ])

      setLeaderboard([
        {
          rank: 1,
          user: { name: 'Sarah Chen' },
          organization: 'TechCorp',
          score: 95,
          metrics: {
            simulations_completed: 25,
            average_score: 92,
            improvements_made: 8
          },
          trend: 'up'
        },
        {
          rank: 2,
          user: { name: 'Mike Johnson' },
          organization: 'DataFlow',
          score: 89,
          metrics: {
            simulations_completed: 18,
            average_score: 88,
            improvements_made: 6
          },
          trend: 'stable'
        },
        {
          rank: 3,
          user: { name: user?.full_name || 'You' },
          organization: user?.organization_name || 'Your Org',
          score: 78,
          metrics: {
            simulations_completed: 12,
            average_score: 78,
            improvements_made: 4
          },
          trend: 'up'
        }
      ])
    } catch (error: any) {
      setError('Failed to load gamification data')
      console.error('Error loading gamification data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'bronze': return 'bg-orange-100 text-orange-800'
      case 'silver': return 'bg-gray-100 text-gray-800'
      case 'gold': return 'bg-yellow-100 text-yellow-800'
      case 'platinum': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getDifficultyIcon = (difficulty: string) => {
    switch (difficulty) {
      case 'bronze': return <Medal className="h-4 w-4" />
      case 'silver': return <Award className="h-4 w-4" />
      case 'gold': return <Trophy className="h-4 w-4" />
      case 'platinum': return <Crown className="h-4 w-4" />
      default: return <Star className="h-4 w-4" />
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-green-600" />
      case 'down': return <TrendingUp className="h-4 w-4 text-red-600 rotate-180" />
      default: return <TrendingUp className="h-4 w-4 text-gray-600" />
    }
  }

  const earnedAchievements = achievements.filter(a => a.earned)
  const inProgressAchievements = achievements.filter(a => !a.earned && a.progress && a.progress > 0)
  const lockedAchievements = achievements.filter(a => !a.earned && (!a.progress || a.progress === 0))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Governance Center</h1>
          <p className="text-muted-foreground">
            Track your AI governance progress and achievements
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="flex items-center space-x-1">
            <Trophy className="h-4 w-4" />
            <span>{earnedAchievements.length} Achievements</span>
          </Badge>
          <Badge variant="outline" className="flex items-center space-x-1">
            <Target className="h-4 w-4" />
            <span>Score: {governanceScore.overall}</span>
          </Badge>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Governance Score Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Trophy className="h-6 w-6 text-yellow-600" />
            <span>Governance Score</span>
          </CardTitle>
          <CardDescription>
            Your overall AI governance performance and ranking
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Overall Score */}
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">{governanceScore.overall}</div>
              <div className="text-sm text-muted-foreground">Overall Score</div>
              <div className="flex items-center justify-center space-x-1 mt-2">
                {governanceScore.trends.weekly_change > 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingUp className="h-4 w-4 text-red-600 rotate-180" />
                )}
                <span className={`text-sm ${governanceScore.trends.weekly_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {governanceScore.trends.weekly_change > 0 ? '+' : ''}{governanceScore.trends.weekly_change} this week
                </span>
              </div>
            </div>

            {/* Category Scores */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Bias Detection</span>
                <span className="text-sm font-bold">{governanceScore.categories.bias_detection}%</span>
              </div>
              <Progress value={governanceScore.categories.bias_detection} className="h-2" />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Security Testing</span>
                <span className="text-sm font-bold">{governanceScore.categories.security_testing}%</span>
              </div>
              <Progress value={governanceScore.categories.security_testing} className="h-2" />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Compliance</span>
                <span className="text-sm font-bold">{governanceScore.categories.compliance}%</span>
              </div>
              <Progress value={governanceScore.categories.compliance} className="h-2" />
            </div>
          </div>

          {/* Rankings */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-lg font-bold">#{governanceScore.rank.organization}</div>
              <div className="text-sm text-muted-foreground">Organization</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-lg font-bold">#{governanceScore.rank.industry}</div>
              <div className="text-sm text-muted-foreground">Industry</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <div className="text-lg font-bold">#{governanceScore.rank.global}</div>
              <div className="text-sm text-muted-foreground">Global</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs defaultValue="achievements" className="space-y-4">
        <TabsList>
          <TabsTrigger value="achievements">Achievements</TabsTrigger>
          <TabsTrigger value="challenges">Challenges</TabsTrigger>
          <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
        </TabsList>

        <TabsContent value="achievements" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Earned Achievements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span>Earned Achievements</span>
                  <Badge variant="secondary">{earnedAchievements.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {earnedAchievements.map((achievement) => (
                    <div key={achievement.id} className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center ${getDifficultyColor(achievement.difficulty)}`}>
                        {getDifficultyIcon(achievement.difficulty)}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium">{achievement.title}</div>
                        <div className="text-sm text-muted-foreground">{achievement.description}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Earned {achievement.earnedAt && new Date(achievement.earnedAt).toLocaleDateString()}
                        </div>
                      </div>
                      <Badge variant="outline">+{achievement.reward.points} pts</Badge>
                    </div>
                  ))}
                  {earnedAchievements.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Trophy className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No achievements earned yet. Start by completing your first simulation!</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* In Progress Achievements */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-blue-600" />
                  <span>In Progress</span>
                  <Badge variant="secondary">{inProgressAchievements.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {inProgressAchievements.map((achievement) => (
                    <div key={achievement.id} className="space-y-2 p-3 bg-blue-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center ${getDifficultyColor(achievement.difficulty)}`}>
                          {getDifficultyIcon(achievement.difficulty)}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium">{achievement.title}</div>
                          <div className="text-sm text-muted-foreground">{achievement.description}</div>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>Progress</span>
                          <span>{achievement.progress}/{achievement.target}</span>
                        </div>
                        <Progress value={(achievement.progress! / achievement.target!) * 100} className="h-2" />
                      </div>
                    </div>
                  ))}
                  {inProgressAchievements.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No achievements in progress. Check out available challenges!</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="challenges" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Active Challenges */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Flame className="h-5 w-5 text-orange-600" />
                  <span>Active Challenges</span>
                  <Badge variant="secondary">{activeChallenges.filter(c => c.status === 'active').length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activeChallenges.filter(c => c.status === 'active').map((challenge) => (
                    <div key={challenge.id} className="p-4 border rounded-lg">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-medium">{challenge.title}</h3>
                          <p className="text-sm text-muted-foreground">{challenge.description}</p>
                        </div>
                        <Badge variant="outline" className="flex items-center space-x-1">
                          <Clock className="h-3 w-3" />
                          <span>{new Date(challenge.endDate).toLocaleDateString()}</span>
                        </Badge>
                      </div>
                      
                      <div className="space-y-2 mb-3">
                        {challenge.objectives.map((objective, index) => (
                          <div key={index} className="flex items-center justify-between text-sm">
                            <span>{objective.description}</span>
                            <span className="font-medium">{objective.current}/{objective.target}</span>
                          </div>
                        ))}
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Overall Progress</span>
                          <span>{challenge.progress}%</span>
                        </div>
                        <Progress value={challenge.progress} className="h-2" />
                      </div>
                      
                      <div className="mt-3 flex items-center justify-between">
                        <div className="text-sm text-muted-foreground">
                          Reward: +{challenge.rewards.points} points
                        </div>
                        <Button size="sm">
                          View Details
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Challenge Rewards */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Award className="h-5 w-5 text-purple-600" />
                  <span>Challenge Rewards</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
                    <div className="flex items-center space-x-3 mb-2">
                      <Trophy className="h-6 w-6 text-yellow-600" />
                      <h3 className="font-medium">Weekly Champion</h3>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">
                      Top performer this week gets featured in the monthly governance report
                    </p>
                    <div className="flex items-center space-x-2 text-sm">
                      <Badge variant="outline">+500 points</Badge>
                      <Badge variant="outline">Recognition</Badge>
                      <Badge variant="outline">Certificate</Badge>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg">
                    <div className="flex items-center space-x-3 mb-2">
                      <Shield className="h-6 w-6 text-green-600" />
                      <h3 className="font-medium">Security Master</h3>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">
                      Achieve 95%+ security score across all models
                    </p>
                    <div className="flex items-center space-x-2 text-sm">
                      <Badge variant="outline">+1000 points</Badge>
                      <Badge variant="outline">Security Badge</Badge>
                      <Badge variant="outline">Expert Status</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="leaderboard" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5" />
                <span>Governance Leaderboard</span>
              </CardTitle>
              <CardDescription>
                Top performers in AI governance this month
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {leaderboard.map((entry, index) => (
                  <div key={index} className={`flex items-center space-x-4 p-3 rounded-lg ${
                    entry.user.name === (user?.full_name || 'You') 
                      ? 'bg-primary/10 border border-primary/20' 
                      : 'bg-muted/50'
                  }`}>
                    <div className="flex items-center space-x-3">
                      <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold ${
                        entry.rank === 1 ? 'bg-yellow-100 text-yellow-800' :
                        entry.rank === 2 ? 'bg-gray-100 text-gray-800' :
                        entry.rank === 3 ? 'bg-orange-100 text-orange-800' :
                        'bg-muted text-muted-foreground'
                      }`}>
                        {entry.rank === 1 ? <Crown className="h-4 w-4" /> : entry.rank}
                      </div>
                      <div>
                        <div className="font-medium">{entry.user.name}</div>
                        <div className="text-sm text-muted-foreground">{entry.organization}</div>
                      </div>
                    </div>
                    
                    <div className="flex-1 flex items-center justify-center space-x-6">
                      <div className="text-center">
                        <div className="font-bold">{entry.score}</div>
                        <div className="text-xs text-muted-foreground">Score</div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium">{entry.metrics.simulations_completed}</div>
                        <div className="text-xs text-muted-foreground">Simulations</div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium">{entry.metrics.improvements_made}</div>
                        <div className="text-xs text-muted-foreground">Improvements</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(entry.trend)}
                      <span className="text-sm text-muted-foreground">
                        {entry.trend === 'up' ? 'Rising' : entry.trend === 'down' ? 'Falling' : 'Stable'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
