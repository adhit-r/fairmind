import { createClient as createSupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// Ensure a single browser client instance to avoid multiple GoTrueClient warnings
let singletonClient: ReturnType<typeof createSupabaseClient> | null = null;

export function createClient() {
  if (!singletonClient) {
    singletonClient = createSupabaseClient(supabaseUrl, supabaseAnonKey);
  }
  return singletonClient;
}
