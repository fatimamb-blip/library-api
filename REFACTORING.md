# Refactored structure

```
app.py                 wires everything together (provides app and init_db)
db.py                  the only module that opens the database; init_db
errors.py              ApiError + api_error(message, status_code) + JSON error handler
notifications.py       EmailSender interface, OutboxEmailSender (mock mail server -> outbox.txt),
                       MockEmailSender (in-memory, for tests)
utils/
  validation.py        input format checks (email, ISBN, date, member type)
  checks.py            library rule checks that raise ApiError (limits, renewals, availability…)
  fines.py             fine calculation ($0.50/day), amounts owed, money rounding
repositories/          SQL only:  book_, member_, loan_repository.py
services/              rules only: book_, member_, loan_, report_service.py
routers/               HTTP only:  book_, member_, loan_, report_router.py (Flask blueprints)
test_api.py            original API tests (unchanged)
test_units.py          unit tests with no HTTP or database, using mock objects
```

Each layer only talks to the layer below it: router → service → repository → db.

## Mocked notifications

Services call `notifications.book_checked_out(...)` etc. and never touch a file or a mail
server. The default sender, `OutboxEmailSender`, mocks a mail server by appending to
`outbox.txt`. Tests swap in `MockEmailSender` with `notifications.set_sender(...)`
and check `sender.sent`. Both have the same interface, so the services can't tell them apart
([Mock object](https://en.wikipedia.org/wiki/Mock_object)).

## Measurements

| Measure | Before | After |
|---|---|---|
| Tests passing | 53 | 53 API + 15 unit = 68 |
| Lines in the largest file | 555 | 92 |
| Places where the fine rate appears | 7 | 1 (`utils/fines.py`) |
| Route handlers containing SQL | 16 | 0 |
| Places that open the database | 17 | 1 (`db.py`) |
| Can the fine rule be tested without HTTP or a database? | No | Yes (`test_units.py`) |

The global `CURRENT_MEMBER` and the control-coupled `check(value, kind)` and
`notify(kind, ...)` functions are gone.
