# PBN Management Guide: Golden Rules

This document outlines the strategy for operating the Antigravity PBN automation system for maximum SEO impact and minimal risk.

## 1. Safety & Efficiency (Operational Rules)

### 🛑 Batching (The 50/Day Rule)
Do not process the entire network at once.
- **Rule:** Launch in batches of 50 sites per day.
- **Why:** Sudden activity spikes on expired/parked domains trigger Google manual review. Gradual filling looks like organic growth.

### 🔄 Anchor Rotation
Avoid "Over-optimization".
- **Rule:** Use a mix of:
  - Exact match: `лучшие финансовые советы` (20%)
  - LSI/Synonyms: `советы по деньгам`, `финансовая грамотность` (40%)
  - Branded/Generic: `тут`, `по этой ссылке`, `ознакомиться` (40%)
- **Tools:** Use Gemini in the prompt to "vary the anchor text case and phrasing naturally".

### 🧹 Database Sanitation
- **Rule:** Monthly health check.
- **Action:** Remove sites from `sites_data.json` that are:
  - Deindexed by Google (`site:domain.com` manual check).
  - Showing repeated 405/500 errors.
  - Hacked or compromised.

## 2. Content & Link Strategy

### 🧠 Persona Diversity
Monitor the `dashboard.py` outputs. 
- If "lifestyle" persona results in 30% faster indexing (verified via GSC/Search), shift the `author_style` in your JSON to prioritize it.

### 🔗 Link Density (Safety Valve)
The script is hardcoded to skip updates if a post has `> 4` links.
- **Maintenance:** If your efficiency drops below 20%, it's time to publish 10-20 "link-free" articles to refresh the site's capacity.

## 3. How to Run

1. **Update Data:** Fill `sites_data.json`.
2. **Launch Batch:** `python3 publish_post.py sites_data.json`
3. **Verify:** `python3 verify_posts.py results.json`
4. **Analyze:** `python3 dashboard.py`
