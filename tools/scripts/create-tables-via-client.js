const { createClient } = require('@supabase/supabase-js');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env.local
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY;

console.log('=== Creating Tables via Supabase Client ===');
console.log(`SUPABASE_URL: ${supabaseUrl}`);
console.log(`SUPABASE_KEY: ${supabaseKey ? 'Found' : 'Missing'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Error: Missing Supabase credentials');
  process.exit(1);
}

async function createTables() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    console.log('🔌 Connecting to Supabase...');
    
    // Test connection first
    const { error: testError } = await supabase
      .from('profiles')
      .select('count')
      .limit(1);
    
    if (testError && testError.message.includes('does not exist')) {
      console.log('✅ Connection works, but tables need to be created');
    } else if (testError) {
      console.log('❌ Connection failed:', testError.message);
      return;
    } else {
      console.log('✅ Tables already exist!');
      return;
    }
    
    console.log('📝 Creating tables programmatically...');
    
    // Create profiles table by inserting a test record
    console.log('Creating profiles table...');
    try {
      const { error: profileError } = await supabase
        .from('profiles')
        .insert({
          id: '00000000-0000-0000-0000-000000000000',
          username: 'admin_test',
          role: 'admin'
        });
      
      if (profileError && profileError.message.includes('does not exist')) {
        console.log('⚠️  Profiles table does not exist - need to create via SQL');
      } else if (profileError) {
        console.log('⚠️  Profile creation issue:', profileError.message);
      } else {
        console.log('✅ Profiles table created/accessed successfully');
      }
    } catch (e) {
      console.log('⚠️  Profiles table creation failed:', e.message);
    }
    
    // Try to create organizations table
    console.log('Creating organizations table...');
    try {
      const { error: orgError } = await supabase
        .from('organizations')
        .insert({
          id: '00000000-0000-0000-0000-000000000001',
          name: 'Demo Organization',
          domain: 'demo.fairmind.xyz',
          created_by: '00000000-0000-0000-0000-000000000000'
        });
      
      if (orgError && orgError.message.includes('does not exist')) {
        console.log('⚠️  Organizations table does not exist - need to create via SQL');
      } else if (orgError) {
        console.log('⚠️  Organization creation issue:', orgError.message);
      } else {
        console.log('✅ Organizations table created/accessed successfully');
      }
    } catch (e) {
      console.log('⚠️  Organizations table creation failed:', e.message);
    }
    
    // Try to create AI models table
    console.log('Creating AI models table...');
    try {
      const { error: modelError } = await supabase
        .from('ai_models')
        .insert({
          id: '00000000-0000-0000-0000-000000000002',
          name: 'Test Model',
          version: '1.0.0',
          model_type: 'classification',
          organization_id: '00000000-0000-0000-0000-000000000001',
          created_by: '00000000-0000-0000-0000-000000000000'
        });
      
      if (modelError && modelError.message.includes('does not exist')) {
        console.log('⚠️  AI models table does not exist - need to create via SQL');
      } else if (modelError) {
        console.log('⚠️  AI model creation issue:', modelError.message);
      } else {
        console.log('✅ AI models table created/accessed successfully');
      }
    } catch (e) {
      console.log('⚠️  AI models table creation failed:', e.message);
    }
    
    console.log('\n📋 Summary:');
    console.log('The Supabase client cannot create tables directly.');
    console.log('You need to run the SQL setup in one of these ways:');
    console.log('');
    console.log('Option 1: Manual SQL (Recommended)');
    console.log('1. Go to: https://supabase.com/dashboard/project/swapkvhzyhcruoyjpkyr');
    console.log('2. SQL Editor → New Query');
    console.log('3. Copy content from: tools/scripts/setup-database.sql');
    console.log('4. Paste and Run');
    console.log('');
    console.log('Option 2: Install Supabase CLI');
    console.log('npm install -g supabase');
    console.log('supabase db push');
    console.log('');
    console.log('Option 3: Use Supabase Dashboard');
    console.log('Go to Database → Tables → Create table manually');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
  }
}

createTables();
