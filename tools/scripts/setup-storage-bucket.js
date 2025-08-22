#!/usr/bin/env node
/**
 * Set up Supabase storage bucket for AI models
 */

const { createClient } = require('@supabase/supabase-js');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from the correct path
dotenv.config({ path: path.resolve(__dirname, '../../.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_SERVICE_ROLE_KEY;

console.log('=== Supabase Storage Bucket Setup ===');
console.log(`SUPABASE_URL: ${supabaseUrl}`);
console.log(`SUPABASE_SERVICE_ROLE_KEY: ${supabaseKey ? supabaseKey.substring(0, 20) + '...' : 'None'}`);

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Error: Missing Supabase URL or Service Role Key in environment variables');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function setupStorageBucket() {
  try {
    console.log('\n🔍 Checking existing storage buckets...');
    
    // List existing buckets
    const { data: buckets, error: listError } = await supabase.storage.listBuckets();
    
    if (listError) {
      console.error('❌ Error listing buckets:', listError.message);
      return;
    }
    
    console.log(`✅ Found ${buckets.length} existing buckets:`);
    buckets.forEach(bucket => {
      console.log(`  - ${bucket.name} (public: ${bucket.public})`);
    });
    
    // Check if ai-models bucket exists
    const aiModelsBucket = buckets.find(b => b.name === 'ai-models');
    
    if (aiModelsBucket) {
      console.log('\n✅ ai-models bucket already exists');
      console.log(`  - Name: ${aiModelsBucket.name}`);
      console.log(`  - Public: ${aiModelsBucket.public}`);
      console.log(`  - File size limit: ${aiModelsBucket.file_size_limit} bytes`);
    } else {
      console.log('\n📦 Creating ai-models bucket...');
      
      // Create the bucket
      const { data: newBucket, error: createError } = await supabase.storage.createBucket('ai-models', {
        public: false,
        fileSizeLimit: 52428800, // 50MB
        allowedMimeTypes: [
          'application/octet-stream',
          'application/json',
          'text/plain',
          'application/x-python-code'
        ]
      });
      
      if (createError) {
        console.error('❌ Error creating bucket:', createError.message);
        return;
      }
      
      console.log('✅ ai-models bucket created successfully');
      console.log(`  - Name: ${newBucket.name}`);
      console.log(`  - Public: ${newBucket.public}`);
    }
    
    // Test bucket functionality
    console.log('\n🧪 Testing bucket functionality...');
    
    const testContent = 'FairMind Storage Test - ' + new Date().toISOString();
    const testFilePath = 'test/test_storage.txt';
    
    // Upload test file
    const { error: uploadError } = await supabase.storage
      .from('ai-models')
      .upload(testFilePath, testContent, {
        contentType: 'text/plain',
        upsert: true
      });
    
    if (uploadError) {
      console.error('❌ Error uploading test file:', uploadError.message);
      return;
    }
    
    console.log('✅ Test file uploaded successfully');
    
    // Download test file
    const { data: downloadedContent, error: downloadError } = await supabase.storage
      .from('ai-models')
      .download(testFilePath);
    
    if (downloadError) {
      console.error('❌ Error downloading test file:', downloadError.message);
      return;
    }
    
    const downloadedText = await downloadedContent.text();
    if (downloadedText === testContent) {
      console.log('✅ Test file download successful - content matches');
    } else {
      console.log('❌ Test file download failed - content mismatch');
      return;
    }
    
    // Clean up test file
    const { error: deleteError } = await supabase.storage
      .from('ai-models')
      .remove([testFilePath]);
    
    if (deleteError) {
      console.error('❌ Error deleting test file:', deleteError.message);
      return;
    }
    
    console.log('✅ Test file cleaned up');
    
    console.log('\n🎉 Supabase storage bucket setup completed successfully!');
    console.log('\nNext steps:');
    console.log('1. The ai-models bucket is ready for storing AI model files');
    console.log('2. You can now use the ModelStorageService in your backend');
    console.log('3. Files will be organized by organization_id/model_name');
    
  } catch (err) {
    console.error('❌ Unexpected error:');
    console.error(err);
  }
}

setupStorageBucket();
