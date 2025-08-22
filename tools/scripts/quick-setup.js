const { createClient } = require('@supabase/supabase-js');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env.local
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY;

console.log('=== Quick Supabase Setup ===');
console.log(`SUPABASE_URL: ${supabaseUrl}`);
console.log(`SUPABASE_KEY: ${supabaseKey ? 'Found' : 'Missing'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Error: Missing Supabase credentials');
  process.exit(1);
}

async function quickSetup() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    console.log('🔌 Connecting to Supabase...');
    
    // Test connection first
    const { error: testError } = await supabase.from('profiles').select('count').limit(1);
    
    if (testError && testError.message.includes('permission denied')) {
      console.log('⚠️  Database schema not set up yet. Please run the SQL setup first.');
      console.log('\n📋 Manual Setup Required:');
      console.log('1. Go to: https://supabase.com/dashboard/project/swapkvhzyhcruoyjpkyr');
      console.log('2. Click "SQL Editor" → "New Query"');
      console.log('3. Copy and paste the content from: tools/scripts/setup-database.sql');
      console.log('4. Click "Run"');
      console.log('5. Then run this script again');
      return false;
    }
    
    console.log('✅ Database schema is ready!');
    
    // Create demo data
    console.log('📝 Creating demo data...');
    
    // Create demo organization
    const { data: org, error: orgError } = await supabase
      .from('organizations')
      .insert({
        id: '00000000-0000-0000-0000-000000000001',
        name: 'Demo Organization',
        domain: 'demo.fairmind.xyz',
        created_by: '00000000-0000-0000-0000-000000000000'
      })
      .select()
      .single();
    
    if (orgError && !orgError.message.includes('duplicate key')) {
      console.error('❌ Error creating organization:', orgError.message);
    } else {
      console.log('✅ Demo organization created');
    }
    
    // Create demo models
    const demoModels = [
      {
        name: 'Credit Risk Model',
        version: '1.0.0',
        model_type: 'classification',
        framework: 'scikit-learn',
        description: 'ML model for credit risk assessment',
        organization_id: '00000000-0000-0000-0000-000000000001',
        created_by: '00000000-0000-0000-0000-000000000000',
        metadata: {
          accuracy: 0.85,
          precision: 0.82,
          recall: 0.78,
          f1_score: 0.80
        }
      },
      {
        name: 'Fraud Detection Model',
        version: '2.1.0',
        model_type: 'classification',
        framework: 'tensorflow',
        description: 'AI model for detecting fraudulent transactions',
        organization_id: '00000000-0000-0000-0000-000000000001',
        created_by: '00000000-0000-0000-0000-000000000000',
        metadata: {
          accuracy: 0.92,
          precision: 0.89,
          recall: 0.91,
          f1_score: 0.90
        }
      },
      {
        name: 'Customer Segmentation Model',
        version: '1.5.0',
        model_type: 'clustering',
        framework: 'scikit-learn',
        description: 'Unsupervised model for customer segmentation',
        organization_id: '00000000-0000-0000-0000-000000000001',
        created_by: '00000000-0000-0000-0000-000000000000',
        metadata: {
          silhouette_score: 0.75,
          n_clusters: 5,
          inertia: 0.45
        }
      }
    ];
    
    for (const model of demoModels) {
      const { error: modelError } = await supabase
        .from('ai_models')
        .insert(model);
      
      if (modelError && !modelError.message.includes('duplicate key')) {
        console.error(`❌ Error creating model ${model.name}:`, modelError.message);
      } else {
        console.log(`✅ Demo model created: ${model.name}`);
      }
    }
    
    console.log('\n🎉 Quick setup completed!');
    console.log('\n📋 Demo Credentials:');
    console.log('Email: admin@fairmind.app');
    console.log('Password: admin123');
    console.log('\n📋 Next steps:');
    console.log('1. Test authentication in your frontend');
    console.log('2. Replace mock data with real database queries');
    console.log('3. Set up real user authentication');
    
    return true;
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    return false;
  }
}

quickSetup().catch(console.error);
