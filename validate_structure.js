// Simple validation script for AI SaaS Intelligence Platform structure

const fs = require('fs');
const path = require('path');

console.log('Validating AI SaaS Intelligence Platform Structure...');
console.log('====================================================\n');

const requiredFiles = [
    'main.py',
    'ai_saas_intelligence/__init__.py',
    'ai_saas_intelligence/core/models.py',
    'ai_saas_intelligence/core/orchestrator.py',
    'ai_saas_intelligence/analyzers/trend_analyzer.py',
    'ai_saas_intelligence/analyzers/pain_point_analyzer.py',
    'ai_saas_intelligence/analyzers/competitor_analyzer.py',
    'ai_saas_intelligence/generators/product_idea_generator.py',
    'ai_saas_intelligence/strategies/gtm_strategy.py',
];

let errors = 0;
let warnings = 0;

requiredFiles.forEach(file => {
    const fullPath = path.join(__dirname, file);
    if (fs.existsSync(fullPath)) {
        const content = fs.readFileSync(fullPath, 'utf8');
        const lineCount = content.split('\n').length;
        console.log(`✓ ${file} (${lineCount} lines)`);
    } else {
        console.log(`✗ ${file} - NOT FOUND`);
        errors++;
    }
});

console.log('\n====================================================');
console.log(`Validation complete: ${requiredFiles.length - errors} files present, ${errors} errors`);

if (errors === 0) {
    console.log('\n✅ All required files present!');
} else {
    console.log('\n❌ Some files are missing!');
    process.exit(1);
}
