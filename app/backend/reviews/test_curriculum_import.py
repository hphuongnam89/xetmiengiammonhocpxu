import json
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase
from openpyxl import Workbook

from .models import Course, CurriculumVersion, CurriculumVersionStatus


class CurriculumImportTests(TestCase):
    def test_import_preserves_source_headers_and_is_idempotent(self):
        with TemporaryDirectory() as directory:
            workbook_path = Path(directory) / "curriculum.xlsx"
            config_path = Path(directory) / "manifest.json"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Khung"
            sheet.append(["Mã HP", "Tên học phần", "Số tín chỉ", "Số tín chỉ"])
            sheet.append(["DEMO101", "Học phần mẫu", 99, 3])
            sheet.append(["DEMO102", "Học phần chưa rõ tín chỉ", 99, "=1+2"])
            workbook.save(workbook_path)
            workbook.close()
            config_path.write_text(json.dumps({
                "program_code": "TEST",
                "program_name": "Chương trình kiểm thử",
                "sheet": "Khung",
                "version_label": "Test v1",
                "header_row": 1,
                "headers": {
                    "course_code": "Mã HP",
                    "course_name": 2,
                    "credits": {"header": "Số tín chỉ", "occurrence": 2},
                },
            }), encoding="utf-8")
            options = {"workbook": str(workbook_path), "config": str(config_path), "stdout": StringIO()}

            call_command("import_curriculum", dry_run=True, **options)
            self.assertEqual(CurriculumVersion.objects.count(), 0)
            call_command("import_curriculum", **options)
            call_command("import_curriculum", **options)

        curriculum = CurriculumVersion.objects.get()
        self.assertEqual(curriculum.status, CurriculumVersionStatus.DRAFT)
        self.assertEqual(Course.objects.count(), 2)
        course = Course.objects.get(raw_code="DEMO101")
        self.assertEqual(course.source_row, 2)
        self.assertEqual(course.credits, Decimal("3"))
        self.assertEqual(course.source_cells["course_name"], {
            "cell": "B2", "header": "Tên học phần", "raw_value": "Học phần mẫu",
        })
        self.assertEqual(course.source_cells["credits"], {
            "cell": "D2", "header": "Số tín chỉ", "raw_value": "3",
        })
        unresolved = Course.objects.get(raw_code="DEMO102")
        self.assertIsNone(unresolved.credits)
        self.assertEqual(unresolved.source_cells["credits"]["raw_value"], "=1+2")
