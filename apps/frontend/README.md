# 🎨 FairMind Frontend

> **Next.js frontend for ethical AI governance with modern tooling (Bun) and terminal-inspired design**

[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18.3+-blue)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9+-blue)](https://www.typescriptlang.org/)
[![Bun](https://img.shields.io/badge/Package%20Manager-Bun-orange)](https://bun.sh/)
[![Tailwind](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC)](https://tailwindcss.com/)

## 🎯 **Overview**

FairMind Frontend is a modern Next.js application featuring a **terminal-inspired design** with gold accents, providing an intuitive interface for ethical AI governance, bias detection, and model monitoring.

### **🏆 Recent Achievements**
- ✅ **Production Deployed**: Netlify deployment at app-demo.fairmind.xyz
- ✅ **Modern UI/UX**: Terminal-inspired design with high accessibility
- ✅ **Modern Tooling**: Bun package manager for fast development
- ✅ **Real Data Integration**: All API endpoints connected with real data

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Install Bun (modern JavaScript runtime)
curl -fsSL https://bun.sh/install | bash

# Verify installation
bun --version
```

### **Installation & Setup**
```bash
cd apps/frontend

# Install dependencies with Bun
bun install

# Start development server
bun run dev
```

### **Production Build**
```bash
# Build for production
bun run build

# Start production server
bun run start

# Export static site
bun run export
```

## 🎨 **Design System**

### **Terminal-Inspired Theme**
- **Color Scheme**: Black/White with gold accents
- **Typography**: JetBrains Mono for code-like appearance
- **Layout**: Sidebar navigation with categorized sections
- **Accessibility**: High contrast ratios and keyboard navigation

### **Color Palette**
```css
/* Primary Colors */
--background: #000000
--foreground: #ffffff
--gold: #FFD700
--gold-foreground: #000000

/* Semantic Colors */
--muted: #1a1a1a
--muted-foreground: #a3a3a3
--border: #262626
--input: #1a1a1a
```

### **Typography**
- **Primary Font**: JetBrains Mono (monospace)
- **Font Weights**: 400 (regular), 500 (medium), 600 (semibold)
- **Line Heights**: Optimized for readability
- **Font Sizes**: Responsive scaling

## 🏗️ **Architecture**

```
apps/frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx       # Root layout with sidebar
│   │   ├── page.tsx         # Dashboard page
│   │   ├── bias-detection/  # Bias detection feature
│   │   ├── security-testing/# Security testing feature
│   │   └── model-upload/    # Model upload feature
│   ├── components/          # Reusable UI components
│   │   ├── ui/              # Base UI components
│   │   └── common/          # Common components
│   ├── config/              # Configuration files
│   │   └── api.ts           # API client configuration
│   └── styles/              # Global styles
├── public/                  # Static assets
├── tailwind.config.ts       # Tailwind configuration
├── package.json             # Dependencies and scripts
└── README.md                # This file
```

## 🛠️ **Technology Stack**

### **Core Framework**
- **Next.js 14**: React framework with App Router
- **React 18**: Modern React with concurrent features
- **TypeScript**: Type-safe JavaScript development

### **Styling & UI**
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Lucide React**: Beautiful icon library
- **Custom Theme**: Terminal-inspired design system

### **State Management**
- **Zustand**: Lightweight state management
- **React Hook Form**: Form handling and validation
- **React Query**: Server state management

### **Development Tools**
- **Bun**: Fast JavaScript runtime and package manager
- **ESLint**: Code linting and quality
- **TypeScript**: Static type checking
- **Tailwind CSS**: Utility-first styling

## 🎪 **Features**

### **Core Pages**
| Page | Description | Status |
|------|-------------|--------|
| **Dashboard** | Main overview with metrics and activity | ✅ |
| **Bias Detection** | Comprehensive bias analysis interface | ✅ |
| **Security Testing** | OWASP AI security assessment | ✅ |
| **Model Upload** | Model registration and management | ✅ |
| **AI DNA Profiling** | Model signatures and lineage | ✅ |
| **AI Time Travel** | Historical and future analysis | ✅ |
| **AI Circus** | Comprehensive testing suite | ✅ |
| **Ethics Observatory** | Ethics framework evaluation | ✅ |

### **Navigation Structure**
```
DISCOVER
├── Dashboard
└── Model Registry

UPLOAD
├── Model Upload
└── Dataset Management

TEST
├── Bias Detection
├── Security Testing
└── AI Circus

MONITOR
├── AI DNA Profiling
├── AI Time Travel
└── Performance Metrics

GOVERN
├── Ethics Observatory
├── Compliance Monitoring
└── Policy Management

ANALYZE
├── Reports
├── Analytics
└── Insights
```

## 📊 **API Integration**

### **API Client**
```typescript
// src/config/api.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const apiClient = {
  // Dashboard endpoints
  getDashboardMetrics: () => fetch(`${API_BASE_URL}/api/dashboard/metrics`),
  getRecentActivity: () => fetch(`${API_BASE_URL}/api/dashboard/activity`),
  
  // Bias detection endpoints
  analyzeBias: (data) => fetch(`${API_BASE_URL}/api/bias-detection/analyze`, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // Security testing endpoints
  runSecurityTest: (data) => fetch(`${API_BASE_URL}/api/security/analyze`, {
    method: 'POST',
    body: JSON.stringify(data)
  })
};
```

### **Real Data Integration**
- **Dashboard Metrics**: Real-time governance metrics
- **Bias Analysis**: Live bias detection results
- **Security Results**: OWASP AI security assessments
- **Model Registry**: Actual model data and metadata

## 🎨 **UI Components**

### **Base Components**
```typescript
// Reusable UI components
- Button: Primary, secondary, and ghost variants
- Card: Content containers with terminal styling
- Input: Form inputs with consistent styling
- Badge: Status indicators and labels
- Modal: Overlay dialogs and forms
- Table: Data display with sorting and pagination
```

### **Feature Components**
```typescript
// Feature-specific components
- BiasAnalysisCard: Bias detection results display
- SecurityTestPanel: Security assessment interface
- ModelUploadForm: Model registration form
- MetricsDashboard: Real-time metrics display
- ActivityFeed: Recent activity timeline
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_API_BASE_URL=https://api.fairmind.xyz

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_REAL_TIME=true

# External Services
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-key
```

### **Tailwind Configuration**
```typescript
// tailwind.config.ts
export default {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: 'hsl(var(--gold))',
          foreground: 'hsl(var(--gold-foreground))',
        },
      },
      fontFamily: {
        mono: ['var(--font-jetbrains)', 'monospace'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

## 🧪 **Testing**

### **Running Tests**
```bash
# Install test dependencies
bun install

# Run all tests
bun run test

# Run tests in watch mode
bun run test:watch

# Run tests with coverage
bun run test:coverage

# Run specific test file
bun test src/components/Button.test.tsx
```

### **Test Coverage**
- **Component Testing**: All UI components tested
- **Integration Testing**: API integration tested
- **Accessibility Testing**: WCAG compliance verified
- **Performance Testing**: Core Web Vitals optimized

## 🚀 **Deployment**

### **Netlify Deployment**
```bash
# Deploy to Netlify (already configured)
netlify deploy --prod

# Check deployment status
netlify status

# View deployment logs
netlify logs
```

### **Manual Deployment**
```bash
# Build for production
bun run build

# Export static site
bun run export

# Deploy to any static hosting
# (Netlify, Vercel, GitHub Pages, etc.)
```

### **Docker Deployment**
```dockerfile
FROM node:18-alpine

# Install Bun
RUN npm install -g bun

# Copy project files
COPY . /app
WORKDIR /app

# Install dependencies
RUN bun install

# Build application
RUN bun run build

# Start application
CMD ["bun", "start"]
```

## 📈 **Performance**

### **Core Web Vitals**
- **Largest Contentful Paint (LCP)**: <2.5s
- **First Input Delay (FID)**: <100ms
- **Cumulative Layout Shift (CLS)**: <0.1

### **Optimizations**
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Font Optimization**: JetBrains Mono with display swap
- **Bundle Analysis**: Regular bundle size monitoring

## 🔒 **Security**

### **Implemented Security**
- **Content Security Policy**: CSP headers configured
- **XSS Protection**: Input sanitization and validation
- **CSRF Protection**: API request validation
- **HTTPS Enforcement**: Secure communication

### **Security Headers**
```typescript
// next.config.js
const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on'
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload'
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  }
];
```

## 📚 **Documentation**

### **Component Documentation**
- **Storybook**: Interactive component documentation
- **TypeScript**: Full type definitions
- **JSDoc**: Comprehensive function documentation
- **Examples**: Code examples and usage patterns

### **API Documentation**
- **OpenAPI**: Machine-readable API schema
- **Swagger UI**: Interactive API documentation
- **Type Definitions**: TypeScript API types

## 🤝 **Contributing**

### **Development Workflow**
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Install** dependencies (`bun install`)
4. **Make** changes and add tests
5. **Run** tests (`bun test`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Push** to branch (`git push origin feature/amazing-feature`)
8. **Create** Pull Request

### **Code Standards**
- **Formatting**: Prettier code formatting
- **Linting**: ESLint with TypeScript rules
- **Type Checking**: Strict TypeScript configuration
- **Testing**: Jest with React Testing Library

## 🆘 **Support**

### **Getting Help**
- **Documentation**: [Component Docs](./docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/fairmind-ethical-sandbox/issues)
- **Testing**: [Test Results](../test_results/)
- **Deployment**: [Netlify Dashboard](https://app.netlify.com/)

### **Common Issues**
- **Build Errors**: Check TypeScript errors and dependencies
- **Styling Issues**: Verify Tailwind configuration
- **API Errors**: Check API endpoint availability
- **Performance Issues**: Run bundle analysis and optimize

---

**🎉 FairMind Frontend is production-ready with modern UI/UX!**

*Built with Next.js and Bun for the future of ethical AI governance interfaces.*
