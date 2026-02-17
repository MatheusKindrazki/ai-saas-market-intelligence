#!/usr/bin/env python3
"""Demo script for AI SaaS Market Intelligence Platform"""

import sys
sys.path.insert(0, '.')

from ai_saas_intelligence import MarketIntelligenceOrchestrator

print("="*70)
print("AI SAAS MARKET INTELLIGENCE PLATFORM - DEMO")
print("="*70)

orchestrator = MarketIntelligenceOrchestrator()

# Get quick recommendations
print("\n🚀 TOP 3 MARKET OPPORTUNITIES")
print("-"*70)
recommendations = orchestrator.get_quick_recommendations(3)

for i, rec in enumerate(recommendations, 1):
    print(f"\n{i}. {rec['product']}")
    print(f"   Market Fit: {rec['market_fit']}")
    print(f"   Time to Market: {rec['time_to_market']}")
    print(f"   Monetization: {rec['monetization']}")
    print(f"   Entry Strategy: {rec['entry_strategy']}")

# Get market insights
print("\n\n📊 MARKET INSIGHTS")
print("-"*70)
overview = orchestrator.generate_overview_report()
print(f"Total Trends Analyzed: {overview['executive_summary']['total_trends_analyzed']}")
print(f"High-Severity Pain Points: {overview['executive_summary']['high_severity_pain_points']}")
print(f"Product Opportunities: {overview['executive_summary']['product_opportunities']}")

# Show top trend
print("\n\n📈 TOP TREND")
print("-"*70)
trend = overview['top_market_opportunities'][0]
print(f"Trend: {trend['trend']}")
print(f"Growth Potential: {trend['growth_potential']}")
print(f"Market Size: {trend['market_size']}")
print(f"Key Technologies: {', '.join(trend['key_tech'])}")

print("\n" + "="*70)
print("✅ Demo Complete!")
print("="*70)
