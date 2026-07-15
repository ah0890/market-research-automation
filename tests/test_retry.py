import unittest

from utils.retry import retry_with_backoff


class RetryOnlyError(Exception):
    pass


class DoNotRetryError(Exception):
    pass


class RetryWithBackoffTests(unittest.TestCase):
    def test_succeeds_without_retrying_on_first_success(self) -> None:
        calls = {"count": 0}

        @retry_with_backoff(retries=3, backoff_seconds=0.0, retryable_exceptions=(RetryOnlyError,))
        def always_succeeds() -> str:
            calls["count"] += 1
            return "ok"

        self.assertEqual(always_succeeds(), "ok")
        self.assertEqual(calls["count"], 1)

    def test_retries_then_succeeds(self) -> None:
        calls = {"count": 0}

        @retry_with_backoff(retries=3, backoff_seconds=0.0, retryable_exceptions=(RetryOnlyError,))
        def fails_twice_then_succeeds() -> str:
            calls["count"] += 1
            if calls["count"] < 3:
                raise RetryOnlyError("transient")
            return "ok"

        self.assertEqual(fails_twice_then_succeeds(), "ok")
        self.assertEqual(calls["count"], 3)

    def test_raises_after_exhausting_retries(self) -> None:
        calls = {"count": 0}

        @retry_with_backoff(retries=2, backoff_seconds=0.0, retryable_exceptions=(RetryOnlyError,))
        def always_fails() -> None:
            calls["count"] += 1
            raise RetryOnlyError("still failing")

        with self.assertRaises(RetryOnlyError):
            always_fails()
        self.assertEqual(calls["count"], 2)

    def test_non_retryable_exception_propagates_immediately(self) -> None:
        calls = {"count": 0}

        @retry_with_backoff(retries=3, backoff_seconds=0.0, retryable_exceptions=(RetryOnlyError,))
        def raises_wrong_error() -> None:
            calls["count"] += 1
            raise DoNotRetryError("not retryable")

        with self.assertRaises(DoNotRetryError):
            raises_wrong_error()
        self.assertEqual(calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
