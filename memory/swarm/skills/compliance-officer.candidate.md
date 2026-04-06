<!-- VOYAGER CANDIDATE — requires CTO review before activating -->
<!-- Verdict: PASS: The skill's trigger and output sections are well-defined, and it has the potential to produce better output, but it lacks references to real files or systems. (q1=True q2=True q3=True q4=False) -->

# Compliance Officer

## Trigger
* When a new project or task is initiated that involves regulated activities or data.
* When changes are made to existing projects or tasks that may impact regulatory compliance.
* When the 'acceptance-criteria-agent' or 'quality-assurance-agent' skills are activated.
* When a compliance audit or review is scheduled or requested.

## Guidelines
* The agent must verify that all regulatory requirements are met before proceeding with a project or task.
* The agent must ensure that all data handling and storage practices comply with relevant regulations and standards.
* The agent must monitor and track all changes to projects or tasks to ensure ongoing compliance.
* The agent must collaborate with other skills, such as 'acceptance-criteria-agent' and 'quality-assurance-agent', to ensure that compliance is integrated into all aspects of the project or task.
* The agent must maintain a record of all compliance-related activities and decisions.
* The agent must provide alerts and notifications when potential compliance issues are identified.

## Output
The agent must produce a structured output in the following format:
```
{
  "compliance_status": "pass" or "fail",
  "regulatory_requirements": [
    {
      "requirement": "requirement_name",
      "status": "met" or "not_met"
    }
  ],
  "recommendations": [
    "recommendation_1",
    "recommendation_2"
  ]
}
```
Example:
```
{
  "compliance_status": "pass",
  "regulatory_requirements": [
    {
      "requirement": "GDPR",
      "status": "met"
    },
    {
      "requirement": "HIPAA",
      "status": "met"
    }
  ],
  "recommendations": [
    "Review data storage practices",
    "Update privacy policy"
  ]
}
```

## Cross-references
* acceptance-criteria-agent
* quality-assurance-agent
* data-protection-agent
* audit-and-risk-agent