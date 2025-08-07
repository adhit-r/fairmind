import { Client } from 'pg';
import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

// Get the database URL from command line arguments or environment variables
let connectionString = process.env.DATABASE_URL || process.argv[2];

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

async function promptForConnectionString(): Promise<string> {
  return new Promise<string>((resolve) => {
    console.log('Please enter your Supabase database connection URL:');
    console.log('Format: postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres');
    
    rl.question('> ', (answer) => {
      resolve(answer.trim());
    });
  });
}

async function runMigrations() {
  if (!connectionString) {
    console.log('No database URL provided as argument.');
    connectionString = await promptForConnectionString();
    rl.close();
  }

  const client = new Client({
    connectionString,
    ssl: {
      rejectUnauthorized: false // Required for Supabase connections
    }
  });

  try {
    console.log('🔌 Connecting to the database...');
    await client.connect();
    console.log('✅ Connected to the database');

    // Read the simplified SQL file
    const sqlPath = path.join(__dirname, 'simplified-setup.sql');
    const sql = fs.readFileSync(sqlPath, 'utf8');

    console.log('🚀 Running migrations...');
    
    // Split into individual statements and execute
    // First, handle DO blocks and other complex statements
    const processedSql = sql.replace(/do \$\$([\s\S]*?)\$\$\s*;/g, (match, content) => {
      // Replace the DO block with a single statement
      return `-- DO BLOCK: ${content.replace(/\n/g, ' ').substring(0, 50)}...`;
    });

    // Then split into individual statements
    const statements = processedSql
      .split(';')
      .map(s => s.trim())
      .filter(s => s.length > 0 && !s.startsWith('--'));
    
    // Add the DO blocks back as single statements
    const doBlocks: string[] = [];
    const doBlockRegex = /do \$\$([\s\S]*?)\$\$\s*;/g;
    let match: RegExpExecArray | null;
    while ((match = doBlockRegex.exec(sql)) !== null) {
      // Ensure match[0] exists before using it
      if (match[0]) {
        doBlocks.push(`do $${match[0].substring(2)}`);
      }
    }

    // Execute all regular statements
    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i];
      if (!statement) continue;
      
      console.log(`  → [${i + 1}/${statements.length + doBlocks.length}] Executing statement...`);
      
      try {
        await client.query(statement);
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
    
    // Execute all DO blocks
    for (let i = 0; i < doBlocks.length; i++) {
      const doBlock = doBlocks[i];
      console.log(`  → [${statements.length + i + 1}/${statements.length + doBlocks.length}] Executing DO block...`);
      
      try {
        await client.query(doBlock);
      } catch (error) {
        // Skip certain errors that might be expected
        if (error.message.includes('already exists') || 
            error.message.includes('does not exist') ||
            error.message.includes('already a member')) {
          console.log(`  ⚠️  ${error.message.split('\n')[0]}`);
          continue;
        }
        console.error(`❌ Error in DO block ${i + 1}:`);
        console.error(doBlock.substring(0, 100) + '...');
        console.error('Error:', error.message);
        throw error;
      }
    }

    console.log('\n🎉 Database setup completed successfully!');
    
  } catch (error) {
    console.error('❌ Error running migrations:');
    console.error(error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

runMigrations();
