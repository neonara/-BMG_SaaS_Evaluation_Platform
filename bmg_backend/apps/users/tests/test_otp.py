"""apps/users/tests/test_otp.py"""
import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


class TestOTP:
    def test_generate_stores_in_cache(self):
        from apps.users.otp import _otp_key, generate_and_store
        code = generate_and_store("test@example.com")
        assert len(code) == 6
        assert code.isdigit()
        assert cache.get(_otp_key("test@example.com")) is not None

    def test_verify_correct_code_returns_true(self):
        from apps.users.otp import generate_and_store, verify
        code = generate_and_store("user@test.com")
        assert verify("user@test.com", code) is True

    def test_verify_deletes_key_after_success(self):
        from apps.users.otp import _otp_key, generate_and_store, verify
        code = generate_and_store("user@test.com")
        verify("user@test.com", code)
        assert cache.get(_otp_key("user@test.com")) is None

    def test_verify_wrong_code_returns_false(self):
        from apps.users.otp import generate_and_store, verify
        generate_and_store("user@test.com")
        assert verify("user@test.com", "000000") is False

    def test_verify_missing_key_returns_false(self):
        from apps.users.otp import verify
        assert verify("nobody@test.com", "123456") is False

    def test_code_is_one_time_use(self):
        from apps.users.otp import generate_and_store, verify
        code = generate_and_store("user@test.com")
        assert verify("user@test.com", code) is True
        assert verify("user@test.com", code) is False  # already consumed

    def test_case_insensitive_email(self):
        from apps.users.otp import generate_and_store, verify
        code = generate_and_store("User@Test.com")
        assert verify("user@test.com", code) is True
