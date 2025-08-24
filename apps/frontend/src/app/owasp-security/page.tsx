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
  Lock,
  Eye,
  Zap,
  Bug,
  FileText,
  Upload,
  Play,
  Download,
  BarChart3,
  Users,
  Activity,
  Brain,
  Database,
  Server,
  Key,
  Search,
  AlertCircle
} from "lucide-react"
import { OWASPSecurityDashboard } from "@/components/features/security/owasp-security-dashboard"

export default function OWASPSecurityPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-8">
        <NeoHeading size="xl" className="mb-4">
          🛡️ OWASP AI Security Testing
        </NeoHeading>
        <NeoText className="text-xl max-w-3xl mx-auto">
          Comprehensive security testing for AI/LLM systems using OWASP Top 10 AI/LLM guidelines.
          Protect your models from attacks and vulnerabilities.
        </NeoText>
      </div>

      {/* Critical Alert */}
      <NeoAlert
        variant="danger"
        title="🚨 AI Security Threats are Real"
        icon={<AlertTriangle className="h-5 w-5" />}
      >
        <div className="space-y-3">
          <p>AI systems are vulnerable to prompt injection, data poisoning, and model theft. Without proper security testing, your AI can be compromised.</p>
          <div className="space-y-2">
            <p className="neo-text neo-text--bold">Key Recommendations:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Test for prompt injection vulnerabilities</li>
              <li>Implement input validation and sanitization</li>
              <li>Monitor for suspicious activities</li>
              <li>Regular security audits and updates</li>
            </ul>
          </div>
        </div>
      </NeoAlert>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <NeoCard className="text-center">
          <div className="text-3xl font-black text-4xl mb-2 text-red-600">10</div>
          <NeoText>Security Categories</NeoText>
        </NeoCard>
        <NeoCard className="text-center">
          <div className="text-3xl font-black text-4xl mb-2 text-blue-600">95%</div>
          <NeoText>Detection Rate</NeoText>
        </NeoCard>
        <NeoCard className="text-center">
          <div className="text-3xl font-black text-4xl mb-2 text-orange-600">200+</div>
          <NeoText>Tests Available</NeoText>
        </NeoCard>
        <NeoCard className="text-center">
          <div className="text-3xl font-black text-4xl mb-2 text-green-600">2hr</div>
          <NeoText>Scan Time</NeoText>
        </NeoCard>
      </div>

      {/* OWASP Categories */}
      <section>
        <NeoHeading size="lg" className="mb-6">🔍 OWASP Top 10 AI/LLM Security</NeoHeading>
        <NeoGrid columns={2}>
          <NeoCard
            variant="risk"
            title="💉 Prompt Injection"
            icon={<Bug className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Malicious inputs that manipulate AI systems to produce unintended outputs or bypass security controls.
            </NeoText>
            <NeoBadge variant="danger">Critical</NeoBadge>
          </NeoCard>

          <NeoCard
            variant="risk"
            title="🔓 Insecure Output Handling"
            icon={<Eye className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Failure to validate and sanitize AI outputs before presenting them to users or other systems.
            </NeoText>
            <NeoBadge variant="danger">High</NeoBadge>
          </NeoCard>

          <NeoCard
            variant="warning"
            title="☠️ Training Data Poisoning"
            icon={<Database className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Malicious manipulation of training data to introduce vulnerabilities or biases into AI models.
            </NeoText>
            <NeoBadge variant="warning">Medium</NeoBadge>
          </NeoCard>

          <NeoCard
            variant="warning"
            title="⚡ Model Denial of Service"
            icon={<Server className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Attacks that consume excessive resources to degrade AI system performance or availability.
            </NeoText>
            <NeoBadge variant="warning">Medium</NeoBadge>
          </NeoCard>

          <NeoCard
            variant="info"
            title="🔗 Supply Chain Vulnerabilities"
            icon={<Key className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Security risks introduced through third-party components, libraries, or pre-trained models.
            </NeoText>
            <NeoBadge variant="info">Low</NeoBadge>
          </NeoCard>

          <NeoCard
            variant="info"
            title="📊 Sensitive Information Disclosure"
            icon={<Search className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Unauthorized access to sensitive data through AI system outputs or model extraction attacks.
            </NeoText>
            <NeoBadge variant="info">Low</NeoBadge>
          </NeoCard>
        </NeoGrid>
      </section>

      {/* Action Buttons */}
      <section className="text-center">
        <NeoHeading size="lg" className="mb-6">⚡ Security Actions</NeoHeading>
        <div className="flex flex-wrap gap-4 justify-center">
          <NeoButton
            variant="danger"
            size="lg"
            icon={<Upload className="h-5 w-5" />}
          >
            Upload Model
          </NeoButton>
          <NeoButton
            variant="primary"
            size="lg"
            icon={<Play className="h-5 w-5" />}
          >
            Run Security Scan
          </NeoButton>
          <NeoButton
            variant="secondary"
            size="lg"
            icon={<Eye className="h-5 w-5" />}
          >
            View Vulnerabilities
          </NeoButton>
          <NeoButton
            variant="success"
            size="lg"
            icon={<Download className="h-5 w-5" />}
          >
            Download Report
          </NeoButton>
        </div>
      </section>

      {/* Main Security Dashboard */}
      <section>
        <NeoHeading size="lg" className="mb-6">📊 Security Analysis Dashboard</NeoHeading>
        <NeoCard>
          <OWASPSecurityDashboard />
        </NeoCard>
      </section>

      {/* Security Benefits */}
      <section>
        <NeoHeading size="lg" className="mb-6">✅ Security Benefits</NeoHeading>
        <NeoGrid columns={2}>
          <NeoCard
            variant="achievement"
            title="🛡️ Comprehensive Protection"
            icon={<Shield className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Protect your AI systems from all major security threats identified by OWASP.
            </NeoText>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <NeoText className="text-sm">Prevent prompt injection attacks</NeoText>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <NeoText className="text-sm">Secure output handling</NeoText>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <NeoText className="text-sm">Protect against data poisoning</NeoText>
              </div>
            </div>
          </NeoCard>

          <NeoCard
            variant="achievement"
            title="📈 Risk Reduction"
            icon={<BarChart3 className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Reduce security risks and protect your organization from costly breaches and attacks.
            </NeoText>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <NeoText className="text-sm">Prevent data breaches</NeoText>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <NeoText className="text-sm">Maintain system availability</NeoText>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <NeoText className="text-sm">Protect intellectual property</NeoText>
              </div>
            </div>
          </NeoCard>
        </NeoGrid>
      </section>

      {/* Industry Applications */}
      <section>
        <NeoHeading size="lg" className="mb-6">🏢 Industry Applications</NeoHeading>
        <NeoGrid columns={3}>
          <NeoCard
            variant="compliance"
            title="🏦 Financial Services"
            icon={<Activity className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Secure AI-powered financial systems against fraud, manipulation, and data breaches.
            </NeoText>
            <div className="space-y-2">
              <NeoBadge variant="info">Fraud Detection</NeoBadge>
              <NeoBadge variant="info">Risk Assessment</NeoBadge>
              <NeoBadge variant="info">Customer Service</NeoBadge>
            </div>
          </NeoCard>

          <NeoCard
            variant="compliance"
            title="🏥 Healthcare"
            icon={<Brain className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Protect patient data and ensure secure AI-powered medical diagnosis and treatment systems.
            </NeoText>
            <div className="space-y-2">
              <NeoBadge variant="info">Medical Diagnosis</NeoBadge>
              <NeoBadge variant="info">Patient Records</NeoBadge>
              <NeoBadge variant="info">Treatment Planning</NeoBadge>
            </div>
          </NeoCard>

          <NeoCard
            variant="compliance"
            title="🔐 Government"
            icon={<Lock className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Secure AI systems handling sensitive government data and critical infrastructure.
            </NeoText>
            <div className="space-y-2">
              <NeoBadge variant="info">National Security</NeoBadge>
              <NeoBadge variant="info">Public Services</NeoBadge>
              <NeoBadge variant="info">Infrastructure</NeoBadge>
            </div>
          </NeoCard>
        </NeoGrid>
      </section>

      {/* Compliance */}
      <section>
        <NeoHeading size="lg" className="mb-6">📋 Security Compliance</NeoHeading>
        <NeoGrid columns={2}>
          <NeoCard
            title="🔒 SOC 2 Type II"
            icon={<Shield className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Ensure your AI systems meet SOC 2 Type II compliance requirements for security, availability, and confidentiality.
            </NeoText>
            <NeoProgress value={95} variant="success" label="Compliance Score" />
          </NeoCard>

          <NeoCard
            title="🌍 ISO 27001"
            icon={<FileText className="h-6 w-6" />}
          >
            <NeoText className="mb-3">
              Align with ISO 27001 information security management standards for comprehensive security controls.
            </NeoText>
            <NeoProgress value={88} variant="success" label="Compliance Score" />
          </NeoCard>
        </NeoGrid>
      </section>

      {/* CTA */}
      <section className="text-center">
        <NeoCard className="max-w-2xl mx-auto">
          <NeoHeading size="lg" className="mb-4">
            🚀 Secure Your AI Today
          </NeoHeading>
          <NeoText className="mb-6">
            Don't wait for a security breach. Start protecting your AI systems with comprehensive OWASP security testing.
          </NeoText>
          <NeoButton
            variant="primary"
            size="lg"
            icon={<Zap className="h-5 w-5" />}
          >
            Start Security Scan
          </NeoButton>
        </NeoCard>
      </section>
    </div>
  )
}
