-- Full workspace folders, notes and resource sharing.

create table if not exists workspace_folders (
  id varchar(48) primary key,
  firm_id varchar(48) not null references firms(id) on delete cascade,
  name varchar(180) not null,
  parent_folder_id varchar(48) references workspace_folders(id) on delete cascade,
  owner_user_id varchar(48) not null references users(id),
  created_at timestamptz not null default now()
);

create table if not exists workspace_notes (
  id varchar(48) primary key,
  firm_id varchar(48) not null references firms(id) on delete cascade,
  folder_id varchar(48) references workspace_folders(id) on delete set null,
  title varchar(220) not null,
  body text not null default '',
  owner_user_id varchar(48) not null references users(id),
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create table if not exists workspace_shares (
  id varchar(48) primary key,
  firm_id varchar(48) not null references firms(id) on delete cascade,
  resource_type varchar(40) not null,
  resource_id varchar(48) not null,
  grantee_user_id varchar(48) not null references users(id) on delete cascade,
  permission varchar(16) not null,
  created_by varchar(48) not null references users(id),
  created_at timestamptz not null default now(),
  constraint uq_workspace_share_target unique (firm_id, resource_type, resource_id, grantee_user_id)
);

alter table documents add column if not exists folder_id varchar(48) references workspace_folders(id) on delete set null;

alter table workspace_folders enable row level security;
alter table workspace_notes enable row level security;
alter table workspace_shares enable row level security;

alter table workspace_folders force row level security;
alter table workspace_notes force row level security;
alter table workspace_shares force row level security;

drop policy if exists tenant_select_workspace_folders on workspace_folders;
drop policy if exists tenant_insert_workspace_folders on workspace_folders;
drop policy if exists tenant_update_workspace_folders on workspace_folders;
create policy tenant_select_workspace_folders on workspace_folders
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_workspace_folders on workspace_folders
  for insert with check (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_update_workspace_folders on workspace_folders
  for update using (firm_id = current_setting('app.current_firm_id', true))
  with check (firm_id = current_setting('app.current_firm_id', true));

drop policy if exists tenant_select_workspace_notes on workspace_notes;
drop policy if exists tenant_insert_workspace_notes on workspace_notes;
drop policy if exists tenant_update_workspace_notes on workspace_notes;
create policy tenant_select_workspace_notes on workspace_notes
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_workspace_notes on workspace_notes
  for insert with check (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_update_workspace_notes on workspace_notes
  for update using (firm_id = current_setting('app.current_firm_id', true))
  with check (firm_id = current_setting('app.current_firm_id', true));

drop policy if exists tenant_select_workspace_shares on workspace_shares;
drop policy if exists tenant_insert_workspace_shares on workspace_shares;
drop policy if exists tenant_update_workspace_shares on workspace_shares;
create policy tenant_select_workspace_shares on workspace_shares
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_workspace_shares on workspace_shares
  for insert with check (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_update_workspace_shares on workspace_shares
  for update using (firm_id = current_setting('app.current_firm_id', true))
  with check (firm_id = current_setting('app.current_firm_id', true));

create index if not exists idx_workspace_folders_firm_owner on workspace_folders(firm_id, owner_user_id);
create index if not exists idx_workspace_notes_firm_owner on workspace_notes(firm_id, owner_user_id);
create index if not exists idx_workspace_notes_folder on workspace_notes(firm_id, folder_id);
create index if not exists idx_workspace_shares_resource on workspace_shares(firm_id, resource_type, resource_id);
create index if not exists idx_workspace_shares_grantee on workspace_shares(firm_id, grantee_user_id);
create index if not exists idx_documents_folder_id on documents(folder_id);
