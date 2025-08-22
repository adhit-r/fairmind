const { PrismaClient } = require('@prisma/client');
const path = require('path');
const dotenv = require('dotenv');

// Suppress dotenv output
process.env.DOTENV_CONFIG_SILENT = 'true';
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const prisma = new PrismaClient();

async function getProfiles() {
  try {
    const limit = parseInt(process.argv[2]) || 10;
    
    const profiles = await prisma.profile.findMany({
      take: limit,
      orderBy: {
        createdAt: 'desc'
      }
    });
    
    // Only output the JSON result
    process.stdout.write(JSON.stringify({
      success: true,
      data: profiles
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

getProfiles();
