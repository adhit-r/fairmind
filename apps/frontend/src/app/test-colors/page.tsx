"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/common/card"
import { Button } from "@/components/ui/common/button"
import { Badge } from "@/components/ui/common/badge"
import { Alert, AlertDescription } from "@/components/ui/common/alert"
import { 
  Eye, 
  EyeOff, 
  CheckCircle, 
  AlertTriangle, 
  Info,
  XCircle
} from "lucide-react"

export default function TestColorsPage() {
  const [isDarkMode, setIsDarkMode] = useState(false)

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode)
    document.documentElement.setAttribute('data-theme', !isDarkMode ? 'dark' : 'light')
  }

  return (
    <div className="p-6 space-y-6">
      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <div id="main-content">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-4 neo-heading">
            Color Scheme & Accessibility Test
          </h1>
          <p className="text-lg neo-text">
            This page tests the color scheme and accessibility features to ensure proper contrast and readability.
          </p>
        </div>

        {/* Theme Toggle */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="neo-heading">Theme Toggle</CardTitle>
            <CardDescription className="neo-text">
              Test switching between light and dark modes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={toggleTheme}
              className="neo-button neo-button--primary"
            >
              {isDarkMode ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
              Switch to {isDarkMode ? 'Light' : 'Dark'} Mode
            </Button>
            <p className="mt-2 neo-text neo-text--muted">
              Current theme: {isDarkMode ? 'Dark' : 'Light'}
            </p>
          </CardContent>
        </Card>

        {/* Color Test Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Primary Card */}
          <Card className="neo-card">
            <CardHeader>
              <CardTitle className="neo-heading">Primary Content</CardTitle>
              <CardDescription className="neo-text">
                This card tests primary text and background colors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="neo-text">
                This is primary text that should be clearly readable in both light and dark modes.
              </p>
              <Button className="neo-button neo-button--primary mt-4">
                Primary Button
              </Button>
            </CardContent>
          </Card>

          {/* Secondary Card */}
          <Card className="neo-card">
            <CardHeader>
              <CardTitle className="neo-heading">Secondary Content</CardTitle>
              <CardDescription className="neo-text">
                This card tests secondary text and background colors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="neo-text neo-text--muted">
                This is secondary text that should also be clearly readable.
              </p>
              <Button className="neo-button neo-button--secondary mt-4">
                Secondary Button
              </Button>
            </CardContent>
          </Card>

          {/* Alert Card */}
          <Card className="neo-card">
            <CardHeader>
              <CardTitle className="neo-heading">Alert Content</CardTitle>
              <CardDescription className="neo-text">
                This card tests alert and notification colors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert className="neo-alert neo-alert--danger mb-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  This is a danger alert that should be clearly visible.
                </AlertDescription>
              </Alert>
              <Alert className="neo-alert neo-alert--success">
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  This is a success alert that should be clearly visible.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </div>

        {/* Accessibility Features Test */}
        <Card className="neo-card">
          <CardHeader>
            <CardTitle className="neo-heading">Accessibility Features Test</CardTitle>
            <CardDescription className="neo-text">
              Test various accessibility features and color contrasts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Badge Tests */}
            <div className="space-y-2">
              <h3 className="neo-heading neo-heading--md">Badge Colors</h3>
              <div className="flex flex-wrap gap-2">
                <Badge variant="default">Default Badge</Badge>
                <Badge variant="secondary">Secondary Badge</Badge>
                <Badge variant="destructive">Destructive Badge</Badge>
                <Badge variant="outline">Outline Badge</Badge>
              </div>
            </div>

            {/* Link Tests */}
            <div className="space-y-2">
              <h3 className="neo-heading neo-heading--md">Link Colors</h3>
              <p className="neo-text">
                This is a paragraph with a <a href="#" className="text-blue-600 hover:text-blue-800 underline">link</a> that should be clearly distinguishable.
              </p>
            </div>

            {/* Form Element Tests */}
            <div className="space-y-2">
              <h3 className="neo-heading neo-heading--md">Form Elements</h3>
              <div className="space-y-2">
                <label htmlFor="test-input" className="neo-text neo-text--bold">
                  Test Input Label
                </label>
                <input 
                  type="text" 
                  id="test-input"
                  placeholder="Test input placeholder"
                  className="w-full p-2 border-2 border-black rounded neo-card"
                />
              </div>
            </div>

            {/* Focus Test */}
            <div className="space-y-2">
              <h3 className="neo-heading neo-heading--md">Focus Indicators</h3>
              <p className="neo-text neo-text--muted">
                Tab through these buttons to test focus indicators:
              </p>
              <div className="flex gap-2">
                <Button className="neo-button neo-button--primary">Button 1</Button>
                <Button className="neo-button neo-button--secondary">Button 2</Button>
                <Button className="neo-button neo-button--danger">Button 3</Button>
              </div>
            </div>

            {/* High Contrast Test */}
            <div className="space-y-2">
              <h3 className="neo-heading neo-heading--md">High Contrast Support</h3>
              <p className="neo-text neo-text--muted">
                Enable high contrast mode in your system settings to test enhanced visibility.
              </p>
              <div className="p-4 border-2 border-black bg-white">
                <p className="text-black font-bold">
                  High contrast test area - should be clearly visible
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* WCAG Compliance Info */}
        <Card className="neo-card">
          <CardHeader>
            <CardTitle className="neo-heading">WCAG 2.1 AA Compliance</CardTitle>
            <CardDescription className="neo-text">
              This page implements accessibility standards
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="neo-heading neo-heading--sm mb-2">Contrast Ratios</h4>
                <ul className="space-y-1 neo-text">
                  <li>• Normal text: 4.5:1 minimum</li>
                  <li>• Large text: 3:1 minimum</li>
                  <li>• UI components: 3:1 minimum</li>
                </ul>
              </div>
              <div>
                <h4 className="neo-heading neo-heading--sm mb-2">Accessibility Features</h4>
                <ul className="space-y-1 neo-text">
                  <li>• Keyboard navigation support</li>
                  <li>• Screen reader compatibility</li>
                  <li>• Focus indicators</li>
                  <li>• High contrast mode support</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
