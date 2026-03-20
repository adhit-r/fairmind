-- Create users table for local auth
create table if not exists users (
  id text primary key,
  email text unique not null,
  hashed_password text not null,
  full_name text,
  role text default 'user',
  is_active boolean default true,
  created_at timestamptz default current_timestamp,
  updated_at timestamptz default current_timestamp
);
