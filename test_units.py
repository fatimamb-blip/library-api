"""Unit tests for the rules, with no HTTP and no database.

The email sender and the repositories are replaced by mock objects, so each
test checks one piece of logic in isolation.
"""
import unittest
from datetime import date
from unittest import mock

import notifications
from errors import ApiError, api_error
from services import loan_service
from utils import checks, fines, validation

TODAY = date(2026, 1, 20)


def loan(**overrides):
    row = {
        "id": 1, "book_id": 1, "member_id": 1, "due_date": "2026-01-15",
        "returned": 0, "fine": 0.0, "fine_paid": 0, "renewals": 0, "checked_out": "2026-01-01",
    }
    row.update(overrides)
    return row


class FineTests(unittest.TestCase):
    def test_fifty_cents_per_day_late(self):
        self.assertEqual(fines.fine_for("2026-01-15", today=TODAY), 2.5)

    def test_no_fine_when_on_time_or_early(self):
        self.assertEqual(fines.fine_for("2026-01-20", today=TODAY), 0)
        self.assertEqual(fines.fine_for("2026-02-01", today=TODAY), 0)

    def test_open_loan_owes_growing_fine(self):
        self.assertEqual(fines.amount_owed(loan(), today=TODAY), 2.5)

    def test_returned_unpaid_loan_owes_its_fine(self):
        self.assertEqual(fines.amount_owed(loan(returned=1, fine=1.5), today=TODAY), 1.5)

    def test_paid_loan_owes_nothing(self):
        self.assertEqual(fines.amount_owed(loan(returned=1, fine=1.5, fine_paid=1), today=TODAY), 0)

    def test_total_owed(self):
        loans = [loan(), loan(returned=1, fine=1.0)]
        self.assertEqual(fines.total_owed(loans, today=TODAY), 3.5)


class ValidationTests(unittest.TestCase):
    def test_isbn(self):
        self.assertTrue(validation.is_valid_isbn("978-0441013593"))
        self.assertFalse(validation.is_valid_isbn("123"))

    def test_email(self):
        self.assertTrue(validation.is_valid_email("a@b.co"))
        self.assertFalse(validation.is_valid_email("not-an-email"))

    def test_date(self):
        self.assertTrue(validation.is_valid_date("2026-01-15"))
        self.assertFalse(validation.is_valid_date("next week"))


class CheckTests(unittest.TestCase):
    def test_loan_limits(self):
        self.assertEqual(checks.loan_limit_for("student"), 3)
        self.assertEqual(checks.loan_limit_for("staff"), 5)

    def test_cannot_renew_overdue(self):
        with self.assertRaises(ApiError) as ctx:
            checks.check_can_renew(loan(), today=TODAY)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_cannot_renew_twice(self):
        with self.assertRaises(ApiError) as ctx:
            checks.check_can_renew(loan(due_date="2026-02-01", renewals=1), today=TODAY)
        self.assertEqual(ctx.exception.message, "loan was already renewed")


class ErrorTests(unittest.TestCase):
    def test_api_error_keeps_message_and_status(self):
        error = api_error("teapot", 418)
        self.assertEqual((error.message, error.status_code), ("teapot", 418))


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.sender = notifications.MockEmailSender()
        notifications.set_sender(self.sender)

    def tearDown(self):
        notifications.reset_sender()

    def test_return_email_format(self):
        notifications.book_returned("sam@campus.edu", "Dune", 2.5)
        self.assertEqual(
            self.sender.sent,
            [notifications.Email("sam@campus.edu", "Book returned", "You returned Dune. Fine: $2.5")],
        )

    def test_return_book_sends_one_email(self):
        """The service is tested with mock repositories and a mock email sender."""
        open_loan = loan(due_date=date.today().isoformat())
        with mock.patch.object(loan_service.loan_repository, "get_loan", return_value=open_loan), \
             mock.patch.object(loan_service.loan_repository, "mark_returned",
                               return_value=loan(returned=1)) as mark_returned, \
             mock.patch.object(loan_service.member_service, "get_member",
                               return_value={"id": 1, "email": "sam@campus.edu"}), \
             mock.patch.object(loan_service.book_service, "get_book",
                               return_value={"id": 1, "title": "Dune", "available": 0}):
            loan_service.return_book(1)

        mark_returned.assert_called_once_with(1, 1, 0)
        self.assertEqual(self.sender.subjects(), ["Book returned"])


if __name__ == "__main__":
    unittest.main()
