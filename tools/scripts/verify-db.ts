import { Client } from 'pg';
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

async function verifyDatabase() {
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

    // List all tables
    console.log('\n📋 Listing all tables:');
    const tablesResult = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public'
      ORDER BY table_name;
    `);
    
    console.log('Tables in the database:');
    tablesResult.rows.forEach((row, index) => {
      console.log(`  ${index + 1}. ${row.table_name}`);
    });

    // Check if auth.users exists
    console.log('\n🔍 Checking auth schema tables:');
    try {
      const authTablesResult = await client.query(`
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'auth'
        ORDER BY table_name;
      `);
      
      console.log('Tables in auth schema:');
      authTablesResult.rows.forEach((row, index) => {
        console.log(`  ${index + 1}. auth.${row.table_name}`);
      });
    } catch (error) {
      console.log('  ⚠️  Could not access auth schema:', error.message);
    }

    // Check if admin user exists
    console.log('\n👤 Checking admin user:');
    try {
      const adminUser = await client.query(`
        SELECT id, email, created_at 
        FROM auth.users 
        WHERE email = 'admin@fairmind.app';
      `);
      
      if (adminUser.rows.length > 0) {
        console.log('✅ Admin user found:');
        console.log(`  ID: ${adminUser.rows[0].id}`);
        console.log(`  Email: ${adminUser.rows[0].email}`);
        console.log(`  Created: ${adminUser.rows[0].created_at}`);
        
        // Check if profile exists
        const profile = await client.query(`
          SELECT username, role 
          FROM public.profiles 
          WHERE id = $1;
        `, [adminUser.rows[0].id]);
        
        if (profile.rows.length > 0) {
          console.log('✅ Admin profile found:');
          console.log(`  Username: ${profile.rows[0].username}`);
          console.log(`  Role: ${profile.rows[0].role}`);
        } else {
          console.log('❌ Admin profile not found');
        }
      } else {
        console.log('❌ Admin user not found');
      }
    } catch (error) {
      console.log('  ⚠️  Could not check admin user:', error.message);
    }

  } catch (error) {
    console.error('❌ Error verifying database:');
    console.error(error);
    process.exit(1);
  } finally {
    await client.end();
    process.exit(0);
  }
}

verifyDatabase();
