const { createClient } = require('@supabase/supabase-js');
const path = require('path');
const dotenv = require('dotenv');
const fs = require('fs');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY;

console.log('🔧 Creating missing enum types...');

async function createEnums() {
  try {
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    // Read the SQL file
    const sqlPath = path.resolve(__dirname, 'create-enums.sql');
    const sqlContent = fs.readFileSync(sqlPath, 'utf8');
    
    console.log('📝 Running enum creation SQL...');
    
    // Split SQL into individual statements and filter out comments
    const statements = sqlContent
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0 && !stmt.startsWith('--') && !stmt.startsWith('/*'));
    
    console.log(`Found ${statements.length} SQL statements to execute`);
    
    // Execute each statement using raw SQL
    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i].trim();
      if (statement && !statement.startsWith('SELECT')) {
        try {
          console.log(`Executing statement ${i + 1}: ${statement.substring(0, 50)}...`);
          
          const { data, error } = await supabase.rpc('exec_sql', { sql_query: statement });
          
          if (error) {
            if (error.message.includes('already exists')) {
              console.log(`✅ Statement ${i + 1}: Already exists (skipping)`);
            } else {
              console.log(`⚠️  Statement ${i + 1}: ${error.message}`);
            }
          } else {
            console.log(`✅ Statement ${i + 1}: Success`);
          }
        } catch (e) {
          if (e.message.includes('already exists')) {
            console.log(`✅ Statement ${i + 1}: Already exists (skipping)`);
          } else {
            console.log(`⚠️  Statement ${i + 1}: ${e.message}`);
          }
        }
      }
    }
    
    // Test enum creation by trying to use them
    console.log('\n🧪 Testing enum types...');
    
    const { data: enumTest, error: enumError } = await supabase
      .from('geographic_bias_analyses')
      .select('risk_level')
      .limit(1);
    
    if (enumError) {
      console.log('⚠️  Enum test failed:', enumError.message);
      console.log('💡 You may need to run the SQL manually in Supabase dashboard');
    } else {
      console.log('✅ Enum types are working!');
    }
    
    console.log('\n🎉 Enum creation completed!');
    
  } catch (error) {
    console.error('❌ Error creating enums:', error.message);
    console.log('\n💡 If this fails, run the SQL manually in Supabase dashboard:');
    console.log('1. Go to: https://supabase.com/dashboard/project/swapkvhzyhcruoyjpkyr');
    console.log('2. SQL Editor → New Query');
    console.log('3. Copy content from: tools/scripts/create-enums.sql');
    console.log('4. Paste and Run');
  }
}

createEnums();
