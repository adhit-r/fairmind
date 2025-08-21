"use client"

import {
  NeoContainer,
  NeoGrid,
  NeoHeading,
  NeoText,
  NeoAlert,
  NeoCard,
  NeoButton,
  NeoBadge,
  NeoProgress
} from "@/components/ui/common/neo-components"
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Brain,
  Database,
  BarChart3,
  FileText,
  Upload,
  Play,
  Download,
  Eye,
  TrendingUp,
  Users,
  Activity,
  Zap,
  Moon,
  Sun,
  Trophy
} from "lucide-react"
import { ThemeToggle } from "@/components/ui/common/theme-toggle"

export default function ThemeShowcasePage() {
  return (
    <div className="space-y-8 p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <NeoHeading size="xl" className="mb-4">
          🌓 Theme Showcase - Dark & Light Modes
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto mb-6">
          Experience the neobrutalism design system in both light and dark modes.
          Toggle between themes to see the complete transformation.
        </NeoText>
        
        {/* Theme Toggle */}
        <div className="flex justify-center mb-8">
          <ThemeToggle />
        </div>
      </div>

      {/* Theme Information */}
      <NeoAlert variant="info" className="mb-8">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <Eye className="h-6 w-6" />
          </div>
          <div>
            <NeoText variant="bold" className="mb-2">
              Theme Features
            </NeoText>
            <NeoText className="mb-2">
              • Automatic system preference detection
            </NeoText>
            <NeoText className="mb-2">
              • Persistent theme storage
            </NeoText>
            <NeoText className="mb-2">
              • High contrast support for accessibility
            </NeoText>
            <NeoText>
              • Reduced motion support for users with vestibular disorders
            </NeoText>
          </div>
        </div>
      </NeoAlert>

      {/* Color Palette Showcase */}
      <section>
        <NeoHeading size="lg" className="mb-6">🎨 Color Palette</NeoHeading>
        <NeoGrid columns={4}>
          <NeoCard className="text-center">
            <div className="w-16 h-16 bg-[var(--neo-primary)] border-4 border-black rounded-lg mx-auto mb-3"></div>
            <NeoText variant="bold">Primary</NeoText>
            <NeoText className="text-sm">#ff6b35</NeoText>
          </NeoCard>
          <NeoCard className="text-center">
            <div className="w-16 h-16 bg-[var(--neo-secondary)] border-4 border-black rounded-lg mx-auto mb-3"></div>
            <NeoText variant="bold">Secondary</NeoText>
            <NeoText className="text-sm">#4ecdc4</NeoText>
          </NeoCard>
          <NeoCard className="text-center">
            <div className="w-16 h-16 bg-[var(--neo-danger)] border-4 border-black rounded-lg mx-auto mb-3"></div>
            <NeoText variant="bold">Danger</NeoText>
            <NeoText className="text-sm">#ff4757</NeoText>
          </NeoCard>
          <NeoCard className="text-center">
            <div className="w-16 h-16 bg-[var(--neo-success)] border-4 border-black rounded-lg mx-auto mb-3"></div>
            <NeoText variant="bold">Success</NeoText>
            <NeoText className="text-sm">#2ed573</NeoText>
          </NeoCard>
        </NeoGrid>
      </section>

      {/* Component Showcase */}
      <section>
        <NeoHeading size="lg" className="mb-6">🧩 Component Showcase</NeoHeading>
        
        {/* Alerts */}
        <div className="space-y-4 mb-8">
          <NeoHeading size="md">Alerts</NeoHeading>
          <NeoGrid columns={2}>
            <NeoAlert variant="danger">
              <div className="flex items-start gap-4">
                <AlertTriangle className="h-6 w-6 flex-shrink-0" />
                <div>
                  <NeoText variant="bold" className="mb-2">Critical Alert</NeoText>
                  <NeoText>This is a critical alert that requires immediate attention.</NeoText>
                </div>
              </div>
            </NeoAlert>
            <NeoAlert variant="success">
              <div className="flex items-start gap-4">
                <CheckCircle className="h-6 w-6 flex-shrink-0" />
                <div>
                  <NeoText variant="bold" className="mb-2">Success Alert</NeoText>
                  <NeoText>Operation completed successfully!</NeoText>
                </div>
              </div>
            </NeoAlert>
          </NeoGrid>
        </div>

        {/* Cards */}
        <div className="space-y-4 mb-8">
          <NeoHeading size="md">Cards</NeoHeading>
          <NeoGrid columns={3}>
            <NeoCard variant="achievement">
              <div className="flex items-center gap-3 mb-3">
                <Trophy className="h-6 w-6" />
                <NeoText variant="bold">Achievement Card</NeoText>
              </div>
              <NeoText>This card showcases achievements and accomplishments.</NeoText>
            </NeoCard>
            <NeoCard variant="compliance">
              <div className="flex items-center gap-3 mb-3">
                <Shield className="h-6 w-6" />
                <NeoText variant="bold">Compliance Card</NeoText>
              </div>
              <NeoText>This card represents compliance and security features.</NeoText>
            </NeoCard>
            <NeoCard variant="risk">
              <div className="flex items-center gap-3 mb-3">
                <AlertTriangle className="h-6 w-6" />
                <NeoText variant="bold">Risk Card</NeoText>
              </div>
              <NeoText>This card highlights potential risks and warnings.</NeoText>
            </NeoCard>
          </NeoGrid>
        </div>

        {/* Buttons */}
        <div className="space-y-4 mb-8">
          <NeoHeading size="md">Buttons</NeoHeading>
          <div className="flex flex-wrap gap-4">
            <NeoButton variant="primary">
              <Play className="h-4 w-4 mr-2" />
              Primary Action
            </NeoButton>
            <NeoButton variant="secondary">
              <Upload className="h-4 w-4 mr-2" />
              Secondary Action
            </NeoButton>
            <NeoButton variant="danger">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Danger Action
            </NeoButton>
            <NeoButton variant="success">
              <CheckCircle className="h-4 w-4 mr-2" />
              Success Action
            </NeoButton>
          </div>
        </div>

        {/* Badges */}
        <div className="space-y-4 mb-8">
          <NeoHeading size="md">Badges</NeoHeading>
          <div className="flex flex-wrap gap-4">
            <NeoBadge variant="success">Success</NeoBadge>
            <NeoBadge variant="warning">Warning</NeoBadge>
            <NeoBadge variant="danger">Danger</NeoBadge>
            <NeoBadge variant="info">Info</NeoBadge>
          </div>
        </div>

        {/* Progress Bars */}
        <div className="space-y-4 mb-8">
          <NeoHeading size="md">Progress Bars</NeoHeading>
          <div className="space-y-4">
            <div>
              <NeoText className="mb-2">Success Progress (75%)</NeoText>
              <NeoProgress value={75} variant="success" />
            </div>
            <div>
              <NeoText className="mb-2">Warning Progress (45%)</NeoText>
              <NeoProgress value={45} variant="warning" />
            </div>
            <div>
              <NeoText className="mb-2">Danger Progress (90%)</NeoText>
              <NeoProgress value={90} variant="danger" />
            </div>
          </div>
        </div>
      </section>

      {/* Typography Showcase */}
      <section>
        <NeoHeading size="lg" className="mb-6">📝 Typography</NeoHeading>
        <NeoGrid columns={2}>
          <div className="space-y-4">
            <div>
              <NeoHeading size="xl">Extra Large Heading</NeoHeading>
              <NeoText>This is the largest heading size for main titles.</NeoText>
            </div>
            <div>
              <NeoHeading size="lg">Large Heading</NeoHeading>
              <NeoText>This is a large heading for section titles.</NeoText>
            </div>
            <div>
              <NeoHeading size="md">Medium Heading</NeoHeading>
              <NeoText>This is a medium heading for subsections.</NeoText>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <NeoText variant="bold">Bold Text</NeoText>
              <NeoText>This is regular body text with good readability.</NeoText>
            </div>
            <div>
              <NeoText className="text-secondary">Secondary Text</NeoText>
              <NeoText>This is secondary text for less important information.</NeoText>
            </div>
            <div>
              <NeoText className="text-muted">Muted Text</NeoText>
              <NeoText>This is muted text for subtle information.</NeoText>
            </div>
          </div>
        </NeoGrid>
      </section>

      {/* Accessibility Features */}
      <section>
        <NeoHeading size="lg" className="mb-6">♿ Accessibility Features</NeoHeading>
        <NeoGrid columns={2}>
          <NeoCard variant="info">
            <div className="flex items-center gap-3 mb-3">
              <Eye className="h-6 w-6" />
              <NeoText variant="bold">High Contrast Support</NeoText>
            </div>
            <NeoText>
              The design automatically adapts to high contrast mode preferences,
              ensuring readability for users with visual impairments.
            </NeoText>
          </NeoCard>
          <NeoCard variant="info">
            <div className="flex items-center gap-3 mb-3">
              <Activity className="h-6 w-6" />
              <NeoText variant="bold">Reduced Motion</NeoText>
            </div>
            <NeoText>
              Animations and transitions are disabled for users who prefer
              reduced motion due to vestibular disorders.
            </NeoText>
          </NeoCard>
        </NeoGrid>
      </section>

      {/* Theme Comparison */}
      <section>
        <NeoHeading size="lg" className="mb-6">🔄 Theme Comparison</NeoHeading>
        <NeoCard>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <NeoHeading size="md" className="mb-4">Light Mode</NeoHeading>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-white border-2 border-black rounded"></div>
                  <NeoText>Clean, professional appearance</NeoText>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-white border-2 border-black rounded"></div>
                  <NeoText>High contrast for readability</NeoText>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-white border-2 border-black rounded"></div>
                  <NeoText>Traditional office environment</NeoText>
                </div>
              </div>
            </div>
            <div>
              <NeoHeading size="md" className="mb-4">Dark Mode</NeoHeading>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-800 border-2 border-white rounded"></div>
                  <NeoText>Reduced eye strain in low light</NeoText>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-800 border-2 border-white rounded"></div>
                  <NeoText>Modern, sleek appearance</NeoText>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-800 border-2 border-white rounded"></div>
                  <NeoText>Battery saving on OLED displays</NeoText>
                </div>
              </div>
            </div>
          </div>
        </NeoCard>
      </section>

      {/* CTA */}
      <section className="text-center">
        <NeoCard className="max-w-2xl mx-auto">
          <NeoHeading size="lg" className="mb-4">
            🎨 Experience the Full Design System
          </NeoHeading>
          <NeoText className="mb-6">
            The neobrutalism design system provides a bold, engaging experience
            that makes critical information stand out while maintaining professional credibility.
          </NeoText>
          <div className="flex flex-wrap gap-4 justify-center">
            <NeoButton variant="primary">
              <Zap className="h-4 w-4 mr-2" />
              Explore Features
            </NeoButton>
            <NeoButton variant="secondary">
              <Download className="h-4 w-4 mr-2" />
              Download Assets
            </NeoButton>
          </div>
        </NeoCard>
      </section>
    </div>
  )
}
