# API Reference

Base URL: `http://localhost:8000`

All admin endpoints require `Authorization: Bearer <token>` header.

---

## Auth (`/api/auth`)

### Staff Login
```
POST /api/auth/login
Body: { "email": "staff@example.com", "password": "pass123" }
Response: { "access_token": "...", "role": "staff", "user_type": "staff" }
```
If TOTP is enabled: returns `requires_totp: true` + `temp_token`.

### Customer Register
```
POST /api/auth/customer/register
Body: { "email": "customer@example.com", "password": "pass123", "name": "John" }
Response: { "access_token": "...", "user_type": "customer" }
```

### Customer Login
```
POST /api/auth/customer/login
Body: { "email": "customer@example.com", "password": "pass123" }
Response: { "access_token": "...", "user_type": "customer" }
```

### Refresh Token
```
POST /api/auth/refresh
Header: Authorization: Bearer <token>
Response: { "access_token": "...", "user_type": "staff" }
```

### Forgot Password (Staff)
```
POST /api/auth/forgot-password
Body: { "email": "staff@example.com" }
Response: { "detail": "If that email is registered, a reset link has been sent." }
```

### Reset Password (Staff)
```
POST /api/auth/reset-password
Body: { "token": "<from_email>", "new_password": "newpass123" }
Response: { "detail": "Password reset successful" }
```

### Forgot Password (Customer)
```
POST /api/auth/customer/forgot-password
Body: { "email": "customer@example.com" }
```

### Reset Password (Customer)
```
POST /api/auth/customer/reset-password
Body: { "token": "<from_email>", "new_password": "newpass123" }
```

---

## Admin (`/api/admin`)

### List Staff
```
GET /api/admin/staff
Response: [{ "id": 1, "name": "...", "email": "...", "role": "staff", "is_active": true }]
```

### Create Staff
```
POST /api/admin/staff
Body: { "name": "New Staff", "email": "staff@test.com", "password": "pass", "role": "staff" }
Response: { "id": 2, "name": "New Staff", "email": "staff@test.com", "role": "staff" }
```

### Update Staff
```
PUT /api/admin/staff/{staff_id}
Body: { "name": "Updated Name", "role": "admin" }
```

### Admin Reset Staff Password
```
PUT /api/admin/staff/{staff_id}/password
Body: { "new_password": "newpass123" }
Response: { "detail": "Password updated successfully" }
```

### List Permissions
```
GET /api/admin/permissions
Response: [{ "id": 1, "key": "edit_menu", "description": "..." }]
```

### Get Role Permissions
```
GET /api/admin/roles/{role}/permissions
Response: [{ "id": 1, "key": "edit_menu", "description": "..." }]
```

### Update Role Permissions
```
PUT /api/admin/roles/{role}/permissions
Body: { "permission_ids": [1, 2, 3] }
```

---

## Categories (`/api/categories`)

### List Categories (Public)
```
GET /api/categories
Response: [{ "id": 1, "name": "Appetizers", "sort_order": 0 }]
```

### Get Category (Public)
```
GET /api/categories/{category_id}
```

### Create Category (Admin)
```
POST /api/admin/categories
Body: { "name": "Main Course", "sort_order": 1 }
```

### Update Category (Admin)
```
PUT /api/admin/categories/{category_id}
Body: { "name": "Updated Name" }
```

### Delete Category (Admin)
```
DELETE /api/admin/categories/{category_id}
```

---

## Menu Items (`/api/menu-items`)

### List Menu Items (Public)
```
GET /api/menu-items?category_id=1&available_only=true
Response: [{ "id": 1, "name": "...", "price": 250.0, "image_url": "...", ... }]
```

### Get Menu Item (Public)
```
GET /api/menu-items/{item_id}
```

### Create Menu Item (Admin)
```
POST /api/admin/menu-items
Body: {
  "category_id": 1,
  "name": "Momo",
  "description": "Steamed dumplings",
  "price": 250.0,
  "image_url": "https://res.cloudinary.com/.../momo.jpg",
  "is_available": true,
  "sort_order": 0
}
```

### Update Menu Item (Admin)
```
PUT /api/admin/menu-items/{item_id}
Body: { "price": 300.0, "is_available": false }
```
If `image_url` changes, old image is deleted from Cloudinary.

### Delete Menu Item (Admin)
```
DELETE /api/admin/menu-items/{item_id}
```
Deletes the item and its image from Cloudinary.

---

## Restaurant Profile (`/api/restaurant-profile`)

### Get Profile (Public)
```
GET /api/restaurant-profile
Response: { "name": "...", "logo_url": "...", "business_hours": {...} }
```

### Update Profile (Admin)
```
PUT /api/admin/restaurant-profile
Body: {
  "name": "My Restaurant",
  "logo_url": "https://res.cloudinary.com/.../logo.png",
  "business_hours": {
    "sun": {"open": "10:00", "close": "20:00"},
    "mon": {"open": "10:00", "close": "20:00"},
    "tue": {"open": "10:00", "close": "20:00"},
    "wed": {"open": "10:00", "close": "20:00"},
    "thu": {"open": "10:00", "close": "20:00"},
    "fri": {"open": "10:00", "close": "20:00"},
    "sat": null
  }
}
```
If `logo_url` changes, old logo is deleted from Cloudinary.

---

## Promo Banners (`/api/promo-banners`)

### List Active Banners (Public)
```
GET /api/promo-banners
Response: [{ "id": 1, "title": "...", "image_url": "...", ... }]
```

### Create Banner (Admin)
```
POST /api/admin/promo-banners
Body: { "title": "Summer Sale", "image_url": "...", "is_active": true, "sort_order": 0 }
```

### Update Banner (Admin)
```
PUT /api/admin/promo-banners/{banner_id}
Body: { "title": "Updated Title" }
```

### Delete Banner (Admin)
```
DELETE /api/admin/promo-banners/{banner_id}
```

---

## Campaigns (`/api/campaigns`)

### List Active Campaigns (Public)
```
GET /api/campaigns/available?order_total=1000
Response: [{ "id": 1, "name": "...", "code": "SAVE20", "discount_type": "percentage", ... }]
```

### Validate Campaign (Public)
```
POST /api/campaigns/validate
Body: { "code": "SAVE20", "order_total": 1000 }
Response: { "valid": true, "discount_amount": 200, "campaign_id": 1 }
```

### List All Campaigns (Admin)
```
GET /api/admin/campaigns
Response: [{ "id": 1, "name": "...", "usage_count": 5, ... }]
```

### Create Campaign (Admin)
```
POST /api/admin/campaigns
Body: {
  "name": "20% Off",
  "code": "SAVE20",
  "discount_type": "percentage",
  "discount_value": 20,
  "max_discount_amount": 500,
  "min_order_amount": 500,
  "is_active": true
}
```

### Update Campaign (Admin)
```
PUT /api/admin/campaigns/{campaign_id}
Body: { "discount_value": 25 }
```

### Delete Campaign (Admin)
```
DELETE /api/admin/campaigns/{campaign_id}
```

---

## Orders (`/api/orders`)

### Create Order
```
POST /api/orders
Body: {
  "order_type": "dine_in",
  "table_number": "5",
  "payment_method": "cash",
  "campaign_code": "SAVE20",
  "items": [
    { "menu_item_id": 1, "quantity": 2 },
    { "menu_item_id": 3, "quantity": 1 }
  ]
}
Response: { "id": 1, "total_amount": 800, "payment_status": "pending", ... }
```

### List Orders
```
GET /api/orders
Customers see only their orders. Staff see all.
Response: [{ "id": 1, "order_type": "...", "total_amount": 800, ... }]
```

### Get Order Detail
```
GET /api/orders/{order_id}
Response: { "id": 1, "items": [...], "status_history": [...], ... }
```

### Update Fulfillment Status
```
PATCH /api/orders/{order_id}/fulfillment
Body: { "status": "preparing" }
Permission: update_fulfillment_status
```
When status changes to `completed`, invoice email is sent to customer.

### Update Payment Status
```
PATCH /api/orders/{order_id}/payment-status
Body: { "status": "paid", "reference": "CASH-001" }
Permission: verify_payment
```

---

## Payments (`/api/payments`)

### Initiate Payment
```
POST /api/payments/initiate
Body: { "order_id": 1, "provider": "esewa" }
Response: {
  "provider": "esewa",
  "redirect_url": "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
  "form_data": { ... }
}
```

### eSewa Callback
```
GET /api/payments/callback/esewa?order_id=1&data=<base64_encoded_json>
```

### Khalti Callback
```
GET /api/payments/callback/khalti?order_id=1&pidx=<pidx>&status=Completed
```

---

## TOTP 2FA (`/api/totp`)

### Setup TOTP
```
POST /api/totp/setup
Response: { "secret": "...", "provisioning_uri": "...", "qr_code": "data:image/png;base64,..." }
```

### Verify & Enable
```
POST /api/totp/verify
Body: { "code": "123456" }
Response: { "detail": "TOTP enabled successfully" }
```

### Verify Login
```
POST /api/totp/verify-login
Body: { "code": "123456", "temp_token": "...", "remember_device": true }
Response: { "access_token": "...", "trusted_token": "..." }
```

### Disable TOTP
```
POST /api/totp/disable
Body: { "code": "123456" }
```

### List Trusted Devices
```
GET /api/totp/trusted-devices
Response: [{ "id": 1, "user_agent": "...", "expires_at": "..." }]
```

---

## WebAuthn Passkeys (`/api/webauthn`)

### Register Begin
```
POST /api/webauthn/register/begin
Body: { "email": "user@example.com", "user_type": "customer" }
Response: <WebAuthn registration options JSON>
```

### Register Finish
```
POST /api/webauthn/register/finish
Body: { "email": "user@example.com", "user_type": "customer", "credential": {...} }
Response: { "verified": true, "message": "Passkey registered" }
```

### Authenticate Begin
```
POST /api/webauthn/authenticate/begin
Body: { "email": "user@example.com", "user_type": "customer" }
Response: <WebAuthn authentication options JSON>
```

### Authenticate Finish
```
POST /api/webauthn/authenticate/finish
Body: { "credential": {...} }
Response: { "access_token": "...", "user_type": "customer" }
```

### List Credentials
```
GET /api/webauthn/credentials
Response: [{ "id": 1, "name": "...", "credential_device_type": "...", ... }]
```

### Delete Credential
```
DELETE /api/webauthn/credentials/{credential_id}
```

---

## Email Verification (`/api/customer/email`)

### Request Verification
```
POST /api/customer/email/request-verification
Body: { "email": "customer@example.com" }
Response: { "detail": "Verification code sent", "email": "..." }
```

### Verify Email
```
POST /api/customer/email/verify
Body: { "email": "customer@example.com", "code": "123456" }
Response: { "detail": "Email verified successfully" }
```
