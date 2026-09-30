from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CourseDecision:
    course_code: str
    recommendation: str
    evidence: tuple[str, ...]
    reason: str
    confidence: Decimal
    needs_human_review: bool


def evaluate_course(*, course_code, rule_approved, prior_grade, prior_credits, content_match, evidence):
    """Evaluate only explicit evidence; never infer missing academic mappings."""
    evidence = tuple(evidence or ())
    if not rule_approved:
        return CourseDecision(course_code, "NEEDS_HUMAN_REVIEW", evidence, "Rule version is not approved.", Decimal("0"), True)
    if not evidence or prior_grade is None or prior_credits is None or content_match is None:
        return CourseDecision(course_code, "NEEDS_HUMAN_REVIEW", evidence, "Required evidence is missing.", Decimal("0"), True)
    try:
        grade = Decimal(str(prior_grade))
        credits = Decimal(str(prior_credits))
    except Exception:
        return CourseDecision(course_code, "NEEDS_HUMAN_REVIEW", evidence, "Grade or credits are invalid.", Decimal("0"), True)
    if grade < Decimal("5") or credits <= 0:
        return CourseDecision(course_code, "NOT_ELIGIBLE", evidence, "Grade or credit threshold is not met.", Decimal("0.95"), False)
    if content_match is True:
        return CourseDecision(course_code, "FULL", evidence, "Grade, credits and content evidence meet the deterministic checks.", Decimal("0.95"), False)
    return CourseDecision(course_code, "PARTIAL", evidence, "Prior learning does not fully match the current course.", Decimal("0.80"), True)
