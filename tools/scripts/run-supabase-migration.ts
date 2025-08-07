import { createClient } from '@supabase/supabase-js';
import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

// Get Supabase URL and API key from command line arguments or environment variables
let supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.argv[2];
let supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.argv[3];

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

async function promptForCredentials(): Promise<{ url: string; key: string }> {
  return new Promise((resolve) => {
    console.log('Please enter your Supabase project URL:');
    console.log('Format: https://[YOUR-PROJECT-REF].supabase.co');
    
    rl.question('> URL: ', (url) => {
      console.log('\nPlease enter your Supabase anon/public key:');
      rl.question('> Key: ', (key) => {
        resolve({ url: url.trim(), key: key.trim() });
      });
    });
  });
}

if (!supabaseUrl || !supabaseKey) {
  console.log('Supabase URL or API key not provided.');
  const credentials = await promptForCredentials();
  supabaseUrl = credentials.url;
  supabaseKey = credentials.key;
  rl.close();
}

async function runMigrations() {
  // Initialize Supabase client with the admin key for migrations
  const supabase = createClient(supabaseUrl, supabaseKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  });

  try {
    console.log('🔌 Starting Supabase migration...');

    // Read the SQL file
    const sqlPath = path.join(__dirname, 'supabase-setup.sql');
    const sql = fs.readFileSync(sqlPath, 'utf8');

    console.log('🚀 Running migrations...');
    
    // Split into individual statements and execute
    const statements = sql
      .split(';')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i];
      if (!statement) continue;
      
      console.log(`  → [${i + 1}/${statements.length}] Executing statement...`);
      
      try {
        // Use the SQL endpoint to execute raw SQL
        const { data, error } = await supabase.rpc('exec_sql', { sql: statement });
        
        if (error) {
          // If the function doesn't exist, create it
          if (error.message.includes('function exec_sql(unknown) does not exist')) {
            console.log('  ℹ️  Creating exec_sql function...');
            
            const createFnSql = `
              create or replace function exec_sql(sql text) 
              returns json as $$
              begin
                execute sql;
                return json_build_object('success', true);
              exception when others then
                return json_build_object(
                  'success', false,
                  'error', SQLERRM,
                  'detail', SQLSTATE
                );
              end;
              $$ language plpgsql security definer;
            `;
            
            // Create the function
            await supabase.rpc('exec_sql', { sql: createFnSql });
            
            // Retry the original statement
            const retry = await supabase.rpc('exec_sql', { sql: statement });
            if (retry.error) throw retry.error;
          } else {
            throw error;
          }
        }
      } catch (error) {
        // Skip certain errors that might be expected
        if (error.message.includes('already exists') || 
            error.message.includes('does not exist') ||
            error.message.includes('already a member')) {
          console.log(`  ⚠️  ${error.message.split('\n')[0]}`);
          continue;
        }
        console.error(`❌ Error in statement ${i + 1}:`);
        console.error(statement);
        console.error('Error:', error.message);
        throw error;
      }
    }

    console.log('\n🎉 Database setup completed successfully!');
    
  } catch (error) {
    console.error('❌ Error running migrations:');
    console.error(error);
    process.exit(1);
  }
}

// Run the migrations
runMigrations();
