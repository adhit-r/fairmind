# Fairmind Frontend Deployment Guide

## 🚀 **Production Deployment to https://app-demo.fairmind.xyz**

### **Overview**
This guide covers deploying the Fairmind AI Governance Platform frontend to production with API integration to `https://api.fairmind.xyz`.

### **✅ Build Status**
- **Build**: ✅ Successful
- **Static Export**: ✅ Complete
- **API Configuration**: ✅ Production ready
- **Environment Variables**: ✅ Configured

### **📁 Build Output**
The build has generated static files in the `./out/` directory:
- **Total Pages**: 42 pages
- **Bundle Size**: Optimized for production
- **Static Export**: Complete with all assets

### **🌐 Deployment Options**

#### **Option 1: Netlify Deployment (Recommended)**
```bash
# 1. Install Netlify CLI
npm install -g netlify-cli

# 2. Deploy to Netlify
netlify deploy --prod --dir=out

# 3. Configure custom domain
netlify domains:add app-demo.fairmind.xyz
```

#### **Option 2: Vercel Deployment**
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy to Vercel
vercel --prod

# 3. Configure custom domain in Vercel dashboard
```

#### **Option 3: Manual Server Deployment**
```bash
# 1. Upload contents of ./out/ to your web server
# 2. Configure nginx/apache to serve static files
# 3. Set up SSL certificates
# 4. Configure CORS headers
```

### **🔧 Configuration Files**

#### **Production Environment**
- **API URL**: `https://api.fairmind.xyz`
- **App URL**: `https://app-demo.fairmind.xyz`
- **Environment**: `production`

#### **Netlify Configuration** (`netlify.toml`)
```toml
[build]
  publish = "out"
  command = "bun run build"

[build.environment]
  NEXT_PUBLIC_API_URL = "https://api.fairmind.xyz"
  NEXT_PUBLIC_APP_URL = "https://app-demo.fairmind.xyz"
  NEXT_PUBLIC_ENVIRONMENT = "production"

[[redirects]]
  from = "/api/*"
  to = "https://api.fairmind.xyz/:splat"
  status = 200
  force = true
```

#### **Vercel Configuration** (`vercel.json`)
```json
{
  "version": 2,
  "name": "fairmind-frontend",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.fairmind.xyz",
    "NEXT_PUBLIC_APP_URL": "https://app-demo.fairmind.xyz",
    "NEXT_PUBLIC_ENVIRONMENT": "production"
  }
}
```

### **🔒 Security Headers**
The application includes security headers:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: origin-when-cross-origin`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### **📊 Performance Optimization**
- **Static Export**: All pages pre-rendered
- **Code Splitting**: Optimized bundle sizes
- **Image Optimization**: Enabled
- **Caching**: Static assets cached for 1 year

### **🔗 API Integration**
- **Base URL**: `https://api.fairmind.xyz`
- **CORS**: Configured for cross-origin requests
- **Authentication**: Supabase integration
- **Real-time**: WebSocket support

### **📋 Deployment Checklist**

#### **Pre-Deployment**
- [x] Build successful
- [x] All TypeScript errors resolved
- [x] Environment variables configured
- [x] API endpoints tested
- [x] Security headers configured

#### **Deployment Steps**
- [ ] Choose deployment platform
- [ ] Upload build files
- [ ] Configure custom domain
- [ ] Set up SSL certificates
- [ ] Test all functionality
- [ ] Monitor performance

#### **Post-Deployment**
- [ ] Verify API connectivity
- [ ] Test user authentication
- [ ] Check all features work
- [ ] Monitor error logs
- [ ] Set up analytics

### **🚨 Troubleshooting**

#### **Common Issues**
1. **CORS Errors**: Ensure API server allows requests from `https://app-demo.fairmind.xyz`
2. **404 Errors**: Check that all static files are uploaded
3. **API Connection**: Verify `https://api.fairmind.xyz` is accessible
4. **SSL Issues**: Ensure SSL certificates are properly configured

#### **Debug Commands**
```bash
# Check build output
ls -la out/

# Test API connectivity
curl -I https://api.fairmind.xyz/health

# Check SSL certificate
openssl s_client -connect app-demo.fairmind.xyz:443
```

### **📈 Monitoring & Analytics**

#### **Performance Monitoring**
- **Core Web Vitals**: Monitor LCP, FID, CLS
- **Error Tracking**: Set up error monitoring
- **Uptime Monitoring**: Monitor application availability

#### **Analytics Setup**
- **Google Analytics**: Track user behavior
- **Custom Events**: Monitor feature usage
- **Performance Metrics**: Track page load times

### **🔄 Continuous Deployment**

#### **GitHub Actions** (Optional)
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm install
      - run: npm run build
      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v2
        with:
          publish-dir: './out'
          production-branch: main
```

### **📞 Support**

#### **Deployment Issues**
- Check build logs for errors
- Verify environment variables
- Test API connectivity
- Review security headers

#### **Contact Information**
- **Technical Support**: Check deployment logs
- **API Issues**: Verify backend deployment
- **Domain Issues**: Check DNS configuration

---

## 🎯 **Next Steps**

1. **Choose Deployment Platform**: Select Netlify, Vercel, or manual deployment
2. **Deploy Application**: Follow platform-specific instructions
3. **Configure Domain**: Set up `app-demo.fairmind.xyz`
4. **Test Functionality**: Verify all features work correctly
5. **Monitor Performance**: Set up monitoring and analytics

**Your Fairmind AI Governance Platform is ready for production deployment!** 🚀
