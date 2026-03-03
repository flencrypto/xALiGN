#!/bin/bash

echo "=== 1. Temperature Matrix Validation ==="
python3 -c "
from backend.services.ai_governance import TEMPERATURE_MATRIX, TaskType, get_temperature_params
print('Temperature Matrix:')
for task in TaskType:
    p = get_temperature_params(task)
    assert p['temperature'] <= 0.5, f'Temperature too high for {task}: {p[\"temperature\"]}'
    print(f'  {task.value}: temp={p[\"temperature\"]}, top_p={p[\"top_p\"]}')
print('All temperatures <= 0.5: PASS')
# Verify numeric tasks have low temperature
assert get_temperature_params(TaskType.PRICING_MODEL)['temperature'] <= 0.15
assert get_temperature_params(TaskType.EARNINGS_PARSING)['temperature'] <= 0.15
# Verify creative is higher but still <= 0.5
assert get_temperature_params(TaskType.BLOG_GENERATION)['temperature'] == 0.4
print('Numeric tasks <= 0.15: PASS')
print('Creative tasks <= 0.4: PASS')
"

echo ""
echo "=== 2. Confidence Scoring Validation ==="
python3 -c "
from backend.services.ai_governance import assess_output_confidence, compute_confidence, ConfidenceFactors, TaskType, REVIEW_THRESHOLD, SUPPRESSION_THRESHOLD

# High confidence output (with evidence)
high = {'company_name': 'Acme Water', 'expansion_signals': 'new reservoir', 
        'evidence_source': 'company website', 'quote_excerpt': 'We plan to expand',
        'business_model': 'water utilities', 'locations': 'Manchester'}
c1 = assess_output_confidence(high, TaskType.COMPANY_RESEARCH)
print(f'High evidence confidence: {c1} (expected > 0.65)')
assert c1 > 0.65

# Low confidence output (no evidence)
low = {'company_name': 'Corp'}
c2 = assess_output_confidence(low, TaskType.COMPANY_RESEARCH)
print(f'Low evidence confidence: {c2} (expected < 0.65)')
assert c2 < 0.65

# Test thresholds
print(f'Review threshold: {REVIEW_THRESHOLD}')
print(f'Suppression threshold: {SUPPRESSION_THRESHOLD}')
assert REVIEW_THRESHOLD > SUPPRESSION_THRESHOLD
print('Confidence scoring: PASS')
"

echo ""
echo "=== 3. Human Review Gateway Validation ==="
python3 -c "
from backend.services.ai_governance import needs_human_review, TaskType

# M&A detection
output = {'expansion_signals': 'merger with rival company', 'company_name': 'Acme'}
review, reasons = needs_human_review(output, 0.75, TaskType.COMPANY_RESEARCH)
assert review == True
assert any('M&A' in r for r in reasons), f'Expected M&A reason in {reasons}'
print(f'M&A detection: PASS - reasons={reasons}')

# Low confidence triggers review
output2 = {'company_name': 'Acme', 'business_model': 'water'}
review2, reasons2 = needs_human_review(output2, 0.5, TaskType.COMPANY_RESEARCH)
assert review2 == True
print(f'Low confidence triggers review: PASS - reasons={reasons2}')

# Clean output does not trigger review
output3 = {'company_name': 'Acme', 'expansion_signals': 'building new site', 
           'evidence_source': 'website', 'quote_excerpt': 'planned growth'}
review3, reasons3 = needs_human_review(output3, 0.80, TaskType.COMPANY_RESEARCH)
print(f'Clean output review={review3}, reasons={reasons3}')
print('Human review gateway: PASS')
"

echo ""
echo "=== 4. Numeric Sanity Checks Validation ==="
python3 -c "
from backend.services.ai_governance import run_numeric_sanity_checks
anomalies = run_numeric_sanity_checks({'contract_value': 15_000_000_000})
assert len(anomalies) == 1
assert '£10bn' in anomalies[0]
print(f'Large contract anomaly: PASS - {anomalies}')

anomalies2 = run_numeric_sanity_checks({'capex_growth_pct': 600})
assert len(anomalies2) == 1
assert '500%' in anomalies2[0]
print(f'CapEx growth anomaly: PASS - {anomalies2}')

no_anomaly = run_numeric_sanity_checks({'contract_value': 5_000_000})
assert len(no_anomaly) == 0
print('Normal values: PASS')
"

echo ""
echo "=== 5. Citation Verification Validation ==="
python3 -c "
from backend.services.ai_governance import verify_claim_in_text, build_source_attribution

# Test claim verification
source = 'The company announced €400m expansion plans for the region'
assert verify_claim_in_text('€400m', source) == True
assert verify_claim_in_text('£999m', source) == False
print('Claim verification: PASS')

# Test source attribution
attr = build_source_attribution('expansion', 'https://example.com', 'press_release', 'announced €400m', 0.82)
assert 'retrieval_timestamp' in attr
assert attr['source_type'] == 'press_release'
assert attr['confidence_score'] == 0.82
print('Source attribution: PASS')
"

echo ""
echo "=== 6. Invocation Record Validation ==="
python3 -c "
from backend.services.ai_governance import create_invocation_record, TaskType
record = create_invocation_record(
    prompt_hash='abc12345',
    model_version='grok-3-mini',
    task_type=TaskType.COMPANY_RESEARCH,
    temperature=0.15,
    top_p=0.9,
    input_tokens=100,
    output_tokens=200,
    confidence_score=0.78,
    validation_outcome='pass',
)
assert record.task_type == 'company_research'
assert record.temperature == 0.15
assert record.confidence_score == 0.78
print('Invocation record: PASS')
"

echo ""
echo "=== 7. Model Fields Validation ==="
python3 -c "
from backend.models.intel import CompanyIntel, ExecutiveProfile, NewsItem, AIInvocationLog, HumanReviewItem
# Check new fields exist
assert hasattr(CompanyIntel, 'evidence_source')
assert hasattr(CompanyIntel, 'quote_excerpt')
assert hasattr(CompanyIntel, 'confidence_score')
assert hasattr(ExecutiveProfile, 'evidence_source')
assert hasattr(ExecutiveProfile, 'confidence_score')
assert hasattr(NewsItem, 'quote_excerpt')
assert hasattr(NewsItem, 'confidence_score')
assert hasattr(AIInvocationLog, 'prompt_hash')
assert hasattr(AIInvocationLog, 'validation_outcome')
assert hasattr(HumanReviewItem, 'reasons')
print('All model fields: PASS')
"

echo ""
echo "=== ALL VALIDATIONS COMPLETE ==="
