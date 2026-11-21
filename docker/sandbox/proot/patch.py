from pathlib import Path
import shutil

root = Path(__file__).parent
src = root / 'proot-5.5.0/src'
shutil.copyfile(root / 'cow.c', src / 'extension/cow.c')
shutil.copyfile(root / 'overlay.c', src / 'extension/overlay.c')
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
if 'A0-COW-3' not in text:
    file.write_text(text.replace('    print_version(cli);', '    print_version(cli);\n    puts("A0-COW-3");'))

# Resolve a directory descriptor opened on the upper back into guest paths.
file = src / 'path/path.c'
text = file.read_text()
anchor = 'status = readlink_proc_pid_fd(tracee->pid, dir_fd, result);'
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + """
    extern int overlay_check_dirfd(const char *);
    if (status >= 0) status = overlay_check_dirfd(result);""")
anchor = 'if (strnlen(path, PATH_MAX) >= PATH_MAX)'
assert text.count(anchor) == 1
file.write_text(text.replace(anchor, '''extern int overlay_inverse(char *);
    int inverse = overlay_inverse(path);
    if (inverse < 0) return inverse;
    char ref[PATH_MAX];
    if (t_referrer && strnlen(t_referrer, PATH_MAX) < PATH_MAX) {
        strcpy(ref, t_referrer);
        inverse = overlay_inverse(ref);
        if (inverse < 0) return inverse;
        if (inverse) t_referrer = ref;
    }
    ''' + anchor))
