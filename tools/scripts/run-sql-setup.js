const { createClient } = require('@supabase/supabase-js');
const path = require('path');
const dotenv = require('dotenv');
const fs = require('fs');

// Load environment variables from .env.local
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY;

console.log('=== Running SQL Setup via Supabase Client ===');
console.log(`SUPABASE_URL: ${supabaseUrl}`);
console.log(`SUPABASE_KEY: ${supabaseKey ? 'Found' : 'Missing'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Error: Missing Supabase credentials');
  process.exit(1);
}

async function runSQLSetup() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    console.log('🔌 Connecting to Supabase...');
    
    // Read the SQL file
    const sqlPath = path.resolve(__dirname, 'setup-database.sql');
    const sqlContent = fs.readFileSync(sqlPath, 'utf8');
    
    console.log('📝 Running SQL setup...');
    
    // Split SQL into individual statements
    const statements = sqlContent
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0 && !stmt.startsWith('--'));
    
    console.log(`Found ${statements.length} SQL statements to execute`);
    
    // Execute each statement
    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i];
      if (statement.trim()) {
        try {
          console.log(`Executing statement ${i + 1}/${statements.length}...`);
          
          // Use rpc to execute SQL
          const { data, error } = await supabase.rpc('exec_sql', {
            sql_query: statement
          });
          
          if (error) {
            console.log(`⚠️  Statement ${i + 1} had an issue:`, error.message);
            // Continue with other statements
          } else {
            console.log(`✅ Statement ${i + 1} executed successfully`);
          }
        } catch (e) {
          console.log(`⚠️  Statement ${i + 1} failed:`, e.message);
          // Continue with other statements
        }
      }
    }
    
    console.log('🎉 SQL setup completed!');
    
    // Test the connection
    console.log('🧪 Testing connection...');
    const { data: testData, error: testError } = await supabase
      .from('profiles')
      .select('count')
      .limit(1);
    
    if (testError) {
      console.log('⚠️  Connection test failed:', testError.message);
    } else {
      console.log('✅ Connection test successful!');
    }
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
  }
}

// Alternative approach: Use direct SQL execution
async function runDirectSQL() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    console.log('🔌 Attempting direct SQL execution...');
    
    // Try to create a simple table first
    const { error: createError } = await supabase
      .from('test_table')
      .select('*')
      .limit(1);
    
    if (createError && createError.message.includes('does not exist')) {
      console.log('✅ Connection works, but tables need to be created');
      console.log('📋 Please run the SQL manually in Supabase dashboard');
      console.log('   Or install Supabase CLI for automated setup');
    } else {
      console.log('✅ Connection successful!');
    }
    
  } catch (error) {
    console.error('❌ Direct SQL failed:', error.message);
  }
}

// Try both approaches
runSQLSetup().then(() => {
  console.log('\n📋 Next steps:');
  console.log('1. If SQL setup worked, run: node quick-setup.js');
  console.log('2. If not, run SQL manually in Supabase dashboard');
  console.log('3. Or install Supabase CLI: npm install -g supabase');
});
