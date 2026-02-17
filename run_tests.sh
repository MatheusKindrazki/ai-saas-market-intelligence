#!/bin/bash
# Test runner for AI SaaS Market Intelligence Platform

echo "Running AI SaaS Market Intelligence Platform Tests"
echo "=================================================="
echo ""

# Check if python is available
if command -v python3 &> /dev/null; then
    echo "Python3 found. Running tests..."
    python3 -m pip install pytest -q 2>/dev/null || echo "Note: pytest installation skipped"
    
    # Run basic import test
    echo ""
    echo "Running import tests..."
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from ai_saas_intelligence import (
        TrendAnalyzer, PainPointAnalyzer, ProductIdeaGenerator,
        CompetitorAnalyzer, GTMStrategyGenerator
    )
    print('✓ All imports successful')
    
    # Test basic functionality
    ta = TrendAnalyzer()
    print(f'✓ TrendAnalyzer initialized with {len(ta.get_all_trends())} trends')
    
    pa = PainPointAnalyzer()
    print(f'✓ PainPointAnalyzer initialized with {len(pa.pain_points_db)} pain points')
    
    ig = ProductIdeaGenerator()
    print(f'✓ ProductIdeaGenerator initialized with {len(ig.generate_all_ideas())} ideas')
    
    from ai_saas_intelligence.core.orchestrator import MarketIntelligenceOrchestrator
    mo = MarketIntelligenceOrchestrator()
    report = mo._generate_overview_report()
    print('✓ MarketIntelligenceOrchestrator generates reports')
    
    print('\\n✅ All basic tests passed!')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
    
    # Run pytest if available
    if command -v pytest &> /dev/null || python3 -m pytest --version &> /dev/null 2>&1; then
        echo ""
        echo "Running pytest suite..."
        python3 -m pytest ai_saas_intelligence/tests/ -v --tb=short || echo "Some tests failed"
    fi
    
else
    echo "Python3 not found. Tests skipped."
    echo "To run tests, ensure Python3 is installed."
fi
