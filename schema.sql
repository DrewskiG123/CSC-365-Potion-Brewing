-- Andrew Ji

-- Cart Items Table
create table
  public.cart_items (
    cart_id bigint not null,
    catalog_id bigint not null,
    quantity integer null,
    constraint cart_items_pkey primary key (cart_id, catalog_id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (id) on update restrict on delete cascade,
    constraint cart_items_catalog_id_fkey foreign key (catalog_id) references catalog (id) on update restrict
  ) tablespace pg_default;

-- Carts Table
create table
  public.carts (
    id bigint generated by default as identity,
    customer text null,
    created_at timestamp with time zone not null default (now() at time zone 'pst'::text),
    constraint carts_pkey primary key (id),
    constraint carts_id_key unique (id)
  ) tablespace pg_default;

-- Catalog Table
create table
  public.catalog (
    id bigint generated by default as identity,
    sku text null,
    name text not null default 'Custom'::text,
    price integer null,
    inventory integer null,
    potion_type integer[] null,
    constraint catalog_pkey primary key (id),
    constraint catalog_id_key unique (id)
  ) tablespace pg_default;

-- Global Inventory Table (Just ml and gold now)
create table
  public.global_inventory (
    id integer generated by default as identity,
    num_red_ml integer not null,
    gold integer null,
    num_green_ml integer null,
    num_blue_ml integer null,
    num_dark_ml integer null,
    constraint global_inventory_pkey primary key (id),
    constraint global_inventory_id_key unique (id)
  ) tablespace pg_default;