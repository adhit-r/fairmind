const { PrismaClient } = require('@prisma/client');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables silently
dotenv.config({ path: path.resolve(__dirname, '../../.env'), silent: true });

const prisma = new PrismaClient();

async function getCountryMetrics() {
  try {
    const limit = parseInt(process.argv[2]) || 10;
    
    const metrics = await prisma.countryPerformanceMetric.findMany({
      take: limit,
      orderBy: {
        lastUpdated: 'desc'
      }
    });
    
    // Only output the JSON result
    process.stdout.write(JSON.stringify({
      success: true,
      data: metrics
    }));
    
  } catch (error) {
    process.stdout.write(JSON.stringify({
      success: false,
      error: error.message
    }));
  } finally {
    await prisma.$disconnect();
  }
}

getCountryMetrics();
