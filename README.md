# FairMind - AI Governance Platform

A comprehensive AI governance and ethical testing platform built with Next.js, FastAPI, and Supabase.

## 🌐 Live Demo

Visit the live application: [FairMind Dashboard](https://radhi1991.github.io/fairmind/)

## 🚀 Features

- **AI Governance Dashboard** - Comprehensive monitoring and management
- **Model Registry** - Track and manage AI models
- **Risk Assessment** - Evaluate model risks and compliance
- **Geographic Bias Detection** - Identify and mitigate bias
- **AI Model Testing** - Comprehensive testing suite
- **Real-time Monitoring** - Live updates and alerts
- **Dark Theme UI** - Modern, accessible interface

## 🏗️ Architecture

- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Backend**: Python FastAPI with SQLAlchemy
- **Database**: Supabase PostgreSQL
- **Authentication**: Supabase Auth
- **Real-time**: Supabase Realtime
- **Deployment**: GitHub Pages (Frontend) + Vercel/Railway (Backend)

## 📁 Project Structure

```
fairmind-ethical-sandbox/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities and services
│   │   └── types/           # TypeScript types
├── backend/                  # FastAPI application
│   ├── main.py              # FastAPI app
│   ├── models/              # AI model implementations
│   └── requirements.txt     # Python dependencies
├── supabase/                # Database migrations
└── docs/                    # Documentation
```

## 🛠️ Development

### Prerequisites

- Node.js 18+ and Bun
- Python 3.9+
- Supabase account

### Frontend Development

```bash
cd frontend
bun install
bun run dev
```

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python main.py
```

## 🚀 Deployment

### GitHub Pages (Frontend)

The frontend is automatically deployed to GitHub Pages when changes are pushed to the `gh-pages` branch.

**Live URL**: https://radhi1991.github.io/fairmind/

### Backend Deployment

The backend can be deployed to:
- **Vercel**: For serverless deployment
- **Railway**: For containerized deployment
- **Heroku**: For traditional deployment

## 📊 Key Features

### AI Governance Dashboard
- Real-time metrics and KPIs
- Model performance tracking
- Risk assessment matrix
- Compliance monitoring

### Geographic Bias Detection
- Multi-regional bias analysis
- Cultural sensitivity testing
- Geographic fairness metrics
- Bias mitigation strategies

### Model Testing Suite
- Comprehensive test scenarios
- Automated testing workflows
- Performance benchmarking
- Safety and robustness testing

## 🔧 Configuration

1. Copy `.env.template` to `.env.local`
2. Configure Supabase credentials
3. Set up email service (optional)
4. Configure authentication settings

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For support and questions, please open an issue on GitHub.

---

**FairMind** - Empowering ethical AI development through comprehensive governance and testing.
