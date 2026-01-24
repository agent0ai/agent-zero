---
description: Monitor keyword rankings, organic traffic, Core Web Vitals, and backlinks with automated alerts and reporting
argument-hint: [--frequency <daily|weekly|monthly>] [--alerts] [--dashboard]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, WebFetch, Bash
---

SEO Monitoring: **${ARGUMENTS}**

## Continuous SEO Performance Monitoring

Use the Task tool with subagent_type=seo-specialist to set up comprehensive SEO monitoring with the following specifications:

### Input Parameters

**Monitoring Frequency**: ${FREQUENCY:-daily} (hourly, daily, weekly, monthly)
**Enable Alerts**: ${ALERTS:-true} (Alert on significant changes)
**Dashboard**: ${DASHBOARD:-true} (Generate visual dashboard)
**Competitors**: ${TRACK_COMPETITORS:-true} (Monitor competitor performance)

### Objectives

You are tasked with implementing continuous monitoring of SEO metrics to track progress, detect issues, and identify opportunities. Your implementation must:

#### 1. Keyword Ranking Tracking

**Keyword Monitoring Setup**:

```javascript
const keywordTracking = {
  // Primary keywords (high priority)
  primary: [
    {
      keyword: "project management software",
      targetUrl: "/",
      currentRank: 12,
      previousRank: 15,
      change: +3,
      searchVolume: 18000,
      difficulty: 72,
      intent: "commercial",
      tracking: "daily"
    },
    {
      keyword: "best pm tools 2024",
      targetUrl: "/blog/best-pm-tools",
      currentRank: 5,
      previousRank: 8,
      change: +3,
      searchVolume: 2400,
      difficulty: 58,
      intent: "informational",
      tracking: "daily"
    }
  ],

  // Secondary keywords (medium priority)
  secondary: [
    {
      keyword: "team collaboration software",
      currentRank: 24,
      searchVolume: 6500,
      tracking: "weekly"
    },
    // ... more keywords
  ],

  // Long-tail keywords (lower priority)
  longTail: [
    {
      keyword: "project management for remote teams",
      currentRank: 8,
      searchVolume: 480,
      tracking: "weekly"
    }
  ],

  // Branded keywords
  branded: [
    {
      keyword: "acme project manager",
      currentRank: 1,
      searchVolume: 1200,
      tracking: "weekly",
      alert: "if rank > 3"  // Alert if not in top 3
    }
  ]
};
```

**Ranking Trend Analysis**:

```markdown
## Keyword Performance Report

### Top Movers (Last 30 Days)

**Biggest Gains** 🟢:
1. "best pm tools 2024": #8 → #5 (+3) - 2,400 searches/month
2. "project management software": #15 → #12 (+3) - 18,000 searches/month
3. "agile pm tools": #25 → #18 (+7) - 950 searches/month

**Estimated Traffic Gain**: +580 monthly visits

**Biggest Losses** 🔴:
1. "free project management": #4 → #9 (-5) - 4,200 searches/month
2. "pm software comparison": #11 → #15 (-4) - 1,800 searches/month

**Estimated Traffic Loss**: -420 monthly visits

**Net Change**: +160 monthly visits

### Rankings Distribution

| Position | Count | % of Total |
|----------|-------|-----------|
| Top 3 | 12 | 15% |
| Top 10 | 28 | 35% |
| Top 20 | 45 | 56% |
| Top 50 | 68 | 85% |
| Top 100 | 78 | 98% |

**Average Position**: 18.4 (↑ improved from 20.1)

### Ranking Opportunities

**Nearly Top 10** (positions 11-15):
- "project management software" - #12 (18K searches)
- "pm software comparison" - #15 (1.8K searches)
- "team collaboration tools" - #14 (6.5K searches)

**Optimization Recommendation**: Target these 3 keywords for quick wins
**Potential Traffic**: +2,850 monthly visits if all reach top 10
```

#### 2. Organic Traffic Monitoring

**Traffic Dashboard**:

```javascript
const trafficMetrics = {
  overview: {
    thisMonth: {
      sessions: 12500,
      users: 10200,
      pageviews: 45000,
      avgSessionDuration: "3:24",
      bounceRate: "42%",
      pagesPerSession: 3.6
    },

    lastMonth: {
      sessions: 11000,
      change: "+13.6%",
      trend: "up"
    },

    yearAgo: {
      sessions: 7800,
      change: "+60.3%",
      trend: "strong growth"
    }
  },

  // Traffic by channel
  channels: {
    organic: {
      sessions: 8750,  // 70% of total
      change: "+18%",
      conversions: 219,
      conversionRate: "2.5%"
    },
    direct: {
      sessions: 2000,  // 16%
      change: "+5%"
    },
    referral: {
      sessions: 1250,  // 10%
      change: "+8%"
    },
    social: {
      sessions: 500,  // 4%
      change: "-2%"
    }
  },

  // Traffic by page
  topPages: [
    {
      url: "/blog/best-pm-tools",
      sessions: 1850,
      change: "+45%",
      bounceRate: "35%",
      avgTimeOnPage: "4:12"
    },
    {
      url: "/",
      sessions: 1650,
      change: "+12%",
      bounceRate: "38%"
    },
    {
      url: "/pricing",
      sessions: 980,
      change: "+8%",
      bounceRate: "28%",
      conversions: 45
    }
  ],

  // Landing pages
  topLandingPages: [
    {
      url: "/blog/best-pm-tools",
      entrances: 1620,
      bounceRate: "32%",
      conversionRate: "2.8%"
    }
  ]
};
```

**Anomaly Detection**:

```javascript
const detectAnomalies = (metrics, baseline) => {
  const anomalies = [];

  // Traffic drop detection
  if (metrics.sessions < baseline.sessions * 0.8) {
    anomalies.push({
      type: "traffic_drop",
      severity: "high",
      metric: "sessions",
      current: metrics.sessions,
      expected: baseline.sessions,
      drop: `${((1 - metrics.sessions/baseline.sessions) * 100).toFixed(1)}%`,
      alert: true,
      message: "⚠️ Traffic dropped 20%+ - investigate immediately",
      possibleCauses: [
        "Google algorithm update",
        "Technical issue (site down, robots.txt)",
        "Ranking losses for key terms",
        "Seasonal variation",
        "Competitor gains"
      ]
    });
  }

  // Bounce rate spike
  if (parseFloat(metrics.bounceRate) > parseFloat(baseline.bounceRate) * 1.2) {
    anomalies.push({
      type: "bounce_rate_spike",
      severity: "medium",
      current: metrics.bounceRate,
      expected: baseline.bounceRate,
      alert: true,
      possibleCauses: [
        "Poor page experience",
        "Misleading meta descriptions",
        "Slow load times",
        "Mobile usability issues"
      ]
    });
  }

  // Conversion rate drop
  if (metrics.conversionRate < baseline.conversionRate * 0.85) {
    anomalies.push({
      type: "conversion_drop",
      severity: "high",
      alert: true,
      message: "Revenue at risk - conversion rate dropped significantly"
    });
  }

  return anomalies;
};
```

#### 3. Core Web Vitals Monitoring

**Performance Tracking**:

```javascript
const coreWebVitals = {
  desktop: {
    LCP: {
      p75: 1.8,  // 75th percentile
      status: "good",  // <2.5s
      trend: "stable",
      history: [2.1, 1.9, 1.8, 1.8, 1.7]
    },
    FID: {
      p75: 45,
      status: "good",  // <100ms
      trend: "improving"
    },
    CLS: {
      p75: 0.08,
      status: "good",  // <0.1
      trend: "stable"
    }
  },

  mobile: {
    LCP: {
      p75: 2.4,
      status: "good",  // <2.5s
      trend: "improving",
      pages_failing: [
        "/blog/long-article",  // LCP: 3.2s
        "/products/demo"       // LCP: 2.8s
      ]
    },
    FID: {
      p75: 68,
      status: "good"
    },
    CLS: {
      p75: 0.12,
      status: "needs_improvement",  // >0.1
      alert: true,
      pages_failing: [
        "/",           // CLS: 0.15
        "/blog/post"   // CLS: 0.13
      ]
    }
  },

  // Field data (real users via CrUX)
  fieldData: {
    goodUrls: 820,   // 82% of URLs
    needsImpUrls: 150,  // 15%
    poorUrls: 30     // 3%
  },

  // Opportunities
  optimization: {
    priority: "Fix mobile CLS issues",
    impact: "Move 150 URLs from 'needs improvement' to 'good'",
    pages: ["/", "/blog/post"],
    fix: "Add width/height to images, reserve space for ads"
  }
};
```

#### 4. Backlink Monitoring

**Link Profile Tracking**:

```javascript
const backlinkMonitoring = {
  summary: {
    totalBacklinks: 1245,
    change_30d: +23,
    referringDomains: 387,
    change_30d: +5,
    newLinks: 35,
    lostLinks: 12,
    netGain: +23
  },

  // New backlinks (last 30 days)
  newBacklinks: [
    {
      fromUrl: "https://techcrunch.com/article",
      toUrl: "https://example.com/",
      anchorText: "project management platform",
      domainRating: 93,
      traffic: "estimated 500/month",
      date: "2024-11-10",
      status: "High value link! 🎉"
    },
    {
      fromUrl: "https://smallblog.com/review",
      toUrl: "https://example.com/pricing",
      domainRating: 28,
      traffic: "low",
      date: "2024-11-12"
    }
  ],

  // Lost backlinks
  lostBacklinks: [
    {
      fromUrl: "https://industry-site.com/old-article",
      status: "Page removed (404)",
      domainRating: 65,
      action: "Reach out to restore or replace"
    }
  ],

  // Toxic links detected
  toxicLinks: [
    {
      fromUrl: "https://spam-site.xyz",
      spamScore: 85,
      action: "Disavow",
      status: "Added to disavow file"
    }
  ],

  // Link velocity
  velocity: {
    thisMonth: +23,
    lastMonth: +18,
    trend: "Healthy growth",
    alert: false
  },

  // Anchor text distribution
  anchorText: {
    branded: "39%",  // ✅ Natural
    naked: "25%",    // ✅ Natural
    generic: "20%",  // ✅ Natural
    exactMatch: "10%", // ✅ Safe
    partialMatch: "6%"  // ✅ Safe
  }
};
```

#### 5. Competitor Monitoring

**Competitive Intelligence**:

```javascript
const competitorTracking = {
  competitors: [
    {
      name: "Competitor A",
      domain: "competitor-a.com",
      metrics: {
        domainRating: 67,
        organicKeywords: 4120,
        organicTraffic: 28000,
        backlinks: 3450,
        growth_30d: "+8%"
      },
      keywordOverlap: {
        competing: 156,  // Keywords we both rank for
        theyWin: 89,     // They rank higher
        weWin: 67,       // We rank higher
        opportunities: [
          {
            keyword: "agile project management",
            theirRank: 5,
            ourRank: 18,
            searchVolume: 2400,
            action: "Create comprehensive guide"
          }
        ]
      }
    }
  ],

  // Share of voice
  shareOfVoice: {
    us: "18%",
    competitorA: "32%",
    competitorB: "24%",
    competitorC: "12%",
    others: "14%"
  }
};
```

#### 6. Automated Alerts

**Alert Configuration**:

```javascript
const alerts = {
  // Critical alerts (immediate notification)
  critical: [
    {
      condition: "traffic_drop > 20%",
      channels: ["email", "sms", "slack"],
      message: "🚨 CRITICAL: Traffic dropped 20%+ in last 24 hours"
    },
    {
      condition: "site_down",
      channels: ["sms", "pagerduty"],
      message: "🚨 CRITICAL: Website unreachable"
    },
    {
      condition: "branded_keyword_rank > 3",
      channels: ["email", "slack"],
      message: "⚠️ Branded keyword not in top 3"
    }
  ],

  // High priority alerts
  high: [
    {
      condition: "top_10_keyword_dropped_out",
      frequency: "daily",
      message: "📉 Keyword dropped out of top 10: {keyword}"
    },
    {
      condition: "core_web_vitals_failed",
      frequency: "daily",
      message: "⚠️ Core Web Vitals failed on: {urls}"
    },
    {
      condition: "high_value_backlink_lost",
      frequency: "weekly",
      message: "🔗 Lost backlink from DR 50+ domain"
    }
  ],

  // Medium priority
  medium: [
    {
      condition: "ranking_improved_to_page_1",
      frequency: "weekly",
      message: "🎉 Keyword reached page 1: {keyword}"
    },
    {
      condition: "new_competitor_ranking",
      frequency: "weekly"
    }
  ]
};
```

#### 7. Automated Reporting

**Weekly SEO Report**:

```markdown
# SEO Weekly Report
**Week of November 11-17, 2024**

## Executive Summary

**Overall Performance**: 📈 Strong Week
- Traffic: 12,500 (+8% vs last week)
- Rankings: Average position 18.4 (↑ from 20.1)
- Backlinks: +23 new links
- Core Web Vitals: 82% URLs passing

## Key Highlights

### Wins 🎉
1. **"best pm tools 2024" reached #5** (was #8)
   - Impact: +120 monthly visits
2. **TechCrunch backlink acquired** (DR 93)
   - High-value editorial link
3. **Mobile performance improved**
   - LCP: 2.6s → 2.4s

### Concerns ⚠️
1. **"free project management" dropped to #9** (was #4)
   - Loss: ~200 monthly visits
   - Action: Content refresh recommended

2. **Homepage CLS needs fixing** (0.15, target <0.1)
   - Affecting mobile rankings
   - Action: Add image dimensions

## Detailed Metrics

### Traffic
- Organic: 8,750 (+18%)
- Direct: 2,000 (+5%)
- Referral: 1,250 (+8%)

### Rankings
- Top 3: 12 keywords
- Top 10: 28 keywords
- Page 1 opportunities: 8 keywords

### Backlinks
- New: 35
- Lost: 12
- Net: +23

## Action Items for Next Week

**Priority 1 (High Impact)**:
1. ✅ Fix homepage CLS issue (2 hours)
2. ✅ Optimize "free project management" page (3 hours)
3. ✅ Create content for "agile pm" keyword gap (4 hours)

**Priority 2 (Medium Impact)**:
4. ⚠️ Reach out to sites with lost backlinks (2 hours)
5. ⚠️ Submit updated sitemap (30 min)

**Expected Impact**: +350 monthly visits

---

**Report Generated**: November 17, 2024 9:00 AM
**Next Report**: November 24, 2024
```

### Implementation Steps

**Step 1: Setup**

1. Configure tracking tools (Google Analytics, Search Console, Ahrefs)
2. Set up keyword tracking list
3. Configure Core Web Vitals monitoring
4. Set baseline metrics

**Step 2: Integration**

1. Connect to Google Search Console API
2. Connect to Analytics API
3. Connect to backlink monitoring tool
4. Set up data pipeline

**Step 3: Dashboard Creation**

1. Build monitoring dashboard
2. Create visualization charts
3. Set up real-time updates
4. Configure exports (PDF, CSV)

**Step 4: Alerts**

1. Define alert conditions
2. Configure notification channels
3. Test alert delivery
4. Set up escalation rules

**Step 5: Reporting**

1. Create automated reports
2. Schedule delivery (daily/weekly/monthly)
3. Customize for stakeholders
4. Track report engagement

### Output Requirements

**Generated Files**:

- `SEO_DASHBOARD.html` - Live monitoring dashboard
- `weekly-report-YYYY-MM-DD.pdf` - Weekly report
- `alerts-log.json` - Alert history
- `tracking-config.json` - Monitoring configuration

## ROI Impact

**Early Problem Detection**:

- **Identify issues before major impact** - 80% faster response
- **Prevent traffic losses** - Catch ranking drops early
- **Capitalize on wins** - Double down on what works

**Time Savings**:

- **Manual monitoring**: 10 hours/week → 0 hours (automated)
- **Report generation**: 4 hours/week → 10 minutes
- **Data analysis**: Automated insights vs manual analysis

**Revenue Protection**:

- **Prevent traffic losses**: $50,000/year
- **Faster issue resolution**: $25,000/year
- **Opportunity identification**: $20,000/year

**Total Value**: $95,000/year

- Revenue protection: $75,000/year
- Time savings: $20,000/year

## Success Criteria

✅ **All key metrics tracked**
✅ **Alerts configured and tested**
✅ **Dashboard accessible and real-time**
✅ **Automated reports delivered**
✅ **Zero monitoring gaps**

**Monitoring Coverage**:

- 100% of target keywords tracked
- Daily ranking updates
- Hourly traffic monitoring
- Real-time Core Web Vitals
- Daily backlink monitoring
- Weekly competitor tracking

## Next Steps

1. Configure tracking tools
2. Set up monitoring dashboard
3. Enable automated alerts
4. Schedule first weekly report
5. Review and optimize alerts based on noise

---

**Monitoring Status**: 🟢 Ready to Deploy
**Tracking Coverage**: Comprehensive
**Annual ROI**: $95,000
