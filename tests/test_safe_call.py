import asyncio
import unittest

from helpers.functions import safe_call


class SafeCallTests(unittest.TestCase):
    def test_ignores_positional_only_keyword_from_hook_context(self):
        def hook(default="fallback", /):
            return default

        self.assertEqual(safe_call(hook, default="context"), "fallback")

    def test_keeps_explicit_positional_only_argument(self):
        def hook(value, /):
            return value

        self.assertEqual(safe_call(hook, "positional", value="context"), "positional")

    def test_ignores_varargs_parameter_name_as_keyword(self):
        def hook(*args):
            return args

        self.assertEqual(safe_call(hook, 1, 2, args="context"), (1, 2))

    def test_keeps_keyword_only_and_positional_or_keyword_parameters(self):
        def hook(value, *, enabled=False):
            return value, enabled

        self.assertEqual(safe_call(hook, value=3, enabled=True, extra=9), (3, True))

    def test_keeps_arbitrary_kwargs_when_hook_accepts_them(self):
        def hook(value, /, **kwargs):
            return value, kwargs

        self.assertEqual(safe_call(hook, 1, value=2, other=3), (1, {"value": 2, "other": 3}))

    def test_preserves_extra_positional_argument_filter(self):
        def hook(value):
            return value

        self.assertEqual(safe_call(hook, 1, 2, 3), 1)

    def test_does_not_hide_missing_required_arguments(self):
        def hook(value, /):
            return value

        with self.assertRaises(TypeError):
            safe_call(hook, value=1)

    def test_bound_method_filters_unsupported_keywords(self):
        class Hook:
            def run(self, default="fallback", /, *, enabled=False):
                return default, enabled

        self.assertEqual(
            safe_call(Hook().run, default="context", enabled=True),
            ("fallback", True),
        )

    def test_async_hook_retains_awaitable_result(self):
        async def hook(default="fallback", /):
            return default

        self.assertEqual(asyncio.run(safe_call(hook, default="context")), "fallback")
