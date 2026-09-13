# Database Models

All tables are defined using SQLModel (SQLAlchemy + Pydantic).

---

## Users & Authentication

### User (`users`)
Staff members (admin, kitchen, etc.)

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `name` | str | NOT NULL |
| `email` | str | UNIQUE, NOT NULL |
| `password_hash` | str | NOT NULL |
| `role` | str | NOT NULL (`admin`, `staff`, `kitchen`) |
| `is_active` | bool | NOT NULL, default `true` |
| `totp_secret` | str | nullable |
| `totp_enabled` | bool | NOT NULL, default `false` |
| `totp_enabled_at` | datetime | nullable |
| `created_at` | datetime | server default `now()` |

### Customer (`customers`)
End users who place orders.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `email` | str | UNIQUE, NOT NULL |
| `password_hash` | str | nullable |
| `name` | str | nullable |
| `phone_number` | str | nullable |
| `phone_verified` | bool | NOT NULL, default `false` |
| `email_verified` | bool | NOT NULL, default `false` |
| `totp_secret` | str | nullable |
| `totp_enabled` | bool | NOT NULL, default `false` |
| `totp_enabled_at` | datetime | nullable |
| `created_at` | datetime | server default `now()` |

---

## Menu

### Category (`categories`)
Menu categories (Appetizers, Main Course, etc.)

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `name` | str | NOT NULL |
| `sort_order` | int | NOT NULL, default `0` |

### MenuItem (`menu_items`)
Individual menu items.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `category_id` | int | FK → `categories.id`, NOT NULL |
| `name` | str | NOT NULL |
| `description` | str | nullable |
| `price` | float | Numeric(10,2), NOT NULL |
| `image_url` | str | nullable |
| `is_available` | bool | NOT NULL, default `true` |
| `sort_order` | int | NOT NULL, default `0` |

---

## Restaurant

### RestaurantProfile (`restaurant_profile`)
Single-row table for restaurant info.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK |
| `name` | str | NOT NULL |
| `logo_url` | str | nullable |
| `description` | str | nullable |
| `address` | str | nullable |
| `phone` | str | nullable |
| `business_hours` | JSON | nullable |

`business_hours` structure:
```json
{
  "sun": {"open": "10:00", "close": "20:00"},
  "mon": {"open": "10:00", "close": "20:00"},
  "sat": null
}
```

---

## Orders

### Order (`orders`)
Customer orders.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `customer_id` | int | FK → `customers.id`, nullable |
| `order_type` | str | NOT NULL (`dine_in`, `takeaway`, `delivery`) |
| `table_number` | str | nullable |
| `delivery_address` | str | nullable |
| `delivery_fee` | float | Numeric(10,2), nullable |
| `scheduled_for` | datetime | nullable |
| `payment_method` | str | NOT NULL (`cash`, `esewa`, `khalti`) |
| `payment_provider` | str | nullable |
| `payment_status` | str | NOT NULL, default `pending` |
| `payment_reference` | str | nullable |
| `fulfillment_status` | str | NOT NULL, default `received` |
| `verified_by_user_id` | int | FK → `users.id`, nullable |
| `verified_at` | datetime | nullable |
| `total_amount` | float | Numeric(10,2), NOT NULL |
| `campaign_id` | int | FK → `campaigns.id`, nullable |
| `discount_amount` | float | Numeric(10,2), nullable |
| `created_at` | datetime | server default `now()` |

### OrderItem (`order_items`)
Items within an order.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `order_id` | int | FK → `orders.id`, NOT NULL |
| `menu_item_id` | int | FK → `menu_items.id`, NOT NULL |
| `quantity` | int | NOT NULL |
| `price_at_order` | float | Numeric(10,2), NOT NULL |

### OrderStatusHistory (`order_status_history`)
Tracks all status changes.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `order_id` | int | FK → `orders.id`, NOT NULL |
| `status_type` | str | NOT NULL (`fulfillment`, `payment`) |
| `from_status` | str | nullable |
| `to_status` | str | NOT NULL |
| `changed_by_user_id` | int | FK → `users.id`, nullable |
| `changed_at` | datetime | server default `now()` |

---

## Promotions

### Campaign (`campaigns`)
Discount rules.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `name` | str | NOT NULL |
| `code` | str | UNIQUE, nullable (null = automatic) |
| `discount_type` | str | NOT NULL (`percentage`, `fixed`) |
| `discount_value` | float | Numeric(10,2), NOT NULL |
| `max_discount_amount` | float | Numeric(10,2), nullable |
| `min_order_amount` | float | Numeric(10,2), nullable |
| `usage_limit_total` | int | nullable |
| `usage_limit_per_customer` | int | nullable |
| `start_date` | date | nullable |
| `end_date` | date | nullable |
| `is_active` | bool | NOT NULL, default `true` |

### PromoBanner (`promo_banners`)
Visual marketing banners.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `title` | str | NOT NULL |
| `description` | str | nullable |
| `image_url` | str | nullable |
| `link_type` | str | NOT NULL, default `none` |
| `link_target_id` | int | nullable |
| `start_date` | date | nullable |
| `end_date` | date | nullable |
| `is_active` | bool | NOT NULL, default `true` |
| `sort_order` | int | NOT NULL, default `0` |

---

## Permissions

### Permission (`permissions`)
Available permission keys.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `key` | str | UNIQUE, NOT NULL |
| `description` | str | NOT NULL |

Seeded keys: `view_payment_status`, `verify_payment`, `complete_cash_order`, `update_fulfillment_status`, `override_gateway_payment`, `edit_menu`, `manage_promos`, `manage_staff`

### RolePermission (`role_permissions`)
Maps roles to permissions.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `role` | str | NOT NULL |
| `permission_id` | int | FK → `permissions.id`, NOT NULL |

---

## Security

### WebAuthnCredential (`webauthn_credentials`)
Registered passkeys.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `user_type` | str | NOT NULL (`staff`, `customer`) |
| `user_id` | int | NOT NULL |
| `credential_id` | str | UNIQUE, NOT NULL |
| `public_key` | bytes | NOT NULL |
| `sign_count` | int | NOT NULL, default `0` |
| `aaguid` | str | nullable |
| `credential_device_type` | str | nullable |
| `credential_backed_up` | bool | NOT NULL, default `false` |
| `name` | str | nullable |
| `created_at` | datetime | server default `now()` |

### WebAuthnChallenge (`webauthn_challenges`)
Temporary challenges for WebAuthn ceremonies.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `challenge` | str | NOT NULL |
| `user_type` | str | NOT NULL |
| `user_id` | int | nullable |
| `ceremony` | str | NOT NULL (`registration`, `authentication`) |
| `expires_at` | datetime | NOT NULL |
| `used` | bool | NOT NULL, default `false` |
| `created_at` | datetime | server default `now()` |

### TrustedDevice (`trusted_devices`)
Devices that skip 2FA for 30 days.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `user_type` | str | NOT NULL (`staff`, `customer`) |
| `user_id` | int | NOT NULL |
| `token_hash` | str | UNIQUE, NOT NULL |
| `user_agent` | str | nullable |
| `ip_address` | str | nullable |
| `expires_at` | datetime | NOT NULL |
| `created_at` | datetime | server default `now()` |

---

## Tokens

### StaffPasswordResetToken (`staff_password_reset_tokens`)

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `user_id` | int | FK → `users.id`, NOT NULL |
| `token_hash` | str | NOT NULL |
| `expires_at` | datetime | NOT NULL |
| `used` | bool | NOT NULL, default `false` |
| `created_at` | datetime | server default `now()` |

### CustomerPasswordResetToken (`customer_password_reset_tokens`)

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `customer_id` | int | FK → `customers.id`, NOT NULL |
| `token_hash` | str | NOT NULL |
| `expires_at` | datetime | NOT NULL |
| `used` | bool | NOT NULL, default `false` |
| `created_at` | datetime | server default `now()` |

### EmailVerification (`email_verifications`)

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | int | PK, auto |
| `customer_id` | int | FK → `customers.id`, NOT NULL |
| `email` | str | NOT NULL |
| `code` | str | NOT NULL |
| `purpose` | str | NOT NULL, default `verify_email` |
| `expires_at` | datetime | NOT NULL |
| `used` | bool | NOT NULL, default `false` |
| `created_at` | datetime | server default `now()` |
