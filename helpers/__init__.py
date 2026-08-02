# This file must exist. Without it, `helpers` is imported as a namespace
# package (no __file__), which makes test/module cleanup helpers that purge
# `sys.modules` treat it as a stub and delete every loaded `helpers.*`
# module. The subsequent re-imports then split extension-registry state
# between stale and fresh module copies (observed as `Agent` instances
# losing extension-initialized attributes such as `loop_data` depending on
# test import order). Keeping `helpers` a regular package prevents that
# entire pollution class.
