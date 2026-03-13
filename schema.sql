-- Enable pgvector extension (if not already enabled)
create extension if not exists vector;

-- Products table to store structured fields + embedding for semantic search
create table if not exists products (
  id                bigint primary key generated always as identity,
  pid               text unique not null,
  name              text not null,
  price             numeric,
  currency          text default 'INR',
  category          text,
  material          text,
  stock_status      text,
  link              text,
  purity            text,
  gem_stone_1       text,
  gem_stone_2       text,
  collection        text,
  product_details   text,
  metal_colour      text,
  diamond_caratage  text,
  diamond_clarity   text,
  diamond_colour    text,
  embedding         vector(3072),
  created_at        timestamptz default now(),
  updated_at        timestamptz default now()
);

-- Brand-level configuration for AI concierge voice and rules
create table if not exists brand_config (
  id                   bigint primary key generated always as identity,
  brand_name           text not null default 'Zoya',
  system_prompt        text,
  voice_rules          text,
  forbidden_words      text,
  price_framing        text,
  out_of_stock_script  text,
  greeting_message     text,
  follow_up_style      text,
  created_at           timestamptz default now(),
  updated_at           timestamptz default now()
);

-- Few-shot conversation examples to shape tone
create table if not exists conversation_examples (
  id                  bigint primary key generated always as identity,
  brand_id            bigint references brand_config(id) on delete cascade,
  scenario_label      text,
  customer_message    text not null,
  concierge_response  text not null,
  sort_order          int default 0,
  is_active           boolean default true,
  created_at          timestamptz default now(),
  updated_at          timestamptz default now()
);

-- Configurable suggestion chips for the chat UI
create table if not exists suggestion_chips (
  id          bigint primary key generated always as identity,
  brand_id    bigint references brand_config(id) on delete cascade,
  label       text not null,
  category    text,
  sort_order  int default 0,
  is_active   boolean default true,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

-- Collection stories used for richer, story-driven recommendations
create table if not exists collection_stories (
  id             bigint primary key generated always as identity,
  brand_id       bigint references brand_config(id) on delete cascade,
  collection_name text not null,
  narrative      text,
  mood_keywords  text[],
  embedding      vector(3072),
  is_active      boolean default true,
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);

-- Occasion guides (anniversary, bridal, self-purchase, etc.)
create table if not exists occasion_guides (
  id             bigint primary key generated always as identity,
  brand_id       bigint references brand_config(id) on delete cascade,
  occasion_name  text not null,
  guide_text     text,
  mood_keywords  text[],
  embedding      vector(3072),
  is_active      boolean default true,
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);

