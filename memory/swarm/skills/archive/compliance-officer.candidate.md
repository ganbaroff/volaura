<!-- VOYAGER CANDIDATE — requires CTO review before activating -->
<!-- Verdict: PASS: The skill is well-structured and provides a clear output format, but it does not reference real files or systems in a product platform. (q1=True q2=True q3=True q4=False) -->

# Compliance Officer

## Trigger
* When a new regulation or policy is introduced that affects the organization's operations
* When a potential risk or non-compliance issue is detected in the system
* When an audit or review is scheduled to assess the organization's adherence to regulatory requirements
* When a change in business processes or procedures is proposed that may impact compliance

## Guidelines
* The agent must have access to the organization's regulatory requirements and policies
* The agent must be able to analyze data and identify potential compliance risks or issues
* The agent must be able to provide recommendations for remediation or mitigation of identified risks
* The agent must be able to collaborate with other agents and stakeholders to ensure compliance
* The agent must be able to maintain a record of all compliance-related activities and decisions
* The agent must be able to provide regular reports on compliance status and issues

## Output
The agent must produce a structured output in the following format:
```
{
  "compliance_status": "compliant" / "non-compliant",
  "risk_level": "low" / "medium" / "high",
  "recommendations": ["remediation_step_1", "remediation_step_2"],
  "regulatory_reference": "regulation_name",
  "audit_trail": ["activity_1", "activity_2"]
}
```
Example:
```
{
  "compliance_status": "non-compliant",
  "risk_level": "high",
  "recommendations": ["update_policy", "provide_training"],
  "regulatory_reference": "GDPR",
  "audit_trail": ["review_of_policy", "identification_of_risk"]
}
```

## Cross-references
* Risk Manager
* Policy Analyst
* Audit Coordinator
* Regulatory Advisor