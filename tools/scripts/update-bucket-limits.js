#!/usr/bin/env node
/**
 * Update Supabase storage bucket file size limits
 */

const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from the correct path
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY;

console.log('=== Update Supabase Bucket Limits ===');
console.log(`SUPABASE_URL: ${supabaseUrl}`);
console.log(`SUPABASE_SERVICE_ROLE_KEY: ${supabaseKey ? supabaseKey.substring(0, 20) + '...' : 'None'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Error: Missing Supabase URL or Service Role Key in environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function updateBucketLimits() {
  try {
    console.log('\n🔍 Checking current bucket configuration...');
    
    // List existing buckets
    const { data: buckets, error: listError } = await supabase.storage.listBuckets();
    
    if (listError) {
      console.error('❌ Error listing buckets:', listError.message);
      return;
    }
    
    const aiModelsBucket = buckets.find(b => b.name === 'ai-models');
    
    if (!aiModelsBucket) {
      console.error('❌ ai-models bucket not found');
      return;
    }
    
    console.log('Current ai-models bucket configuration:');
    console.log(`  - Name: ${aiModelsBucket.name}`);
    console.log(`  - Public: ${aiModelsBucket.public}`);
    console.log(`  - File size limit: ${aiModelsBucket.file_size_limit} bytes (${Math.round(aiModelsBucket.file_size_limit / 1024 / 1024)}MB)`);
    
    // Check if we need to update the limits
    const currentLimit = aiModelsBucket.file_size_limit;
    const newLimit = 100 * 1024 * 1024; // 100MB
    
    if (currentLimit >= newLimit) {
      console.log('\n✅ Bucket already supports files up to 100MB');
      return;
    }
    
    console.log(`\n📦 Updating file size limit from ${Math.round(currentLimit / 1024 / 1024)}MB to ${Math.round(newLimit / 1024 / 1024)}MB...`);
    
    // Note: Supabase doesn't provide a direct API to update bucket settings
    // We need to recreate the bucket or use the dashboard
    console.log('\n⚠️  Note: Supabase storage API does not support updating bucket settings directly.');
    console.log('To increase the file size limit, you need to:');
    console.log('1. Go to your Supabase dashboard');
    console.log('2. Navigate to Storage > Buckets');
    console.log('3. Click on the ai-models bucket');
    console.log('4. Update the file size limit to 100MB or higher');
    console.log('5. Save the changes');
    
    console.log('\nAlternatively, you can use the Supabase CLI:');
    console.log('supabase storage update-bucket ai-models --file-size-limit 104857600');
    
    // Test current upload capabilities
    console.log('\n🧪 Testing current upload capabilities...');
    
    const testSizes = [
      { name: 'Small file (1MB)', size: 1 * 1024 * 1024 },
      { name: 'Medium file (25MB)', size: 25 * 1024 * 1024 },
      { name: 'Large file (60MB)', size: 60 * 1024 * 1024 }
    ];
    
    for (const test of testSizes) {
      try {
        const testContent = 'A'.repeat(test.size);
        const testFilePath = `test/size_test_${Math.round(test.size / 1024 / 1024)}MB.txt`;
        
        console.log(`\nTesting ${test.name}...`);
        
        const { error: uploadError } = await supabase.storage
          .from('ai-models')
          .upload(testFilePath, testContent, {
            contentType: 'text/plain',
            upsert: true
          });
        
        if (uploadError) {
          console.log(`❌ ${test.name} failed: ${uploadError.message}`);
        } else {
          console.log(`✅ ${test.name} uploaded successfully`);
          
          // Clean up test file
          await supabase.storage
            .from('ai-models')
            .remove([testFilePath]);
        }
        
      } catch (err) {
        console.log(`❌ ${test.name} failed: ${err.message}`);
      }
    }
    
    console.log('\n📊 Summary:');
    console.log('- Files up to 50MB: Should work with current configuration');
    console.log('- Files 50MB-100MB: May fail until bucket limits are updated');
    console.log('- Files >100MB: Will be rejected by backend validation');
    
    console.log('\n💡 Recommendations:');
    console.log('1. Update bucket file size limit to 100MB in Supabase dashboard');
    console.log('2. Consider implementing chunked uploads for files >100MB');
    console.log('3. Use local storage as fallback for very large files');
    
  } catch (err) {
    console.error('❌ Unexpected error:');
    console.error(err);
  }
}

updateBucketLimits();
