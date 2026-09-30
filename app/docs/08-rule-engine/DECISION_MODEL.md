# Decision model

Input tối thiểu: `approved_rule_version`, course evidence, prior course evidence, grade, credits và certificate validity.

Output:

```json
{
  "course_code": "...",
  "recommendation": "FULL|PARTIAL|NOT_ELIGIBLE|NEEDS_HUMAN_REVIEW",
  "evidence": [],
  "reason": "...",
  "confidence": 0.0,
  "needs_human_review": true
}
```

