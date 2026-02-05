# SQL Queries for Grafana (PBN Command Center)

Use these queries in Grafana with the SQLite Data Source points to `pbn_monitor.db`.

## 1. Success Rate (Gauge)
Calculates the overall success percentage.
```sql
SELECT 
  (SUM(success) * 100.0 / (SUM(success) + SUM(errors))) as "Success Rate"
FROM stats;
```

## 2. Publication Dynamics (Time Series)
Shows posts and errors over time.
```sql
SELECT
  timestamp as time,
  success as "Successful Posts",
  errors as "Errors",
  links as "Internal Links"
FROM stats
ORDER BY timestamp ASC;
```

## 3. Total Links in Network (Stat)
Grand total of all internal links ever placed.
```sql
SELECT SUM(links) FROM stats;
```

## 4. Run Status (Table)
Shows history of the last 10 runs.
```sql
SELECT 
  datetime(timestamp, 'localtime') as "Date",
  success as "Success",
  errors as "Errors",
  links as "Links"
FROM stats
ORDER BY timestamp DESC
LIMIT 10;
```

## 5. ROI Индексации (Gauge)
Стоимость одной успешной ссылки.
```sql
SELECT 
  sum(cost_usd) / NULLIF(sum(success_count), 0) as "Cost per Link" 
FROM publications;
```

## 6. Эффективность Перелинковки (Bar Chart)
Сравнение новых постов и обновленных старых.
```sql
SELECT 
  'Internal Links' as category, sum(links_inserted) as count FROM publications
UNION ALL
  SELECT 'New Post Links' as category, sum(success_count) as count FROM publications;
```

---

## Docker Command to start Grafana
If you don't have Grafana installed, run this in your terminal:
```bash
docker run -d -p 3000:3000 --name=antigravity-grafana grafana/grafana
```
*Note: We are using `antigravity-grafana` with plugin `frser-sqlite-datasource` installed.*
