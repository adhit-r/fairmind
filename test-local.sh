#!/bin/bash

echo "🧪 Testing FairMind Platform Locally"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${YELLOW}1. Testing Backend API...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend API is running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend API is not responding${NC}"
    exit 1
fi

echo -e "\n${YELLOW}2. Testing Frontend...${NC}"
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend is running on http://localhost:3000${NC}"
else
    echo -e "${RED}❌ Frontend is not responding${NC}"
    exit 1
fi

echo -e "\n${YELLOW}3. Testing Dashboard...${NC}"
if curl -s http://localhost:3000/dashboard > /dev/null; then
    echo -e "${GREEN}✅ Dashboard is accessible${NC}"
else
    echo -e "${RED}❌ Dashboard is not accessible${NC}"
fi

echo -e "\n${YELLOW}4. Testing Model Upload...${NC}"
if curl -s http://localhost:3000/model-upload > /dev/null; then
    echo -e "${GREEN}✅ Model Upload page is accessible${NC}"
else
    echo -e "${RED}❌ Model Upload page is not accessible${NC}"
fi

echo -e "\n${YELLOW}5. Testing Model Testing...${NC}"
if curl -s http://localhost:3000/model-testing > /dev/null; then
    echo -e "${GREEN}✅ Model Testing page is accessible${NC}"
else
    echo -e "${RED}❌ Model Testing page is not accessible${NC}"
fi

echo -e "\n${YELLOW}6. Testing Analytics...${NC}"
if curl -s http://localhost:3000/analytics > /dev/null; then
    echo -e "${GREEN}✅ Analytics page is accessible${NC}"
else
    echo -e "${RED}❌ Analytics page is not accessible${NC}"
fi

echo -e "\n${GREEN}🎉 Local Testing Complete!${NC}"
echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  Dashboard: ${GREEN}http://localhost:3000/dashboard${NC}"
echo -e "  Model Upload: ${GREEN}http://localhost:3000/model-upload${NC}"
echo -e "  Model Testing: ${GREEN}http://localhost:3000/model-testing${NC}"
echo -e "  Analytics: ${GREEN}http://localhost:3000/analytics${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "  Health Check: ${GREEN}http://localhost:8000/health${NC}"

echo -e "\n${YELLOW}Ready for SQ1 Demo! 🚀${NC}"
