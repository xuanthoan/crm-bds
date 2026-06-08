import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import ast
from pathlib import Path

source = Path("backend/app/services/customer_service.py").read_text()
tree = ast.parse(source)
function_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "calculate_customer_score")
module = ast.Module(body=[function_node], type_ignores=[])
namespace = {"datetime": datetime, "timezone": timezone, "Customer": object, "Decimal": Decimal}
exec(compile(ast.fix_missing_locations(module), "customer_service.py", "exec"), namespace)
calculate_customer_score = namespace["calculate_customer_score"]


def customer(**values):
    defaults = dict(buying_timeline="unknown", financial_rating="unknown", expected_budget=None, available_cash=None, monthly_income=None, last_contact_at=None, next_follow_up_at=None)
    defaults.update(values)
    return SimpleNamespace(**defaults)


class Sprint9CustomerScoringTests(unittest.TestCase):
    def test_hot_customer_score(self):
        score, label, note = calculate_customer_score(customer(
            buying_timeline="immediate", financial_rating="A",
            expected_budget=Decimal("1000000000"), available_cash=Decimal("300000000"),
            monthly_income=Decimal("50000000"), last_contact_at=datetime.now(timezone.utc) - timedelta(days=2),
            next_follow_up_at=datetime.now(timezone.utc) + timedelta(days=1),
        ))
        self.assertEqual(105, score)
        self.assertEqual("hot", label)
        self.assertIn("Timeline +30", note)

    def test_low_quality_customer_score(self):
        score, label, note = calculate_customer_score(customer())
        self.assertEqual(0, score)
        self.assertEqual("unqualified", label)
        self.assertEqual("Chưa có tiêu chí cộng điểm", note)

    def test_threshold_labels(self):
        self.assertEqual("cold", calculate_customer_score(customer(buying_timeline="one_month"))[1])
        self.assertEqual("warm", calculate_customer_score(customer(buying_timeline="one_month", financial_rating="B"))[1])


if __name__ == "__main__":
    unittest.main()
