import { createClient } from '@supabase/supabase-js';
import { execSync } from 'child_process';
import * as dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../apps/web/.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('Error: Missing Supabase URL or Anon Key in environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkSupabaseSetup() {
  // First, create the helper function if it doesn't exist
  const { error: createFnError } = await supabase.rpc('create_get_tables_function', {});
  
  if (createFnError && !createFnError.message.includes('already exists')) {
    console.error('❌ Error creating helper function:');
    console.error(createFnError);
    return;
  }
  console.log('🔍 Checking Supabase connection...');
  
  try {
    // Test connection by listing tables using raw SQL
    const { data: tables, error } = await supabase.rpc('get_tables');
    
    // If the function doesn't exist, create it
    if (error && error.message.includes('function get_tables() does not exist')) {
      console.log('ℹ️  Creating helper function to list tables...');
      
      const { error: createFnError } = await supabase.rpc('create_get_tables_function');
      
      if (createFnError) {
        // If we can't create the function, use a direct query
        console.log('⚠️  Could not create helper function, trying direct query...');
        const { data, error: queryError } = await supabase
          .from('pg_tables')
          .select('tablename')
          .eq('schemaname', 'public');
          
        if (queryError) {
          throw queryError;
        }
        
        return {
          data: data.map((row: any) => ({ table_name: row.tablename })),
          error: null
        };
      }
      
      // Try again with the new function
      const retry = await supabase.rpc('get_tables');
      if (retry.error) throw retry.error;
      return retry;
    }

    if (error) {
      console.error('❌ Error connecting to Supabase:');
      console.error(error);
      return;
    }

    console.log('✅ Successfully connected to Supabase!');
    
    if (tables.length === 0) {
      console.log('\nℹ️  No tables found in the public schema.');
      console.log('You\'ll need to create the necessary tables.');
    } else {
      console.log('\n📋 Found tables:');
      tables.forEach((table: any) => {
        console.log(`- ${table.table_name}`);
      });
    }

    // Check if auth.users table exists
    const { data: authTables } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'auth')
      .eq('table_name', 'users');

    if (authTables && authTables.length > 0) {
      console.log('\n🔑 Auth tables are set up.');
    } else {
      console.log('\n⚠️  Auth tables not found. You need to enable Authentication in your Supabase project.');
    }

  } catch (err) {
    console.error('❌ Unexpected error:');
    console.error(err);
  }
}

checkSupabaseSetup();
