const { PrismaClient } = require('@prisma/client');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const prisma = new PrismaClient();

async function debugDatabase() {
  try {
    console.log('🔍 Debugging database connection...');
    console.log('Environment variables loaded from:', path.resolve(__dirname, '../../.env'));
    console.log('DATABASE_URL:', process.env.DATABASE_URL ? 'Found' : 'Missing');
    
    // Test connection
    await prisma.$connect();
    console.log('✅ Prisma connected successfully!');
    
    // Test profiles table
    console.log('\n📊 Testing profiles table...');
    const profiles = await prisma.profile.findMany({
      take: 5
    });
    console.log(`Found ${profiles.length} profiles:`, profiles);
    
    // Test geographic bias analyses table
    console.log('\n📊 Testing geographic bias analyses table...');
    const analyses = await prisma.geographicBiasAnalysis.findMany({
      take: 5
    });
    console.log(`Found ${analyses.length} analyses:`, analyses);
    
    // Test audit logs table
    console.log('\n📊 Testing audit logs table...');
    const logs = await prisma.auditLog.findMany({
      take: 5
    });
    console.log(`Found ${logs.length} audit logs:`, logs);
    
    // Test country metrics table
    console.log('\n📊 Testing country metrics table...');
    const metrics = await prisma.countryPerformanceMetric.findMany({
      take: 5
    });
    console.log(`Found ${metrics.length} country metrics:`, metrics);
    
    console.log('\n🎉 All database queries successful!');
    
  } catch (error) {
    console.error('❌ Database error:', error.message);
    console.error('Full error:', error);
  } finally {
    await prisma.$disconnect();
  }
}

debugDatabase();
