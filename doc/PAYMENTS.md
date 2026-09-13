# Payment Gateway Integration

## Overview

eMenu supports two Nepali payment gateways:

| Gateway | Type | Flow |
|---------|------|------|
| eSewa | Form redirect | Browser submits form to eSewa |
| Khalti | API + redirect | Server initiates, user redirected to payment page |

---

## eSewa Integration

### Flow
```
1. Frontend calls POST /api/payments/initiate
   { "order_id": 1, "provider": "esewa" }

2. Backend returns form_data + redirect_url

3. Frontend creates hidden form, auto-submits to eSewa:
   action="https://rc-epay.esewa.com.np/api/epay/main/v2/form"
   method="POST"

4. User pays on eSewa

5. eSewa redirects to success_url with base64-encoded data:
   GET /api/payments/callback/esewa?order_id=1&data=<base64>

6. Backend decodes data, verifies HMAC-SHA256 signature
7. Backend verifies amount matches order total
8. Order marked as paid
```

### Signature Generation
```python
message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
signature = hmac.new(secret_key, message, sha256).digest()
signature_b64 = base64.b64encode(signature)
```

### Callback Verification
- Decodes base64 `data` parameter
- Verifies HMAC-SHA256 signature
- Validates amount matches order total
- Validates `transaction_uuid` matches

### Test Credentials
- Merchant ID: `EPAYTEST`
- Secret Key: `8gBm/:&EnhH.1/q`
- UAT URL: `https://rc-epay.esewa.com.np/api/epay/main/v2/form`
- Status API: `https://rc-epay.esewa.com.np/api/epay/transaction/status/`

---

## Khalti Integration

### Flow
```
1. Frontend calls POST /api/payments/initiate
   { "order_id": 1, "provider": "khalti" }

2. Backend calls Khalti API to initiate payment
   POST https://dev.khalti.com/api/v2/epayment/initiate/

3. Khalti returns { "pidx": "...", "payment_url": "..." }

4. User redirected to payment_url

5. User pays, Khalti redirects to return_url:
   GET /api/payments/callback/khalti?order_id=1&pidx=xxx&status=Completed

6. Backend calls Khalti Lookup API to verify
   POST https://dev.khalti.com/api/v2/epayment/lookup/

7. Backend validates amount matches order total
8. Order marked as paid
```

### Amount Format
Khalti expects amount in **paisa** (not rupees):
- NPR 100 = 10000 paisa
- `amount_paisa = int(total_amount * 100)`

### Callback Verification
- Calls Khalti Lookup API with `pidx`
- Verifies `status == "Completed"`
- Validates `total_amount` matches order total (in paisa)

### Test Credentials
- Sign up at https://khalti.com as merchant
- Get Secret Key from dashboard
- Sandbox URL: `https://dev.khalti.com/api/v2/epayment/initiate/`

---

## Security Measures

| Measure | Implementation |
|---------|---------------|
| Server-side verification | Both gateways verified via API, never trust client redirect |
| Signature verification | eSewa: HMAC-SHA256 on callback data |
| Amount validation | Both: compare gateway amount with order total |
| Idempotency | Order status checked before updating |
| Audit trail | All payment changes logged in `order_status_history` |

---

## Payment Status Flow

```
Order Created → payment_status: "pending"
                ↓
eSewa/Khalti callback received
                ↓
If verified → payment_status: "paid"
If failed   → payment_status: "failed"
```

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Missing callback params | 400 Bad Request |
| Signature mismatch | 400 Bad Request |
| Amount mismatch | 400 Bad Request |
| Order not found | 404 Not Found |
| Gateway API error | Logs error, returns 500 |

Emails are sent asynchronously — failures are logged but don't affect the response.
