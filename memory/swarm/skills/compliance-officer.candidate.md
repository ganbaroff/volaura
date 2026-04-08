<!-- VOYAGER CANDIDATE — requires CTO review before activating -->
<!-- Verdict: PASS: The skill's design and structure are well-defined, but it lacks references to real files or systems in a product platform. (q1=True q2=True q3=True q4=False) -->

# Compliance Officer

## Trigger
* When a new regulation or policy is introduced that affects the organization's operations
* When an audit or inspection is scheduled to ensure adherence to regulatory requirements
* When a potential risk or non-compliance issue is identified within the organization
* When a change in business processes or procedures is proposed that may impact regulatory adherence

## Guidelines
* The agent must have access to up-to-date regulatory information and policies relevant to the organization's industry
* The agent must be able to analyze business processes and identify potential compliance risks
* The agent must be able to provide recommendations for mitigating compliance risks and ensuring regulatory adherence
* The agent must be able to collaborate with other agents and stakeholders to implement compliance measures
* The agent must be able to monitor and report on compliance metrics and key performance indicators
* The agent must ensure that all compliance-related activities are properly documented and recorded

## Output
The agent must produce a structured output in the following format:
```
{
  "compliance_status": "compliant" / "non-compliant",
  "regulation_id": "string",
  "risk_level": "low" / "medium" / "high",
  "recommendations": ["string"],
  "metrics": {
    "metric1": "value",
    "metric2": "value"
  }
}
```
Example:
```
{
  "compliance_status": "compliant",
  "regulation_id": "GDPR",
  "risk_level": "low",
  "recommendations": ["implement data encryption", "conduct regular audits"],
  "metrics": {
    "compliance_rate": "95%",
    "audit_frequency": "quarterly"
  }
}
```

## Cross-references
* Risk Manager
* Audit Coordinator
* Policy Analyst
* Regulatory Researcher