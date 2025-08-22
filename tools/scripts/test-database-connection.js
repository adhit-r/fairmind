const { createClient } = require('@supabase/supabase-js');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env.local
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY;

console.log('=== Testing Supabase Connection ===');
console.log(`SUPABASE_URL: ${supabaseUrl}`);
console.log(`SUPABASE_KEY: ${supabaseKey ? 'Found' : 'Missing'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Error: Missing Supabase credentials');
  process.exit(1);
}

async function testConnection() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    console.log('🔌 Testing connection...');
    
    // Test basic connection
    const { data, error } = await supabase.from('profiles').select('count').limit(1);
    
    if (error) {
      console.error('❌ Connection failed:', error.message);
      return false;
    }
    
    console.log('✅ Connection successful!');
    
    // Test if tables exist
    console.log('📋 Checking tables...');
    
    const tables = ['profiles', 'organizations', 'ai_models', 'bias_analyses'];
    
    for (const table of tables) {
      try {
        const { error: tableError } = await supabase.from(table).select('count').limit(1);
        if (tableError) {
          console.log(`❌ Table ${table}: ${tableError.message}`);
        } else {
          console.log(`✅ Table ${table}: exists`);
        }
      } catch (e) {
        console.log(`❌ Table ${table}: ${e.message}`);
      }
    }
    
    return true;
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    return false;
  }
}

testConnection().then((success) => {
  if (success) {
    console.log('\n🎉 Database connection test passed!');
    console.log('\n📋 Next steps:');
    console.log('1. Run the SQL setup in Supabase dashboard');
    console.log('2. Test authentication');
    console.log('3. Replace mock data with real queries');
  } else {
    console.log('\n❌ Database connection test failed!');
    console.log('Please check your Supabase credentials and run the SQL setup.');
  }
});
