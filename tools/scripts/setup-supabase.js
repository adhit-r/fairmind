const { Client } = require('pg');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env.local
dotenv.config({ path: path.resolve(__dirname, '../.env.local') });

async function runSQLFile(client, filePath) {
  try {
    const sql = fs.readFileSync(filePath, 'utf8');
    console.log(`Running ${path.basename(filePath)}...`);
    await client.query(sql);
    console.log(`✅ ${path.basename(filePath)} executed successfully`);
  } catch (error) {
    console.error(`❌ Error in ${path.basename(filePath)}:`, error.message);
    throw error;
  }
}

async function setupSupabase() {
  // Parse the database URL
  const dbUrl = new URL(process.env.DATABASE_URL);
  const dbConfig = {
    user: dbUrl.username,
    password: dbUrl.password,
    host: dbUrl.hostname,
    port: dbUrl.port || 5432,
    database: dbUrl.pathname.replace(/^\//, '') || 'postgres',
    ssl: {
      rejectUnauthorized: false, // For self-signed certificates
      require: true
    },
    // Additional connection options
    connectionTimeoutMillis: 5000,
    query_timeout: 10000,
    statement_timeout: 10000
  };

  console.log('🔌 Connecting to database...');
  console.log(`📡 Host: ${dbConfig.host}:${dbConfig.port}`);
  console.log(`📝 Database: ${dbConfig.database}`);
  
  const client = new Client(dbConfig);

  try {
    await client.connect();
    console.log('Connected to database');

    // Run RLS setup
    await runSQLFile(client, path.join(__dirname, 'setup-rls.sql'));
    
    // Run functions setup
    await runSQLFile(client, path.join(__dirname, 'setup-functions.sql'));

    console.log('\n🎉 Supabase setup completed successfully!');
  } catch (error) {
    console.error('Setup failed:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

setupSupabase();
