#!/usr/bin/env bash
set -uo pipefail

LOG_FILE="quality_gate_error.log"
> "$LOG_FILE"

fail() {
  echo "=== FAILED STEP: $1 ===" >> "$LOG_FILE"
  cat "$2" >> "$LOG_FILE" 2>/dev/null
  echo "--- Quality gate failed at: $1 ---"
  cat "$LOG_FILE"
  exit 1
}

echo "--- terraform validate ---"
if ! terraform validate -no-color > validate_output.txt 2>&1; then
  fail "terraform validate" validate_output.txt
fi

echo "--- tflint ---"
tflint --init > /dev/null 2>&1 || true
if ! tflint --format compact --no-color > tflint_output.txt 2>&1; then
  tflint --format json > tflint_results.json 2>/dev/null || echo "[]" > tflint_results.json
  fail "tflint" tflint_output.txt
fi
tflint --format json > tflint_results.json 2>/dev/null || echo "[]" > tflint_results.json

echo "--- tfsec scan ---"
if ! tfsec . --minimum-severity=HIGH > tfsec_output.txt 2>&1; then
  tfsec . --format json --out tfsec_results.json > /dev/null 2>&1 || true
  fail "tfsec" tfsec_output.txt
fi
tfsec . --format json --out tfsec_results.json > /dev/null 2>&1 || true

echo "--- trivy config scan ---"
trivy config . --severity CRITICAL,HIGH --format json --output trivy_results.json --exit-code 0 > /dev/null 2>&1 || true
trivy config . --severity CRITICAL,HIGH --format table --exit-code 0 > trivy_results.txt 2>&1 || true
CRIT_COUNT=$(jq '[.Results[]?.Misconfigurations[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH")] | length' trivy_results.json 2>/dev/null || echo 0)
if [[ "$CRIT_COUNT" -gt 0 ]]; then
  fail "trivy (CRITICAL/HIGH findings: $CRIT_COUNT)" trivy_results.txt
fi

echo "--- terraform plan ---"
# Yahan maine flag wali error ke liye -var arguments add kiye hain
if ! terraform plan -var="resource_group_name=myResourceGroup" -var="location=eastus" -input=false -out=tfplan -no-color > plan_run_output.txt 2>&1; then
  fail "terraform plan" plan_run_output.txt
fi
terraform show -no-color tfplan > plan_output.txt
terraform show -json tfplan > plan.json

echo "Quality gate passed."
exit 0