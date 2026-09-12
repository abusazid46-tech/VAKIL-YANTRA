-- Auth lifecycle tables for OTP, invitations and password reset.

create table if not exists auth_challenges (
  id varchar(48) primary key,
  user_id varchar(48) not null references users(id) on delete cascade,
  otp_hash varchar(128) not null,
  delivery_channel varchar(32) not null default 'email',
  expires_at timestamptz not null,
  consumed_at timestamptz,
  attempts integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists invitations (
  id varchar(48) primary key,
  firm_id varchar(48) not null references firms(id) on delete cascade,
  email varchar(320) not null,
  role varchar(48) not null,
  token_hash varchar(128) not null unique,
  invited_by_user_id varchar(48) not null references users(id),
  expires_at timestamptz not null,
  accepted_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists password_resets (
  id varchar(48) primary key,
  user_id varchar(48) not null references users(id) on delete cascade,
  token_hash varchar(128) not null unique,
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_auth_challenges_user_id on auth_challenges(user_id);
create index if not exists idx_invitations_firm_email on invitations(firm_id, email);
create index if not exists idx_invitations_token_hash on invitations(token_hash);
create index if not exists idx_password_resets_user_id on password_resets(user_id);
create index if not exists idx_password_resets_token_hash on password_resets(token_hash);
