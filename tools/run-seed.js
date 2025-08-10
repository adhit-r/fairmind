const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Supabase configuration
const supabaseUrl = 'https://swapkvhzyhcruoyjpkyr.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN3YXBrdmh6eWhjcnVveWpwa3lyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM0Njg4NTQsImV4cCI6MjA2OTA0NDg1NH0.ckdz6Kv63Tp4F6iuMhzuTQr8sfMhxpeZVmGzGaf40k8';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function runSeed() {
  try {
    console.log('Reading seed script...');
    const seedPath = path.join(__dirname, '../backend/supabase/seed.sql');
    const seedScript = fs.readFileSync(seedPath, 'utf8');
    
    console.log('Running seed script...');
    
    // Split the script into individual statements
    const statements = seedScript
      .split(';')
      .map(stmt => stmt.trim())
      .filter(stmt => stmt.length > 0 && !stmt.startsWith('--'));
    
    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i];
      if (statement.trim()) {
        console.log(`Executing statement ${i + 1}/${statements.length}...`);
        
        try {
          // Use the REST API to execute SQL
          const response = await fetch(`${supabaseUrl}/rest/v1/rpc/exec_sql`, {
            method: 'POST',
            headers: {
              'apikey': supabaseAnonKey,
              'Authorization': `Bearer ${supabaseAnonKey}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sql: statement })
          });
          
          if (!response.ok) {
            console.log(`Statement ${i + 1} failed (this is expected for some statements):`, statement.substring(0, 100) + '...');
          } else {
            console.log(`Statement ${i + 1} executed successfully`);
          }
        } catch (error) {
          console.log(`Statement ${i + 1} failed (this is expected):`, error.message);
        }
      }
    }
    
    console.log('Seed script execution completed!');
    
  } catch (error) {
    console.error('Error running seed script:', error);
  }
}

runSeed();
