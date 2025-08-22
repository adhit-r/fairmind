const { PrismaClient } = require('@prisma/client');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

const prisma = new PrismaClient();

async function testConnection() {
  try {
    console.log('🔌 Testing Prisma connection...');
    
    // Test basic connection
    await prisma.$connect();
    console.log('✅ Prisma connected successfully!');
    
    // Test querying existing data
    console.log('\n📊 Testing existing data...');
    
    // Check profiles table
    const profiles = await prisma.profile.findMany({
      take: 5
    });
    console.log(`📋 Found ${profiles.length} profiles`);
    
    // Check geographic bias analyses
    const biasAnalyses = await prisma.geographicBiasAnalysis.findMany({
      take: 5
    });
    console.log(`📋 Found ${biasAnalyses.length} geographic bias analyses`);
    
    // Check audit logs
    const auditLogs = await prisma.auditLog.findMany({
      take: 5
    });
    console.log(`📋 Found ${auditLogs.length} audit logs`);
    
    // Check country performance metrics
    const countryMetrics = await prisma.countryPerformanceMetric.findMany({
      take: 5
    });
    console.log(`📋 Found ${countryMetrics.length} country performance metrics`);
    
    // Check cultural factors
    const culturalFactors = await prisma.culturalFactor.findMany({
      take: 5
    });
    console.log(`📋 Found ${culturalFactors.length} cultural factors`);
    
    console.log('\n🎉 All queries successful! Prisma is working with your existing data.');
    
    // Show sample data
    if (profiles.length > 0) {
      console.log('\n👤 Sample profile:');
      console.log(JSON.stringify(profiles[0], null, 2));
    }
    
    if (biasAnalyses.length > 0) {
      console.log('\n🔍 Sample bias analysis:');
      console.log(JSON.stringify(biasAnalyses[0], null, 2));
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    
    if (error.message.includes('does not exist')) {
      console.log('\n💡 The table doesn\'t exist yet. You need to run the SQL setup first.');
      console.log('Go to Supabase dashboard and run the SQL from setup-database.sql');
    }
  } finally {
    await prisma.$disconnect();
  }
}

async function createSampleData() {
  try {
    console.log('\n📝 Creating sample data...');
    
    // Create a sample profile (if none exist)
    const existingProfiles = await prisma.profile.findMany();
    if (existingProfiles.length === 0) {
      const newProfile = await prisma.profile.create({
        data: {
          id: '00000000-0000-0000-0000-000000000000',
          username: 'admin',
          fullName: 'System Administrator',
          role: 'admin'
        }
      });
      console.log('✅ Created sample profile:', newProfile.username);
    } else {
      console.log('✅ Profiles already exist');
    }
    
    // Create sample geographic bias analysis
    const newAnalysis = await prisma.geographicBiasAnalysis.create({
      data: {
        modelId: 'sample-model-001',
        sourceCountry: 'US',
        targetCountry: 'UK',
        biasScore: 0.15,
        riskLevel: 'low',
        culturalFactors: {
          language: 'en',
          cultural_norms: 'similar'
        },
        createdBy: existingProfiles.length > 0 ? existingProfiles[0].id : '00000000-0000-0000-0000-000000000000'
      }
    });
    console.log('✅ Created sample bias analysis:', newAnalysis.id);
    
    // Create sample audit log
    const newAuditLog = await prisma.auditLog.create({
      data: {
        action: 'model_upload',
        resourceType: 'ai_model',
        resourceId: 'sample-model-001',
        details: {
          file_size: 1024000,
          model_type: 'classification'
        },
        ipAddress: '127.0.0.1',
        userAgent: 'FairMind/1.0',
        userId: existingProfiles.length > 0 ? existingProfiles[0].id : null
      }
    });
    console.log('✅ Created sample audit log:', newAuditLog.id);
    
    console.log('\n🎉 Sample data created successfully!');
    
  } catch (error) {
    console.error('❌ Error creating sample data:', error.message);
  }
}

// Run tests
testConnection()
  .then(() => createSampleData())
  .then(() => {
    console.log('\n📋 Next steps:');
    console.log('1. ✅ Prisma is working with your database');
    console.log('2. ✅ You can now use Prisma in your application');
    console.log('3. 🔄 Update your backend to use Prisma instead of raw SQL');
    console.log('4. 🔄 Update your frontend to use the new Prisma-based API');
  })
  .catch(console.error);
