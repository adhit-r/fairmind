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
    // Read all migration files
    const migrationsDir = path.join(__dirname, 'supabase-migrations');
    const migrationFiles = fs.readdirSync(migrationsDir)
      .filter(file => file.endsWith('.sql'))
      .sort(); // Apply migrations in order

    console.log(`📦 Found ${migrationFiles.length} migration(s) to apply`);

    for (const file of migrationFiles) {
      console.log(`\n🔧 Applying migration: ${file}`);
      const migration = fs.readFileSync(path.join(migrationsDir, file), 'utf8');
      
      // Split the migration into individual statements
      const statements = migration
        .split(';')
        .map(s => s.trim())
        .filter(s => s.length > 0);

      // Execute each statement
      for (const [index, statement] of statements.entries()) {
        try {
          console.log(`  → [${index + 1}/${statements.length}] Executing statement...`);
          const { error } = await supabase.rpc('exec_sql', { query: statement + ';' });
          
          if (error) {
            // If the function doesn't exist, create it
            if (error.message.includes('function exec_sql(unknown) does not exist')) {
              console.log('  ℹ️  Creating exec_sql function...');
              const createFnSql = `
                create or replace function exec_sql(query text) 
                returns json as $$
                declare
                  result json;
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
                $$ language plpgsql security definer;
              `;
              
              await supabase.rpc('exec_sql', { query: createFnSql });
              
              // Retry the original statement
              const retry = await supabase.rpc('exec_sql', { query: statement + ';' });
              if (retry.error) throw retry.error;
            } else {
              throw error;
            }
          }
        } catch (err) {
          console.error(`❌ Error in statement ${index + 1}:`);
          console.error(statement);
          console.error('Error:', err.message);
          console.error('\n⚠️  Migration failed. Please check the error above.');
          process.exit(1);
        }
      }
      
      console.log(`✅ Applied migration: ${file}`);
    }

    console.log('\n🎉 All migrations applied successfully!');
    
  } catch (err) {
    console.error('❌ Error applying migrations:');
    console.error(err);
    process.exit(1);
  }
}

// Run the migrations
applyMigrations();
