# Migration Notes

## Completed Migrations

### Exercise 2: logEvent → track migration
- Replaced deprecated `logEvent(name, payload)` with `track({ name, props })` across:
  - `src/notifications.ts`: Updated `sendOrderShipped()` and `sendReturnApproved()`
  - `src/orders.ts`: Updated `markDelivered()` and `cancelOrder()`
- All imports updated from `logEvent` to `track`
- Migration verified: Grep shows no remaining live calls to `logEvent()` outside of the deprecated definition in `analytics.ts`

### Exercise 3: Event name standardization
- Renamed analytics event: `order_cancelled` → `order_canceled` (one L) in `src/orders.ts`
- This standardizes spelling across the codebase for consistency

## Migration Strategy
The migration followed the **find → read-only-what-matters → change** loop:
1. **Glob** to map test files (`*.test.ts`)
2. **Grep** to locate exact call sites (`logEvent(` in src/)
3. **Read** only `analytics.ts` to understand the replacement signature
4. **Edit** each file individually with minimal, targeted changes
5. **Verify** with Grep to confirm no remaining deprecated calls

This incremental approach avoids loading the entire repository and ensures precise, scriptable changes.
