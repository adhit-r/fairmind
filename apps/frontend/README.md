# FairMind Frontend

A modern, enterprise-grade AI governance and bias detection platform built with Next.js, React, and TypeScript.

## Overview

The FairMind frontend provides a sophisticated user interface for AI model governance, bias detection, security testing, and compliance monitoring. Built with a terminal-inspired design system featuring high contrast and accessibility-first principles.

## Features

### Core Functionality
- **AI Model Governance Dashboard** - Comprehensive monitoring and metrics
- **Bias Detection & Analysis** - Advanced fairness testing with multiple algorithms
- **Security Testing** - OWASP AI/LLM security assessment
- **Model Lifecycle Management** - Upload, test, monitor, and govern AI models
- **Compliance Monitoring** - NIST, GDPR, and regulatory adherence tracking

### Technical Features
- **Modern UI/UX** - Terminal-inspired design with gold accents
- **High Accessibility** - WCAG 2.1 AA compliant with excellent contrast ratios
- **Real-time Data** - Live integration with backend APIs
- **Responsive Design** - Optimized for desktop and mobile devices
- **Type Safety** - Full TypeScript implementation

## Technology Stack

### Core Framework
- **Next.js 14** - React framework with App Router
- **React 18** - UI library with hooks and concurrent features
- **TypeScript** - Type-safe JavaScript development

### Styling & UI
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives
- **Lucide React** - Modern icon library
- **JetBrains Mono** - Terminal-style typography

### State Management & Data
- **Zustand** - Lightweight state management
- **React Hook Form** - Form handling and validation
- **Recharts** - Data visualization library
- **Chart.js** - Additional charting capabilities

### Development Tools
- **ESLint** - Code linting and quality
- **PostCSS** - CSS processing
- **Autoprefixer** - CSS vendor prefixing

## Getting Started

### Prerequisites
- Node.js 18+ 
- Bun (recommended) or npm
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fairmind-ethical-sandbox/apps/frontend
   ```

2. **Install dependencies**
   ```bash
   bun install
   # or
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   ```
   
   Configure the following variables:
   ```env
   NEXT_PUBLIC_API_URL=https://api.fairmind.xyz
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

4. **Start development server**
   ```bash
   bun dev
   # or
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
apps/frontend/
├── public/                 # Static assets
├── src/
│   ├── app/               # Next.js App Router pages
│   │   ├── (auth)/        # Authentication pages
│   │   ├── bias-detection/ # Bias analysis interface
│   │   ├── model-upload/   # Model upload workflow
│   │   ├── security-testing/ # Security testing interface
│   │   ├── globals.css    # Global styles
│   │   ├── layout.tsx     # Root layout
│   │   └── page.tsx       # Dashboard page
│   ├── components/        # Reusable UI components
│   │   ├── core/          # Core UI components
│   │   ├── forms/         # Form components
│   │   ├── charts/        # Data visualization
│   │   └── ui/            # UI primitives
│   ├── config/            # Configuration files
│   │   └── api.ts         # API client configuration
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility libraries
│   ├── stores/            # Zustand state stores
│   └── types/             # TypeScript type definitions
├── tailwind.config.ts     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies and scripts
```

## Design System

### Color Palette
- **Background**: Dark terminal theme (#141414)
- **Foreground**: High contrast white (#F2F2F2)
- **Accent**: Gold (#FFD700) for primary actions
- **Muted**: Gray tones for secondary information

### Typography
- **Primary Font**: JetBrains Mono (monospace)
- **Font Weights**: 400 (normal), 600 (semibold), 700 (bold)
- **Line Heights**: Optimized for readability

### Components
- **Cards**: Elevated containers with borders
- **Buttons**: High contrast with hover states
- **Tables**: Clean, readable data presentation
- **Charts**: Monochrome with gold accents

## API Integration

The frontend integrates with the FairMind backend API for:

### Core Endpoints
- `GET /api/models` - Model registry
- `GET /api/datasets` - Dataset management
- `GET /api/governance/metrics` - Governance metrics
- `GET /api/activity/recent` - Recent activity

### Bias Detection
- `POST /api/bias/analyze` - Bias analysis
- `GET /api/bias/history` - Analysis history
- `GET /api/bias/datasets` - Available datasets

### Security Testing
- `POST /api/security/test` - Security assessment
- `GET /api/security/history` - Test history
- `GET /api/security/owasp` - OWASP categories

## Development Workflow

### Code Quality
```bash
# Lint code
bun lint

# Type checking
bun type-check

# Build for production
bun build
```

### Testing
```bash
# Run tests
bun test

# Run tests in watch mode
bun test:watch
```

### Deployment
```bash
# Build for production
bun build

# Start production server
bun start
```

## Accessibility

### WCAG 2.1 AA Compliance
- **Color Contrast**: Minimum 4.5:1 ratio for normal text
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Semantic HTML and ARIA labels
- **Focus Management**: Visible focus indicators

### Best Practices
- Semantic HTML structure
- Proper heading hierarchy
- Alt text for images
- Form labels and error messages
- Skip navigation links

## Performance

### Optimization Strategies
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Bundle Analysis**: Regular bundle size monitoring
- **Caching**: Static generation and ISR

### Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## Browser Support

- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

## Contributing

### Development Guidelines
1. Follow TypeScript best practices
2. Use semantic commit messages
3. Write self-documenting code
4. Maintain accessibility standards
5. Test across different screen sizes

### Code Style
- Use Prettier for formatting
- Follow ESLint rules
- Use meaningful variable names
- Add JSDoc comments for complex functions

## Troubleshooting

### Common Issues

**Build Errors**
```bash
# Clear Next.js cache
rm -rf .next
bun build
```

**TypeScript Errors**
```bash
# Check types
bun type-check
```

**API Connection Issues**
- Verify environment variables
- Check backend server status
- Review network connectivity

## License

This project is part of the FairMind Ethical Sandbox platform. See the main repository for licensing information.

## Support

For technical support or questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide

---

**Built with ❤️ for responsible AI development**
