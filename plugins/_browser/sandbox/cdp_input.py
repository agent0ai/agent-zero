"""Trusted Chromium input events for the Linux browser guest."""


_MODIFIERS = {"Alt": 1, "Control": 2, "Meta": 4, "Shift": 8}
_BUTTONS = {"left": 1, "right": 2, "middle": 4, "back": 8, "forward": 16}
_NAMED = {
    "Backspace": 8, "Tab": 9, "Enter": 13, "Shift": 16, "Control": 17, "Alt": 18,
    "Pause": 19, "CapsLock": 20, "Escape": 27, " ": 32, "PageUp": 33, "PageDown": 34,
    "End": 35, "Home": 36, "ArrowLeft": 37, "ArrowUp": 38, "ArrowRight": 39,
    "ArrowDown": 40, "PrintScreen": 44, "Insert": 45, "Delete": 46, "Meta": 91,
    "ContextMenu": 93, "NumLock": 144, "ScrollLock": 145, "AltGraph": 225, "Clear": 12,
    **{f"F{i}": 111 + i for i in range(1, 25)},
}
_PUNCTUATION = {
    ";:": ("Semicolon", 186), "=+": ("Equal", 187), ",<": ("Comma", 188),
    "-_": ("Minus", 189), ".>": ("Period", 190), "/?": ("Slash", 191),
    "`~": ("Backquote", 192), "[{": ("BracketLeft", 219), "\\|": ("Backslash", 220),
    "]}": ("BracketRight", 221), "'\"": ("Quote", 222),
}
_NUMPAD = {"Add": ("+", 107), "Subtract": ("-", 109), "Multiply": ("*", 106),
           "Divide": ("/", 111), "Enter": ("Enter", 13)}
_NUMPAD_NAV = ("Insert", "End", "ArrowDown", "PageDown", "ArrowLeft", "Clear",
               "ArrowRight", "Home", "ArrowUp", "PageUp")
_ALIASES = {"\n": "Enter", "\r": "Enter", "\t": "Tab", "Space": " ", "Spacebar": " ", "Return": "Enter", "Esc": "Escape",
            "Ctrl": "Control", "ControlOrMeta": "Control"}


def _key(raw, shifted):
    key = _ALIASES.get(raw, raw)
    for modifier in _MODIFIERS:
        if key in (modifier + "Left", modifier + "Right"):
            return modifier, key, 92 if key == "MetaRight" else _NAMED[modifier]
    if key.startswith("Numpad"):
        pad = key.removeprefix("Numpad")
        if pad in _NUMPAD:
            symbol, virtual = _NUMPAD[pad]
            return symbol, key, virtual
        if len(pad) == 1 and pad in "0123456789":
            navigation = _NUMPAD_NAV[int(pad)]
            return (pad, key, 96 + int(pad)) if shifted else (navigation, key, _NAMED[navigation])
        if pad == "Decimal":
            return (".", key, 110) if shifted else ("Delete", key, 46)
    if key in _NAMED:
        code = "Space" if key == " " else key + "Left" if key in _MODIFIERS else key
        return key, code, _NAMED[key]
    if key.startswith("Key") and len(key) == 4:
        key = key[-1].lower()
    if key.startswith("Digit") and len(key) == 6:
        key = key[-1]
    if len(key) == 1 and key.isascii() and key.isalpha():
        return key.upper() if shifted else key, "Key" + key.upper(), ord(key.upper())
    for digit, symbol in zip("1234567890", "!@#$%^&*()"):
        if key in (digit, symbol):
            return symbol if shifted else key, "Digit" + digit, ord(digit)
    for pair, (code, virtual) in _PUNCTUATION.items():
        if key in (pair[0], pair[1], code):
            return pair[1] if shifted or key == pair[1] else pair[0], code, virtual
    if len(key) == 1:
        return key, "", 0
    raise ValueError(f"Unknown Chromium key {raw!r}")


class Keyboard:
    def __init__(self, page):
        self.page = page
        self.modifiers = 0
        self.held = set()

    async def _event(self, raw, down):
        key, code, virtual = _key(raw, self.modifiers & 8)
        flag = _MODIFIERS.get(key, 0)
        modifiers = self.modifiers | flag if down else self.modifiers & ~flag
        text = key if len(key) == 1 else "\r" if key == "Enter" else ""
        if modifiers & 7:
            text = ""
        params = {"type": "keyDown" if text else "rawKeyDown", "key": key, "code": code,
                  "windowsVirtualKeyCode": virtual, "modifiers": modifiers}
        if down:
            params.update(text=text, autoRepeat=code in self.held)
        else:
            params["type"] = "keyUp"
        if code.startswith("Numpad"):
            params.update(location=3, isKeypad=True)
        elif flag:
            params["location"] = 2 if code.endswith("Right") else 1
        await self.page.send("Input.dispatchKeyEvent", params)
        self.modifiers = modifiers
        if down:
            self.held.add(code)
        else:
            self.held.discard(code)

    async def down(self, key):
        await self._event(key, True)

    async def up(self, key):
        await self._event(key, False)

    async def press(self, chord):
        # Keep '+' usable both as a literal and as the final key of 'Control++'.
        keys = chord.split("+") if not chord.endswith("+") else chord[:-1].split("+")[:-1] + ["+"]
        pressed = []
        try:
            for key in keys:
                await self.down(key)
                pressed.append(key)
        finally:
            for key in reversed(pressed):
                await self.up(key)

    async def insert_text(self, text):
        await self.page.send("Input.insertText", {"text": text})

    async def type(self, text):
        for character in text:
            if character in _ALIASES or character.isascii() and character.isprintable():
                await self.press(character)
            else:
                await self.insert_text(character)


class Mouse:
    def __init__(self, page):
        self.page = page
        self.x = self.y = 0
        self.buttons = 0

    async def _event(self, kind, **kwargs):
        await self.page.send("Input.dispatchMouseEvent", {
            "type": kind, "x": self.x, "y": self.y, "buttons": self.buttons,
            "modifiers": self.page.keyboard.modifiers, **kwargs})

    async def move(self, x, y, steps=1):
        start_x, start_y = self.x, self.y
        for step in range(1, steps + 1):
            self.x, self.y = start_x + (x - start_x) * step / steps, start_y + (y - start_y) * step / steps
            await self._event("mouseMoved")

    async def down(self, button="left", click_count=1):
        self.buttons |= _BUTTONS[button]
        try:
            await self._event("mousePressed", button=button, clickCount=click_count)
        except BaseException:
            self.buttons &= ~_BUTTONS[button]
            raise

    async def up(self, button="left", click_count=1):
        self.buttons &= ~_BUTTONS[button]
        await self._event("mouseReleased", button=button, clickCount=click_count)

    async def click(self, x, y, button="left"):
        await self.move(x, y)
        await self.down(button)
        await self.up(button)

    async def dblclick(self, x, y, button="left"):
        await self.click(x, y, button)
        await self.down(button, 2)
        await self.up(button, 2)

    async def wheel(self, delta_x, delta_y):
        await self._event("mouseWheel", deltaX=delta_x, deltaY=delta_y)
