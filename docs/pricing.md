# Pricing & free-tier strategy (USA)

All numbers below are accurate as of **April 2026**; always confirm on the
vendor's pricing page before building a production collector. The strategies
assume a USA-based account billed in USD.

## Google Maps Platform

- **Product**: Directions API.
- **Pricing page**: <https://mapsplatform.google.com/pricing/>
- **SKU**: `Directions Advanced` (with traffic) or `Directions Basic`.
- **Free tier**: $200 of monthly credits across the platform. Basic Directions
  is priced per request (~$5 / 1k), so the $200 ceiling covers **~40k
  requests/month** on Basic.
- **Staying free**: poll at most every ~60 seconds across all routes
  (40k / (30 days × 24 h × 60 min) ≈ 0.92 req/min). Use `traffic_model=best_guess`
  only when you actually need live traffic, since it's a more expensive SKU.

## Bing Maps

- **Product**: Routes API.
- **Pricing**: <https://www.microsoft.com/en-us/maps/bing-maps/pricing>
- **SKU**: `Basic Key / Non-billable Transactions` (legacy) or **Azure Maps**
  (Microsoft is migrating Bing Maps features to Azure). A `Basic` key allows
  **125k non-billable transactions per calendar year**.
- **Staying free**: budget 125k / 365 ≈ 342 req/day. One trip every ~4 minutes
  fits easily.

## TomTom

- **Product**: Routing API.
- **Pricing**: <https://developer.tomtom.com/store/maps-api>
- **Free tier**: **2,500 requests/day** (Developer plan).
- **Staying free**: one trip every 35 seconds sustained, more than enough.

## HERE

- **Product**: Routing v8.
- **Pricing**: <https://www.here.com/get-started/pricing>
- **Free tier**: **30k transactions/month** on the Freemium plan.
- **Staying free**: 30k / 30 days = 1,000/day, ≈ one every 90 seconds.

## MapQuest

- **Product**: Directions API (open & licensed).
- **Pricing**: <https://developer.mapquest.com/plans>
- **Free tier**: **15,000 transactions/month** on the Community plan.
- **Staying free**: 500/day; every ~3 minutes.

## Mapbox

- **Product**: Directions API (driving-traffic).
- **Pricing**: <https://www.mapbox.com/pricing>
- **Free tier**: First **100,000 Directions requests/month** free.
- **Staying free**: practically unlimited for a personal collector.

## Azure Maps

- **Product**: Route service.
- **Pricing**: <https://azure.microsoft.com/en-us/pricing/details/azure-maps/>
- **Free tier** (Gen2 S0 SKU): 250,000 transactions/month.
- **Staying free**: effectively unlimited for a single collector.

## Multi-provider budget sheet

If you want to hit every provider once per poll, the binding constraint is
**MapQuest (500/day)**. At one poll every ~3 minutes across weekday work
hours, you stay within every free tier listed above.
