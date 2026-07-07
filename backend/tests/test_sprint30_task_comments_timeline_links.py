from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend" / "src"

class Sprint30TaskCommentsTimelineLinksSourceTests(unittest.TestCase):
    def b(self, rel): return (BACKEND / rel).read_text(encoding="utf-8")
    def f(self, rel): return (FRONTEND / rel).read_text(encoding="utf-8")

    def test_migration_and_models(self):
        migration = self.b("alembic/versions/20260707_0021_task_comments_timeline_links.py")
        model = self.b("app/models/task_collaboration.py")
        activity = self.b("app/models/task_activity.py")
        for source in (migration, model):
            for name in ("task_comments", "task_related_links", "task_id", "users.id", "ondelete=\"CASCADE\""):
                self.assertIn(name, source)
        self.assertIn("idx_task_comments_task_id_created_at", migration)
        self.assertIn("idx_task_related_links_task_id_created_at", migration)
        self.assertIn("TaskActivity", activity)

    def test_comment_link_timeline_api_and_service(self):
        api = self.b("app/api/v1/tasks.py")
        schema = self.b("app/schemas/task.py")
        service = self.b("app/services/task_service.py")
        for route in ('/{task_id}/comments', '/{task_id}/links', '/{task_id}/timeline'):
            self.assertIn(route, api)
        for fn in ("list_task_comments", "create_task_comment", "list_task_links", "create_task_link", "delete_task_link", "list_task_timeline"):
            self.assertIn(f"def {fn}", service)
        self.assertIn("max_length=5000", schema)
        self.assertIn('startswith("http://") or value.startswith("https://")', schema)
        for bad in ("javascript:", "data:", "file:", "vbscript:"):
            self.assertNotIn(f"startswith(\"{bad}\")", schema)
        for event_type in ("comment_added", "link_added", "link_deleted", "status_changed", "due_date_changed", "primary_assignee_changed", "assignees_changed", "watchers_changed"):
            self.assertIn(event_type, service)
        self.assertIn("recipients.discard(getattr(actor", service)
        self.assertIn("_can_access", service)

    def test_frontend_linkify_and_task_sections(self):
        linkified = self.f("components/common/LinkifiedText.tsx")
        panel = self.f("features/tasks/TaskCollaborationPanel.tsx")
        modal = self.f("features/tasks/TaskFormModal.tsx")
        api = self.f("features/tasks/api.ts")
        types = self.f("features/tasks/types.ts")
        self.assertNotIn("dangerouslySetInnerHTML", linkified + panel)
        self.assertIn('target="_blank"', linkified)
        self.assertIn('rel="noopener noreferrer"', linkified)
        self.assertIn("https?:", linkified)
        self.assertIn("Nhập bình luận hoặc dán link tài liệu...", panel)
        for label in ("Bình luận", "Link liên quan", "Dòng thời gian"):
            self.assertIn(label, panel)
        self.assertNotIn('type="file"', panel)
        self.assertIn("startsWith('http://')||v.startsWith('https://')", panel)
        self.assertIn("Array.isArray", panel)
        self.assertNotRegex(panel, r"undefined\.map")
        self.assertIn("TaskCollaborationPanel", modal)
        for fn in ("listTaskComments", "createTaskComment", "listTaskLinks", "createTaskLink", "listTaskTimeline"):
            self.assertIn(fn, api)
        for typ in ("TaskComment", "TaskRelatedLink", "TaskTimelineEvent"):
            self.assertIn(typ, types)
        self.assertIn("Pagination", self.f("features/tasks/TasksPage.tsx"))
        self.assertIn("today:true", self.f("features/tasks/TodayTasksPage.tsx"))
        self.assertIn("overdue:true", self.f("features/tasks/OverdueTasksPage.tsx"))
