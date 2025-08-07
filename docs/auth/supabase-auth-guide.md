# Supabase Authentication Guide

## Overview
This guide explains how authentication works in the Fairmind Ethical Sandbox using Supabase Auth.

## Setup

### 1. Environment Variables
Ensure these environment variables are set in your `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 2. Supabase Client
Initialize the Supabase client in your application:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

## Authentication Flows

### 1. Email/Password Sign Up

```typescript
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password',
  options: {
    data: {
      full_name: 'John Doe',
    },
  },
})
```

### 2. Email/Password Sign In

```typescript
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password',
})
```

### 3. Sign Out

```typescript
const { error } = await supabase.auth.signOut()
```

### 4. Password Reset

```typescript
const { data, error } = await supabase.auth.resetPasswordForEmail('user@example.com', {
  redirectTo: 'https://yourapp.com/update-password',
})
```

## User Sessions

### Get Current Session

```typescript
const { data: { session } } = await supabase.auth.getSession()
```

### Listen for Auth Changes

```typescript
const { data: { subscription } } = supabase.auth.onAuthStateChange(
  (event, session) => {
    console.log(event, session)
  }
)

// Cleanup subscription
subscription.unsubscribe()
```

## User Management

### Get Current User

```typescript
const { data: { user } } = await supabase.auth.getUser()
```

### Update User Data

```typescript
const { data, error } = await supabase.auth.updateUser({
  data: { full_name: 'John Updated' }
})
```

## Row Level Security (RLS)

### Example Policy
```sql
-- Enable RLS on a table
ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;

-- Create policy for user-specific access
CREATE POLICY "Users can view their own data"
ON your_table
FOR SELECT
USING (auth.uid() = user_id);
```

## Error Handling

Always handle authentication errors:

```typescript
try {
  const { data, error } = await supabase.auth.signInWithPassword({
    email: 'user@example.com',
    password: 'wrong-password',
  })
  
  if (error) throw error
  
  // Handle successful login
} catch (error) {
  console.error('Authentication error:', error.message)
  // Show user-friendly error message
}
```

## Common Issues

1. **Missing Environment Variables**
   - Ensure `.env.local` is properly set up
   - Restart development server after changes

2. **CORS Issues**
   - Configure CORS in Supabase dashboard
   - Add your development/production domains

3. **RLS Not Working**
   - Verify RLS is enabled on tables
   - Check policy conditions
   - Test with SQL directly in Supabase dashboard

## Best Practices

1. Always check for errors after auth operations
2. Use loading states during auth operations
3. Protect sensitive routes with middleware
4. Implement proper error boundaries
5. Log auth events for debugging

## Next Steps

1. Implement email confirmation flow
2. Add social logins (Google, GitHub, etc.)
3. Set up MFA (Multi-Factor Authentication)
4. Implement rate limiting
5. Set up monitoring and alerts
