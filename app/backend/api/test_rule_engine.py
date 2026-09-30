from decimal import Decimal

from django.test import SimpleTestCase

from .rule_engine import evaluate_course


class RuleEngineTests(SimpleTestCase):
    def test_missing_evidence_never_auto_accepts(self):
        decision = evaluate_course(
            course_code="LAW101",
            rule_approved=True,
            prior_grade=8,
            prior_credits=3,
            content_match=None,
            evidence=[],
        )
        self.assertEqual(decision.recommendation, "NEEDS_HUMAN_REVIEW")
        self.assertTrue(decision.needs_human_review)

    def test_approved_matching_course_is_full(self):
        decision = evaluate_course(
            course_code="ACC101",
            rule_approved=True,
            prior_grade="8.5",
            prior_credits=3,
            content_match=True,
            evidence=["transcript:p1", "curriculum:ACC101"],
        )
        self.assertEqual(decision.recommendation, "FULL")
        self.assertEqual(decision.confidence, Decimal("0.95"))

    def test_unapproved_rule_is_blocked(self):
        decision = evaluate_course(
            course_code="ACC101",
            rule_approved=False,
            prior_grade=9,
            prior_credits=3,
            content_match=True,
            evidence=["transcript:p1"],
        )
        self.assertEqual(decision.recommendation, "NEEDS_HUMAN_REVIEW")
