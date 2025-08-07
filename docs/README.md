# FairMind Documentation

This directory contains comprehensive documentation for the FairMind Ethical Sandbox platform.

## 📚 **Documentation Structure**

### **📖 Guides**
- **[Neo4j Quick Setup](guides/QUICK_NEO4J_SETUP.md)** - 5-minute Neo4j AuraDB setup
- **[Neo4j Setup Guide](guides/NEO4J_SETUP_GUIDE.md)** - Detailed Neo4j integration guide
- **[Neo4j Setup Script](guides/setup_neo4j.sh)** - Automated Neo4j setup script

### **🎯 Features**
- **[Feature Checklist](features/FEATURE_CHECKLIST.md)** - Complete feature implementation status
- **[Geographic Bias Feature](features/GEOGRAPHIC_BIAS_FEATURE.md)** - Cross-country bias analysis
- **[Implementation Summary](features/IMPLEMENTATION_SUMMARY.md)** - Feature implementation overview
- **[Dashboard Organization](features/DASHBOARD_ORGANIZATION.md)** - Dashboard structure and navigation

### **🚀 Deployment**
- **[Project Summary](deployment/PROJECT_SUMMARY.md)** - Complete project overview and status
- **[Website Update Summary](deployment/WEBSITE_UPDATE_SUMMARY.md)** - Website updates and changes
- **[Website Analysis](deployment/FAIRMIND_WEBSITE_ANALYSIS.md)** - Website analysis and improvements
- **[Demo Deployment Script](deployment/deploy-demo.sh)** - Automated demo deployment

### **🏗️ Architecture**
- **[Architecture Overview](architecture/ARCHITECTURE.md)** - System architecture and design
- **[Folder Organization](architecture/FOLDER_ORGANIZATION.md)** - Project structure and organization
- **[Test Servers](architecture/test-servers.md)** - Development server setup
- **[Supabase Test](architecture/test-supabase.js)** - Supabase connection testing

### **⚙️ Setup**
- **[Email Configuration](setup/email-config.md)** - Email service setup
- **[Environment Template](setup/env.template)** - Environment variables template

### **📋 Development**
- **[Feature Checklist](features/FEATURE_CHECKLIST.md)** - Development progress tracking
- **[Folder Organization](architecture/FOLDER_ORGANIZATION.md)** - Project structure organization

## 🚀 **Quick Links**

### **Getting Started**
1. [Main README](../README.md) - Project overview and quick start
2. [Neo4j Quick Setup](guides/QUICK_NEO4J_SETUP.md) - Set up knowledge graph
3. [Demo Deployment](deployment/deploy-demo.sh) - Deploy demo to Netlify

### **Development**
1. [Feature Checklist](features/FEATURE_CHECKLIST.md) - Track development progress
2. [Architecture Overview](architecture/ARCHITECTURE.md) - Understand system design
3. [Folder Organization](architecture/FOLDER_ORGANIZATION.md) - Navigate project structure

### **Deployment**
1. [Demo Deployment](deployment/deploy-demo.sh) - Deploy to demo subdomain
2. [Project Summary](deployment/PROJECT_SUMMARY.md) - Complete project status
3. [Environment Setup](setup/env.template) - Configure environment variables

## 📊 **Live Demo**

**Try the platform:** [app-demo.fairmind.xyzp](https://app-demo.fairmind.xyz/)

The demo starts with an empty dashboard. Click "Load Demo Data" to explore all features.

## 🔧 **Development Workflow**

1. **Setup**: Follow the [Neo4j Quick Setup](guides/QUICK_NEO4J_SETUP.md)
2. **Development**: Use the [Feature Checklist](features/FEATURE_CHECKLIST.md) to track progress
3. **Testing**: Run the [test servers](architecture/test-servers.md)
4. **Deployment**: Use the [demo deployment script](deployment/deploy-demo.sh)

## 📝 **Contributing to Documentation**

When adding new documentation:

1. **Guides**: Place in `guides/` for setup and configuration
2. **Features**: Place in `features/` for feature descriptions
3. **Deployment**: Place in `deployment/` for deployment guides
4. **Architecture**: Place in `architecture/` for system design
5. **Setup**: Place in `setup/` for configuration files

Update this README.md to include new documentation files.

## 📁 **Complete Directory Structure**

```
docs/
├── README.md                    # This documentation index
├── guides/                      # Setup and configuration guides
│   ├── QUICK_NEO4J_SETUP.md
│   ├── NEO4J_SETUP_GUIDE.md
│   └── setup_neo4j.sh
├── features/                    # Feature descriptions and implementations
│   ├── FEATURE_CHECKLIST.md
│   ├── GEOGRAPHIC_BIAS_FEATURE.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── DASHBOARD_ORGANIZATION.md
├── deployment/                  # Deployment guides and scripts
│   ├── PROJECT_SUMMARY.md
│   ├── WEBSITE_UPDATE_SUMMARY.md
│   ├── FAIRMIND_WEBSITE_ANALYSIS.md
│   └── deploy-demo.sh
├── architecture/                # System architecture and design
│   ├── ARCHITECTURE.md
│   ├── FOLDER_ORGANIZATION.md
│   ├── test-servers.md
│   └── test-supabase.js
├── setup/                       # Configuration files and setup guides
│   ├── email-config.md
│   └── env.template
├── api/                         # API documentation
├── auth/                        # Authentication documentation
├── migrations/                  # Database migration guides
└── v2/                         # Website documentation
```
