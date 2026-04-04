#!/usr/bin/env python3
"""
aggregate_test_results.py

Merge all team test results into one comprehensive report.
Input: test_results/*.json (one file per team)
Output: test_results/AGGREGATED_REPORT.json + pretty HTML summary
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def load_results(results_dir: str) -> List[Dict[str, Any]]:
    """Load all JSON test results from directory."""
    results = []

    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"ERROR: {results_dir} directory not found", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(results_path.glob("*.json"))

    # Skip aggregated report itself
    json_files = [f for f in json_files if f.name != "AGGREGATED_REPORT.json"]

    if not json_files:
        print(f"WARNING: No test result files found in {results_dir}", file=sys.stderr)
        return results

    for json_file in json_files:
        try:
            with open(json_file) as f:
                result = json.load(f)
                results.append(result)
                print(f"✓ Loaded {json_file.name}")
        except json.JSONDecodeError as e:
            print(f"⚠ Skipping {json_file.name}: Invalid JSON ({e})", file=sys.stderr)
        except Exception as e:
            print(f"⚠ Skipping {json_file.name}: {e}", file=sys.stderr)

    return results


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge results and generate summary."""

    if not results:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "NO_DATA",
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": "N/A",
            },
            "by_team": [],
            "critical_blockers": [],
            "next_steps": ["Submit test results from team leads"]
        }

    # Count results
    total_tests = 0
    passed = 0
    failed = 0
    warnings = 0

    for team_result in results:
        for test in team_result.get("tests", []):
            total_tests += 1
            if test.get("status") == "PASS":
                passed += 1
            elif test.get("status") == "FAIL":
                failed += 1

    # Extract blockers
    blockers = []
    for team_result in results:
        team = team_result.get("team", "Unknown")
        for blocker in team_result.get("blockers", []):
            blockers.append({
                "team": team,
                "issue": blocker,
                "severity": "CRITICAL"
            })
        for warning in team_result.get("warnings", []):
            blockers.append({
                "team": team,
                "issue": warning,
                "severity": "WARNING"
            })

    # Calculate pass rate
    pass_rate = f"{100*passed/total_tests:.1f}%" if total_tests > 0 else "N/A"

    # Determine overall status
    overall_status = "PASS" if failed == 0 else "FAIL"

    # Next steps
    next_steps = []
    if failed == 0:
        next_steps.append("✓ All tests passed!")
        next_steps.append("→ Proceed to manual walkthrough")
    else:
        next_steps.append(f"⚠ Fix {failed} failing tests")
        next_steps.append("→ Estimated fix time: 2-3 hours (batch fixes)")
        next_steps.append("→ Re-run affected tests")
        next_steps.append("→ Confirm fixes before manual walkthrough")

    # Build report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": overall_status,
        "summary": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "teams_reporting": len(results),
        },
        "by_team": results,
        "critical_blockers": blockers,
        "next_steps": next_steps,
        "failure_details": extract_failures(results),
    }

    return report


def extract_failures(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract detailed failure information for triage."""
    failures = []

    for team_result in results:
        team = team_result.get("team", "Unknown")
        for test in team_result.get("tests", []):
            if test.get("status") == "FAIL":
                failures.append({
                    "team": team,
                    "test_name": test.get("name", "Unknown"),
                    "endpoint": test.get("endpoint", "N/A"),
                    "expected": test.get("expected", "N/A"),
                    "actual": test.get("actual", "N/A"),
                    "root_cause": test.get("root_cause", "Unknown"),
                    "timestamp": test.get("timestamp", "N/A"),
                })

    return failures


def generate_html_report(report: Dict[str, Any], output_path: str):
    """Generate pretty HTML summary for easy viewing."""

    summary = report["summary"]
    blockers = report["critical_blockers"]
    failures = report["failure_details"]

    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>VOLAURA Functional Test Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-top: 0;
        }}
        h2 {{
            color: #555;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .status-pass {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-fail {{
            color: #dc3545;
            font-weight: bold;
        }}
        .metric {{
            display: inline-block;
            margin-right: 30px;
            margin-bottom: 20px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .metric-label {{
            color: #999;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .blocker {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .blocker.critical {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f9f9f9;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .status-icon {{
            font-size: 16px;
            margin-right: 5px;
        }}
        .next-steps {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .timestamp {{
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>VOLAURA Functional Test Report</h1>
        <p class="timestamp">Generated: {report['timestamp']}</p>

        <div style="margin: 30px 0;">
            <div class="metric">
                <div class="metric-label">Overall Status</div>
                <div class="metric-value status-{'pass' if report['overall_status'] == 'PASS' else 'fail'}">
                    {report['overall_status']}
                </div>
            </div>

            <div class="metric">
                <div class="metric-label">Total Tests</div>
                <div class="metric-value">{summary['total_tests']}</div>
            </div>

            <div class="metric">
                <div class="metric-label">Passed</div>
                <div class="metric-value" style="color: #28a745;">{summary['passed']}</div>
            </div>

            <div class="metric">
                <div class="metric-label">Failed</div>
                <div class="metric-value" style="color: #dc3545;">{summary['failed']}</div>
            </div>

            <div class="metric">
                <div class="metric-label">Pass Rate</div>
                <div class="metric-value">{summary['pass_rate']}</div>
            </div>
        </div>

        <h2>Next Steps</h2>
        <div class="next-steps">
            {''.join(f'<p>✓ {step}</p>' if '✓' in step else f'<p>{step}</p>' for step in report['next_steps'])}
        </div>

        {f'''
        <h2>Critical Issues ({len(blockers)})</h2>
        {''.join(
            f'<div class="blocker {blocker["severity"].lower()}">'
            f'<strong>{blocker["team"]}</strong>: {blocker["issue"]}'
            f'</div>'
            for blocker in blockers
        ) if blockers else '<p style="color: #999;">No critical issues</p>'}
        ''' if blockers else ''}

        {f'''
        <h2>Failure Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Team</th>
                    <th>Test Name</th>
                    <th>Endpoint</th>
                    <th>Root Cause</th>
                </tr>
            </thead>
            <tbody>
                {''.join(
                    f'<tr>'
                    f'<td>{f["team"]}</td>'
                    f'<td>{f["test_name"]}</td>'
                    f'<td><code>{f["endpoint"]}</code></td>'
                    f'<td>{f["root_cause"]}</td>'
                    f'</tr>'
                    for f in failures
                )}
            </tbody>
        </table>
        ''' if failures else ''}

        <h2>Teams Reporting</h2>
        <p>{summary['teams_reporting']} team(s) submitted results</p>
    </div>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✓ HTML report saved: {output_path}")


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else "test_results"

    print(f"Loading results from {results_dir}...")
    results = load_results(results_dir)

    print("\nAggregating results...")
    report = aggregate(results)

    # Save JSON report
    output_json = Path(results_dir) / "AGGREGATED_REPORT.json"
    with open(output_json, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✓ JSON report saved: {output_json}")

    # Generate HTML report
    output_html = Path(results_dir) / "AGGREGATED_REPORT.html"
    generate_html_report(report, str(output_html))

    # Print summary to console
    print("\n" + "=" * 60)
    print(f"OVERALL STATUS: {report['overall_status']}")
    print("=" * 60)
    print(f"\nTests: {report['summary']['passed']}/{report['summary']['total_tests']} passed ({report['summary']['pass_rate']})")

    if report['critical_blockers']:
        print(f"\n⚠ Critical Issues ({len(report['critical_blockers'])}):")
        for blocker in report['critical_blockers'][:5]:  # Show first 5
            print(f"  • {blocker['team']}: {blocker['issue']}")
        if len(report['critical_blockers']) > 5:
            print(f"  ... and {len(report['critical_blockers']) - 5} more")

    print(f"\nNext steps:")
    for step in report['next_steps']:
        print(f"  {step}")

    print("\n" + "=" * 60)
    print(f"See {output_html.name} for full report")
    print("=" * 60 + "\n")

    # Exit with failure if any tests failed
    sys.exit(0 if report['overall_status'] == 'PASS' else 1)


if __name__ == "__main__":
    main()
