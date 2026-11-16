from pathlib import Path
import shutil

root = Path(__file__).parent
src = root / 'proot-5.5.0/src'
shutil.copyfile(root / 'cow.c', src / 'extension/cow.c')
file = src / 'GNUmakefile'
text = file.read_text()
if 'extension/cow.o' not in text:
    file.write_text(text.replace('extension/extension.o', 'extension/cow.o \\\n\textension/extension.o'))
file = src / 'cli/proot.c'
text = file.read_text()
if 'cow_callback' not in text:
    text = text.replace('static int handle_option_i(', 'extern int cow_callback(Extension *, ExtensionEvent, intptr_t, intptr_t);\n\nstatic int handle_option_i(')
    text = text.replace('(void) initialize_extension(tracee, fake_id0_callback, value);', '(void) initialize_extension(tracee, fake_id0_callback, value);\n    if (getenv("A0_COW_ROOT") && initialize_extension(tracee, cow_callback, value) < 0)\n        return -1;')
    file.write_text(text)

file = src / 'cli/proot.c'
text = file.read_text()
if 'A0-COW-1' not in text:
    file.write_text(text.replace('    print_version(cli);', '    print_version(cli);\n    puts("A0-COW-1");'))
