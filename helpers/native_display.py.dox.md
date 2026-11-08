# Native display operations

Standard-library XRandR size detection, bounded mode selection and resizing.
`virtual_desktop` supplies host localization/environment and window fitting;
the Browser guest loads this same source for its private X display. No framework
imports, state discovery, route registration or package installation occurs here.
Verify Desktop resize regression tests and the Browser sandbox viewer smoke test.
