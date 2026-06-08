import re
import unittest
from types import SimpleNamespace
from uuid import UUID

from app.services.lead_activity_service import serialize_activity

UUID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)


class FakeSession:
    def __init__(self, users):
        self.users = iter(users)

    def scalar(self, _query):
        return next(self.users, None)


class LeadAssignmentTimelineTests(unittest.TestCase):
    def test_legacy_owner_uuids_are_rendered_as_names(self):
        old_owner_id = UUID("8d1f2d1c-df49-46c5-b87a-81628cd11606")
        new_owner_id = UUID("394a89a0-c8c4-4704-b932-f9efcd1b0028")
        actor = SimpleNamespace(id=old_owner_id, full_name="System Admin", email="admin@example.com")
        activity = SimpleNamespace(
            id=UUID("11111111-1111-4111-8111-111111111111"),
            activity_type="assignment",
            title="Chuyển lead",
            content="Phân công lead cho Sale 04",
            old_value=str(old_owner_id),
            new_value=str(new_owner_id),
            user=actor,
            created_at=None,
        )
        db = FakeSession([
            SimpleNamespace(full_name="System Admin"),
            SimpleNamespace(full_name="Sale 04"),
        ])

        result = serialize_activity(activity, db)
        timeline_text = f"{result['old_owner_name']} → {result['new_owner_name']}"

        self.assertEqual("System Admin", result["old_owner_name"])
        self.assertEqual("Sale 04", result["new_owner_name"])
        self.assertEqual("System Admin", result["old_value"])
        self.assertEqual("Sale 04", result["new_value"])
        self.assertEqual("System Admin → Sale 04", timeline_text)
        self.assertIsNone(UUID_PATTERN.search(timeline_text))

    def test_deleted_legacy_owner_falls_back_without_uuid(self):
        activity = SimpleNamespace(
            id=UUID("11111111-1111-4111-8111-111111111111"),
            activity_type="assignment",
            title="Chuyển lead",
            content="Chuyển người phụ trách",
            old_value="8d1f2d1c-df49-46c5-b87a-81628cd11606",
            new_value="Sale 04",
            user=SimpleNamespace(id=UUID("22222222-2222-4222-8222-222222222222"), full_name="System Admin", email="admin@example.com"),
            created_at=None,
        )

        result = serialize_activity(activity, FakeSession([None]))

        self.assertEqual("Người dùng không còn tồn tại", result["old_owner_name"])
        self.assertIsNone(UUID_PATTERN.search(result["old_value"]))


if __name__ == "__main__":
    unittest.main()
