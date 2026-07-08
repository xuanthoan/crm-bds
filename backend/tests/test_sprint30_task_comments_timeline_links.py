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
        for snippet in ("_user_label", "_collab_change_content", "Đã thêm: ", "Đã bỏ: ", "old=_join_labels(db", "new=_join_labels(db", "old != new"):
            self.assertIn(snippet, service)
        self.assertNotIn('old=",".join(map(str, old))', service)
        self.assertNotIn('new=",".join(map(str, new))', service)
        self.assertIn("recipients.discard(getattr(actor", service)
        self.assertIn("_can_access", service)
        self.assertIn("def get_today_tasks(db,actor,page=1,page_size=200,q=None,with_meta=False)", service)
        self.assertIn("def get_overdue_tasks(db,actor,page=1,page_size=200,q=None,with_meta=False)", service)
        self.assertIn("q=q,due_from=start_of_today,due_before=start_of_tomorrow", service)
        self.assertIn("q=q,due_before=start_of_today", service)
        self.assertIn('status in {"open","in_progress"}', service)
        self.assertIn("total_pages", service)

    def test_frontend_linkify_and_task_sections(self):
        linkified = self.f("components/common/LinkifiedText.tsx")
        panel = self.f("features/tasks/TaskCollaborationPanel.tsx")
        modal = self.f("features/tasks/TaskFormModal.tsx")
        api = self.f("features/tasks/api.ts")
        types = self.f("features/tasks/types.ts")
        service = self.b("app/services/task_service.py")
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
        for cls in ("task-collaboration-panel", "task-tabs", "task-tab-panel", "task-comment-card", "task-comment-author", "task-comment-meta", "task-comment-content", "task-link-card", "task-timeline-item", "task-timeline-actor", "task-timeline-meta", "task-timeline-description"):
            self.assertIn(cls, panel)
        self.assertIn("prettyValue", panel)
        self.assertIn("uuidLike", panel)
        self.assertNotIn("JSON.stringify", panel)
        styles = self.f("styles.css")
        for cls in (".task-tabs", ".task-comment-card", ".task-comment-author", ".task-comment-meta", ".task-comment-content", ".task-link-card", ".task-timeline-item", ".task-timeline-actor", ".task-timeline-meta", ".task-timeline-description", ".task-empty-state"):
            self.assertIn(cls, styles)
        self.assertIn("color: #3157d5", styles)
        self.assertIn("font-size: 0.92rem", styles)
        self.assertIn("font-weight: 400", styles)
        self.assertNotIn("body .task-comment", styles)
        self.assertIn("<LinkifiedText text={e.description}/>", panel)
        for label in ("Từ:", "Sang:"):
            self.assertIn(label, panel)
        for label in ("Đã thêm: ", "Đã bỏ: "):
            self.assertIn(label, service)
        self.assertIn("task.assignees_changed", panel)
        self.assertIn("task.watchers_changed", panel)
        self.assertIn(".task-timeline-description a", styles)
        self.assertIn("TaskCollaborationPanel", modal)
        layout = self.f("layouts/AppLayout.tsx")
        routes = self.f("routes/AppRoutes.tsx")
        tasks_page = self.f("features/tasks/TasksPage.tsx")
        overdue_page = self.f("features/tasks/OverdueTasksPage.tsx")
        self.assertIn("renderLink('Công việc', '/tasks')", layout)
        self.assertNotIn("renderLink('Việc hôm nay', '/tasks/today')", layout)
        self.assertNotIn("renderLink('Việc quá hạn', '/tasks/overdue')", layout)
        for route in ("'/tasks'", "'/tasks/today'", "'/tasks/overdue'"):
            self.assertIn(route, routes)
        order = [tasks_page.index("label:'Việc hôm nay'"), tasks_page.index("label:'Việc quá hạn'"), tasks_page.index("label:'Tất cả công việc'")]
        self.assertEqual(order, sorted(order))
        for path in ("path:'/tasks/today'", "path:'/tasks/overdue'", "path:'/tasks'"):
            self.assertIn(path, tasks_page)
        self.assertIn("task-view-switcher", tasks_page)
        self.assertIn("task-view-button", tasks_page)
        self.assertIn("aria-current={active?'page':undefined}", tasks_page)
        self.assertIn("today-search", tasks_page)
        self.assertIn("overdue-search", tasks_page)
        self.assertIn("Tìm mã task, tiêu đề, booking, hợp đồng...", tasks_page)
        self.assertIn("q:e.target.value,page:1", tasks_page)
        self.assertIn("Không có công việc hôm nay phù hợp.", tasks_page)
        self.assertIn("Không có công việc quá hạn phù hợp.", tasks_page)
        self.assertIn("totalItems={meta.total}", tasks_page)
        self.assertIn("Quá hạn", self.f("features/tasks/components/TaskFilters.tsx"))
        self.assertIn("today:true", self.f("features/tasks/TodayTasksPage.tsx"))
        self.assertIn("overdue:true", overdue_page)
        self.assertIn("/api/v1/tasks/today?${qs(filters)}", api)
        self.assertIn("/api/v1/tasks/overdue?${qs(filters)}", api)
        for fn in ("listTaskComments", "createTaskComment", "listTaskLinks", "createTaskLink", "listTaskTimeline"):
            self.assertIn(fn, api)
        for typ in ("TaskComment", "TaskRelatedLink", "TaskTimelineEvent"):
            self.assertIn(typ, types)
        self.assertIn("Pagination", self.f("features/tasks/TasksPage.tsx"))
        styles = self.f("styles.css")
        self.assertIn(".task-view-switcher", styles)
        self.assertIn(".task-view-button.active", styles)
        self.assertIn("today:true", self.f("features/tasks/TodayTasksPage.tsx"))
        self.assertIn("overdue:true", self.f("features/tasks/OverdueTasksPage.tsx"))
