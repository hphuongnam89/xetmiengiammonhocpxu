"""Single-process local analysis queue; external inference never holds a DB transaction."""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from django.db import close_old_connections, transaction
from django.utils import timezone

from reviews.models import AnalysisJob
from .ai_preliminary import PreliminaryRecommendationError, create_preliminary_recommendation

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dossier-analysis")
_start_lock = Lock()
_worker_token = str(uuid.uuid4())
ACTIVE = ("PENDING", "RUNNING")


def recover_interrupted(submission):
    AnalysisJob.objects.filter(submission=submission, status__in=ACTIVE).exclude(
        worker_token=_worker_token,
    ).update(status="FAILED", stage="INTERRUPTED", updated_at=timezone.now(),
             message="Lượt phân tích bị gián đoạn khi máy chủ khởi động lại. Bấm phân tích để thử lại.")


def start_analysis(submission, actor):
    with _start_lock:
        recover_interrupted(submission)
        existing = AnalysisJob.objects.filter(submission=submission, status__in=ACTIVE).first()
        if existing:
            return existing
        job = AnalysisJob.objects.create(submission=submission, requested_by=actor,
            worker_token=_worker_token, message="Đã nhận yêu cầu. Đang chờ đến lượt phân tích…")
        transaction.on_commit(lambda: _executor.submit(_run_job, job.id))
        return job


def _update(job_id, **values):
    AnalysisJob.objects.filter(pk=job_id).update(updated_at=timezone.now(), **values)


def _run_job(job_id):
    close_old_connections()
    try:
        job = AnalysisJob.objects.select_related("submission__student", "requested_by").get(pk=job_id)
        _update(job_id, status="RUNNING")
        result = create_preliminary_recommendation(submission=job.submission, actor=job.requested_by,
            progress=lambda stage, message: _update(job_id, stage=stage, message=message))
        _update(job_id, status="SUCCEEDED", stage="DONE", result_id=result.id,
            message=f"Đã tạo {result.items.count()} đề xuất sơ bộ. Giảng viên sẽ kiểm tra và quyết định cuối.")
    except PreliminaryRecommendationError as exc:
        logger.warning("Analysis %s failed: %s", job_id, exc)
        _update(job_id, status="FAILED", stage="ERROR", message=str(exc))
    except Exception:
        logger.exception("Unexpected analysis failure %s", job_id)
        _update(job_id, status="FAILED", stage="ERROR",
            message="Phân tích gặp lỗi xử lý. Nội dung OCR đã đọc được vẫn được giữ; bấm thử lại.")
    finally:
        close_old_connections()


def job_state(job):
    return {"id": str(job.id), "status": job.status, "stage": job.stage, "message": job.message,
            "created_at": job.created_at.isoformat(), "updated_at": job.updated_at.isoformat(),
            "result_id": str(job.result_id) if job.result_id else None}
