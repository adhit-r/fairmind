#!/usr/bin/env node
/**
 * Test Supabase connection using the correct environment file path
 */

const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from the correct path
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

console.log('=== Supabase Connection Test ===');
console.log(`SUPABASE_URL: ${supabaseUrl}`);
console.log(`SUPABASE_ANON_KEY: ${supabaseKey ? supabaseKey.substring(0, 20) + '...' : 'None'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Error: Missing Supabase URL or Anon Key in environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function testSupabaseConnection() {
  try {
    console.log('\n🔍 Testing Supabase connection...');
    
    // Test basic connection by trying to list tables
    const { data: tables, error } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'public')
      .limit(5);
    
    if (error) {
      console.error('❌ Error connecting to Supabase:');
      console.error(error);
      return;
    }
    
    console.log('✅ Successfully connected to Supabase!');
    
    if (tables && tables.length > 0) {
      console.log('\n📋 Found tables in public schema:');
      tables.forEach(table => {
        console.log(`  - ${table.table_name}`);
      });
    } else {
      console.log('\nℹ️  No tables found in public schema.');
    }
    
    // Test storage functionality
    console.log('\n--- Testing Storage ---');
    try {
      const { data: buckets, error: storageError } = await supabase.storage.listBuckets();
      
      if (storageError) {
        console.error('❌ Error accessing storage:', storageError.message);
      } else {
        console.log(`✅ Storage access successful. Found ${buckets.length} buckets:`);
        buckets.forEach(bucket => {
          console.log(`  - ${bucket.name} (public: ${bucket.public})`);
        });
        
        // Check if ai-models bucket exists
        const aiModelsBucket = buckets.find(b => b.name === 'ai-models');
        if (aiModelsBucket) {
          console.log('✅ ai-models bucket exists');
        } else {
          console.log('❌ ai-models bucket does not exist');
        }
      }
    } catch (storageErr) {
      console.error('❌ Storage test failed:', storageErr.message);
    }
    
  } catch (err) {
    console.error('❌ Unexpected error:');
    console.error(err);
  }
}

testSupabaseConnection();
