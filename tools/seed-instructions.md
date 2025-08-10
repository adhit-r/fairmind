# Running the Seed Script

## Option 1: Manual (Recommended)

1. **Go to your Supabase dashboard:**
   - https://supabase.com/dashboard/project/swapkvhzyhcruoyjpkyr

2. **Click on "SQL Editor" in the left sidebar**

3. **Copy the entire contents of `backend/supabase/seed.sql`**

4. **Paste it into the SQL Editor**

5. **Click "Run"**

## Option 2: Using Supabase CLI (if installed)

```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Link your project
supabase link --project-ref swapkvhzyhcruoyjpkyr

# Run the seed script
supabase db reset --linked
```

## What the seed script does:

- ✅ Creates the `profiles` table
- ✅ Sets up Row Level Security (RLS) policies
- ✅ Creates necessary functions and triggers
- ✅ Enables authentication to work properly

## After running the seed script:

- The 401 "Invalid API key" error should be resolved
- You'll be able to sign up and log in successfully
- The authentication flow will work properly

## Test the authentication:

1. Go to http://localhost:3000/login
2. Try signing up with a new account
3. Or try logging in if you have an existing account
