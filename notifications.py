"""Notifications.

The library talks to an EmailSender interface, never to a mail server.
Two implementations share that interface, so callers can't tell them apart
(see https://en.wikipedia.org/wiki/Mock_object):

* OutboxEmailSender is the default. It mocks a real mail server by appending
  each email to outbox.txt.
* MockEmailSender keeps emails in memory so unit tests can check what was
  sent, without touching any file.

Swap the sender with set_sender(); restore the default with reset_sender().
"""
from dataclasses import dataclass

from utils.fines import money

OUTBOX_PATH = "outbox.txt"


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    body: str


class EmailSender:
    """Interface: anything with send(email) can deliver notifications."""

    def send(self, email):
        raise NotImplementedError


class OutboxEmailSender(EmailSender):
    """Mock mail server: writes each email as one line of outbox.txt."""

    def __init__(self, path=OUTBOX_PATH):
        self.path = path

    def send(self, email):
        with open(self.path, "a") as f:
            f.write("TO: " + email.to + " | SUBJECT: " + email.subject + " | BODY: " + email.body + "\n")


class MockEmailSender(EmailSender):
    """Test double: records emails instead of delivering them."""

    def __init__(self):
        self.sent = []

    def send(self, email):
        self.sent.append(email)

    def subjects(self):
        return [email.subject for email in self.sent]


_sender = OutboxEmailSender()


def set_sender(sender):
    global _sender
    _sender = sender


def reset_sender():
    set_sender(OutboxEmailSender())


def get_sender():
    return _sender


def _send(to, subject, body):
    _sender.send(Email(to, subject, body))


def book_checked_out(email, title):
    _send(email, "Book checked out", "You checked out " + title)


def loan_renewed(email, title):
    _send(email, "Loan renewed", "You renewed " + title)


def book_returned(email, title, fine):
    _send(email, "Book returned", "You returned " + title + ". Fine: $" + str(money(fine)))


def fine_paid(email, amount):
    _send(email, "Fine paid", "We received $" + str(money(amount)))
