const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testConnection() {
  const { data, error } = await supabase.from('User').select('*');
  if (error) {
    console.error('Error connecting to Supabase:', error);
  } else {
    console.log('Supabase connection successful:', data);
  }
}

testConnection();
