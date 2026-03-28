# Geo-Adaptive Pricing Research — 2026-03-28

## Key Finding
Nobody uses pure PPP. Hybrid: PPP baseline + manual tier override + local currency decision.

## Implementation Stack for Volaura
1. **Phase 1 (free):** Stripe Adaptive Pricing — local currency display only
2. **Phase 2 ($29/mo):** ParityDeals — real PPP discounts + VPN detection
3. **Phase 3 (DIY):** World Bank PPP CSV + dynamic `price_data` in Stripe Checkout

## Country Detection Stack
1. Cloudflare `CF-IPCountry` header (free, zero latency)
2. Billing address at Stripe Checkout (authoritative)
3. ASN analysis via Fingerprint.com (VPN detection)
4. Account country lock after first payment

## Price Tiers (benchmarked against Spotify/Netflix/Duolingo)

| Market | Tier | PPP Factor | Pro Price | Ultra Price |
|--------|------|-----------|-----------|-------------|
| UAE | Tier 1 (Wealthy) | 0.95 | $9.50/mo | $24.70/mo |
| USA/EU | Tier 1 | 1.00 | $10.00/mo | $26.00/mo |
| Azerbaijan | Tier 2 (Emerging) | 0.50 | 4.99 AZN/mo | 12.99 AZN/mo |
| Kazakhstan | Tier 3 | 0.45 | $4.50/mo | $11.70/mo |
| Georgia | Tier 3 | 0.40 | $4.00/mo | $10.40/mo |
| Turkey | Tier 4 (Challenged) | 0.25 | $2.50/mo | $6.50/mo |

## Anti-Arbitrage (layered)
1. Payment method lock (Turkish plan requires Turkish card)
2. Account country lock after subscription
3. VPN/ASN detection (ParityDeals or Fingerprint.com)
4. Short-lived coupon codes (15-60 min TTL)

## AZ-Specific Payment Methods (CRITICAL)
- **Birbank** — 3.4M active users, PRIMARY
- **m10 (PashaPay)** — commission-free, QR-based
- **eManat** — payment terminals
- **GoldenPay** — aggregator
- Stripe is NOT locally familiar. Birbank/m10 integration non-negotiable.

## Stripe Implementation
```python
# FastAPI: dynamic PPP pricing
session = stripe.checkout.Session.create(
    line_items=[{
        "price_data": {
            "currency": "usd",
            "unit_amount": compute_ppp_price(country_code, base_price_cents),
            "product_data": {"name": "Volaura Pro"},
        },
        "quantity": 1,
    }],
    mode="subscription",
)
```

## Sources
- Stripe Adaptive Pricing: +4.7% conversion, +5.4% LTV (1.5M checkout A/B test)
- Spotify AZ: $5.49, Turkey: 99 TRY (~$2.32), Georgia: $3.29
- ParityDeals: $29+/mo, React SDK, Next.js compatible
