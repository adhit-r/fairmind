-- Create datasets table
create table if not exists datasets (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  file_path text not null,
  file_type text not null,
  file_size bigint,
  row_count bigint,
  column_count int,
  schema jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Enable RLS
alter table datasets enable row level security;

-- Create policy to allow all access for now (or restrict as needed)
create policy "Allow public read access"
  on datasets for select
  using ( true );

create policy "Allow authenticated insert"
  on datasets for insert
  with check ( auth.role() = 'authenticated' or auth.role() = 'service_role' );

create policy "Allow authenticated update"
  on datasets for update
  using ( auth.role() = 'authenticated' or auth.role() = 'service_role' );

-- Create storage bucket if not exists
insert into storage.buckets (id, name, public)
values ('datasets', 'datasets', true)
on conflict (id) do nothing;

-- Storage policies
create policy "Public Access"
  on storage.objects for select
  using ( bucket_id = 'datasets' );

create policy "Authenticated Upload"
  on storage.objects for insert
  with check ( bucket_id = 'datasets' and (auth.role() = 'authenticated' or auth.role() = 'service_role') );
