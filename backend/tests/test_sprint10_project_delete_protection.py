import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.services.project_service import soft_delete_project


class FakeSession:
    def __init__(self, project, active_property_count):
        self.results = iter((project, active_property_count))
        self.queries = []
        self.commit_count = 0

    def scalar(self, query):
        self.queries.append(query)
        return next(self.results)

    def commit(self):
        self.commit_count += 1


class Sprint10ProjectDeleteProtectionTests(unittest.TestCase):
    def make_project(self):
        return SimpleNamespace(
            id=uuid4(),
            project_code="PRJ-000001",
            name="Dự án kiểm thử",
            deleted_at=None,
            deleted_by_id=None,
        )

    def make_actor(self):
        return SimpleNamespace(id=uuid4(), is_superuser=True)

    @patch("app.services.project_service.write_audit_log")
    def test_delete_project_with_active_property_returns_409(self, write_audit_log):
        project = self.make_project()
        db = FakeSession(project, 1)

        with self.assertRaises(HTTPException) as context:
            soft_delete_project(db, project.id, self.make_actor())

        self.assertEqual(409, context.exception.status_code)
        self.assertEqual(
            "Dự án hiện còn 1 bất động sản. Vui lòng xử lý các bất động sản trước khi xóa dự án.",
            context.exception.detail,
        )
        self.assertIsNone(project.deleted_at)
        self.assertIsNone(project.deleted_by_id)
        self.assertEqual(0, db.commit_count)
        write_audit_log.assert_not_called()
        self.assertIn("property_units.deleted_at IS NULL", str(db.queries[1]))

    @patch("app.services.project_service.write_audit_log")
    def test_delete_project_with_only_soft_deleted_properties_succeeds(self, write_audit_log):
        project = self.make_project()
        actor = self.make_actor()
        db = FakeSession(project, 0)

        soft_delete_project(db, project.id, actor)

        self.assertIsNotNone(project.deleted_at)
        self.assertEqual(actor.id, project.deleted_by_id)
        self.assertEqual(1, db.commit_count)
        write_audit_log.assert_called_once()

    @patch("app.services.project_service.write_audit_log")
    def test_delete_project_without_properties_succeeds(self, write_audit_log):
        project = self.make_project()
        actor = self.make_actor()
        db = FakeSession(project, 0)

        soft_delete_project(db, project.id, actor)

        self.assertIsNotNone(project.deleted_at)
        self.assertEqual(actor.id, project.deleted_by_id)
        self.assertEqual(1, db.commit_count)
        write_audit_log.assert_called_once()

    def test_project_delete_ui_keeps_dialog_and_displays_business_error(self):
        list_page = Path("frontend/src/features/projects/ProjectsPage.tsx").read_text()
        detail_page = Path("frontend/src/features/projects/ProjectDetailPage.tsx").read_text()
        error_helper = Path("frontend/src/features/projects/deleteError.ts").read_text()

        for source in (list_page, detail_page):
            self.assertIn("setDeleteError(formatProjectDeleteError(requestError))", source)
            self.assertIn("title={deleteError ? 'Không thể xóa dự án' : 'Xóa dự án'}", source)
            self.assertIn("error={deleteError}", source)
        self.assertIn("Vui lòng chuyển dự án hoặc xóa các bất động sản trước.", error_helper)


if __name__ == "__main__":
    unittest.main()
