import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../apps/web/.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Error: Missing Supabase URL or Anon Key in environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function applyMigrations() {
  console.log('🚀 Starting database migrations...');
  
  try {
    // Read the migration file
    const migrationPath = path.join(__dirname, 'supabase-migrations/001_initial_schema.sql');
    const migration = fs.readFileSync(migrationPath, 'utf8');
    
    console.log('🔧 Applying migration: 001_initial_schema.sql');
    
    // Split into individual statements
    const statements = migration
      .split(';')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    // Execute each statement
    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i];
      console.log(`  → [${i + 1}/${statements.length}] Executing statement...`);
      
      try {
        // Use the SQL endpoint directly
        const { error } = await supabase.rpc('pg_temp.exec_sql', { query: statement + ';' });
        
        if (error) {
          // If the temp function doesn't exist, create it
          if (error.message.includes('function pg_temp.exec_sql(unknown) does not exist')) {
            console.log('  ℹ️  Creating temporary exec_sql function...');
            const createFnSql = `
              create or replace function pg_temp.exec_sql(query text) 
              returns json as $$
              begin
                execute query;
                return json_build_object('success', true);
              exception when others then
                return json_build_object(
                  'success', false,
                  'error', SQLERRM,
                  'detail', SQLSTATE
                );
              end;
              $$ language plpgsql;
            `;
            
            // Create the temp function
            await supabase.rpc('pg_temp.exec_sql', { query: createFnSql });
            
            // Retry the original statement
            const retry = await supabase.rpc('pg_temp.exec_sql', { query: statement + ';' });
            if (retry.error) throw retry.error;
          } else {
            throw error;
          }
        }
      } catch (err) {
        console.error(`❌ Error in statement ${i + 1}:`);
        console.error(statement);
        console.error('Error:', err.message);
        console.error('\n⚠️  Migration failed. Please check the error above.');
        process.exit(1);
      }
    }
    
    console.log('✅ Migration applied successfully!');
    
  } catch (err) {
    console.error('❌ Error applying migrations:');
    console.error(err);
    process.exit(1);
  }
}

// Run the migrations
applyMigrations();
