const { PrismaClient } = require('@prisma/client');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables silently
dotenv.config({ path: path.resolve(__dirname, '../../.env'), silent: true });

const prisma = new PrismaClient();

async function getBiasAnalyses() {
  try {
    const limit = parseInt(process.argv[2]) || 10;
    
    const analyses = await prisma.geographicBiasAnalysis.findMany({
      take: limit,
      orderBy: {
        analysisDate: 'desc'
      },
      include: {
        creator: {
          select: {
            id: true,
            username: true,
            fullName: true
          }
        }
      }
    });
    
    // Only output the JSON result
    process.stdout.write(JSON.stringify({
      success: true,
      data: analyses
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

getBiasAnalyses();
