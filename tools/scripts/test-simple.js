const { PrismaClient } = require('@prisma/client');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const prisma = new PrismaClient();

async function testSimple() {
  try {
    console.log('🔍 Simple test starting...');
    
    // Test connection
    await prisma.$connect();
    console.log('✅ Connected to database');
    
    // Test simple query
    const profiles = await prisma.profile.findMany({
      take: 1
    });
    
    console.log('📊 Found profiles:', profiles.length);
    
    // Return JSON result
    console.log(JSON.stringify({
      success: true,
      data: profiles,
      count: profiles.length,
      message: 'Test successful'
    }));
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    console.log(JSON.stringify({
      success: false,
      error: error.message,
      message: 'Test failed'
    }));
  } finally {
    await prisma.$disconnect();
  }
}

testSimple();
