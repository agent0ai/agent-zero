/* SPDX-License-Identifier: GPL-2.0-or-later
 * Sparse guest root. Lower paths come from PRoot's canonical binding resolver.
 * All private files and marker directories belong to the leased guest UID.
 */
#include "syscall/chain.h"
#include <stddef.h>
#include <sys/syscall.h>

static const char *lower;
static char whiteouts[PATH_MAX];

static const char *suffix(const char *base, const char *path) {
    if (!base) return NULL;
    size_t n = strlen(base);
    return !strncmp(base, path, n) && (!path[n] || path[n] == '/') ? path + n : NULL;
}

static int compose(char out[PATH_MAX], const char *base, const char *relative) {
    return snprintf(out, PATH_MAX, "%s%s", base, relative) >= PATH_MAX ? -ENAMETOOLONG : 0;
}

int overlay_inverse(char path[PATH_MAX]) {
    const char *relative = lower ? suffix(root, path) : NULL;
    if (!relative) return 0;
    char translated[PATH_MAX];
    if (compose(translated, lower, relative)) return -ENAMETOOLONG;
    strcpy(path, translated);
    return 1;
}

/* A sticky directory in the private marker tree hides this lower name and
 * its descendants. Ordinary directories only hold markers for children. */
static int hidden(const char *relative) {
    char path[PATH_MAX];
    if (compose(path, whiteouts, relative)) return -ENAMETOOLONG;
    size_t prefix = strlen(whiteouts);
    for (char *p = path + prefix; *p;) {
        while (*p == '/') p++;
        while (*p && *p != '/') p++;
        char saved = *p;
        *p = 0;
        struct stat st;
        if (lstat(path, &st)) return errno == ENOENT ? 0 : -errno;
        if (!S_ISDIR(st.st_mode)) return -ENOTDIR;
        if (st.st_mode & S_ISVTX) return 1;
        *p = saved;
    }
    return 0;
}

/* A lower directory descriptor can outlive its name. After a whiteout,
 * re-resolving that descriptor by path could open a replacement directory. */
int overlay_check_dirfd(const char *path) {
    const char *relative = suffix(lower, path);
    if (!relative) return 0;
    int masked = hidden(relative);
    return masked > 0 ? -ESTALE : masked;
}

static int select_layer(char path[PATH_MAX]) {
    const char *relative = suffix(lower, path);
    if (!relative) return 0;
    char upper[PATH_MAX];
    if (compose(upper, root, relative)) return -ENAMETOOLONG;
    struct stat st;
    if (lstat(upper, &st) == 0) {
        strcpy(path, upper);
        return 0;
    }
    if (errno != ENOENT && errno != ENOTDIR) return -errno;
    int masked = hidden(relative);
    if (masked < 0) return masked;
    if (masked) strcpy(path, upper);
    return 0;
}

static int overlay_lock(void) {
    char path[PATH_MAX];
    if (compose(path, control, "/lock")) return -ENAMETOOLONG;
    int fd = open(path, O_RDWR | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return -errno;
    if (flock(fd, LOCK_EX)) {
        int err = -errno;
        close(fd);
        return err;
    }
    return fd;
}

/* Create only missing ancestors, descending by pinned non-symlink descriptors. */
static int make_dirs(const char *base, const char *relative, bool include_leaf) {
    char path[PATH_MAX];
    if (strlen(relative) >= sizeof(path)) return -ENAMETOOLONG;
    strcpy(path, relative);
    size_t length = strlen(path);
    while (length && path[length - 1] == '/') path[--length] = 0;
    if (!include_leaf) {
        char *end = strrchr(path, '/');
        if (!end) return -EINVAL;
        *end = 0;
    }
    int fd = open(base, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return -errno;
    char *cursor = NULL;
    int rc = 0;
    for (char *part = strtok_r(path, "/", &cursor); part; part = strtok_r(NULL, "/", &cursor)) {
        if (!strcmp(part, ".") || !strcmp(part, "..")) { rc = -EINVAL; break; }
        int next = openat(fd, part, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
        if (next < 0 && errno == ENOENT) {
            if (mkdirat(fd, part, 0755) && errno != EEXIST) { rc = -errno; break; }
            next = openat(fd, part, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
        }
        if (next < 0) { rc = -errno; break; }
        close(fd);
        fd = next;
    }
    close(fd);
    return rc;
}

static int mark_hidden(const char *relative) {
    char path[PATH_MAX];
    if (compose(path, whiteouts, relative)) return -ENAMETOOLONG;
    int rc = make_dirs(whiteouts, relative, true);
    if (rc < 0) return rc;
    return chmod(path, 01700) ? -errno : 0;
}

static int private_link(const char *file, const char *path) {
    char name[NAME_MAX + 1];
    int parent = parent_fd(path, name);
    if (parent < 0) return parent;
    int rc = linkat(AT_FDCWD, file, parent, name, 0) ? -errno : 0;
    close(parent);
    return rc;
}

static int publish_aliases(const char *upper, const struct stat *original) {
    char index[PATH_MAX];
    if (snprintf(index, sizeof(index), "%s/../overlay-links/%llu", lower,
                 (unsigned long long)original->st_ino) >= PATH_MAX) return -ENAMETOOLONG;
    FILE *stream = fopen(index, "re");
    if (!stream) return errno == ENOENT ? 0 : -errno;
    char *relative = NULL;
    size_t capacity = 0;
    int rc = 0;
    while (getdelim(&relative, &capacity, 0, stream) > 0) {
        char path[PATH_MAX];
        if ((rc = compose(path, lower, relative)) || (rc = select_layer(path))) break;
        if (!suffix(lower, path)) continue;
        struct stat st;
        if (lstat(path, &st) || st.st_ino != original->st_ino || st.st_dev != original->st_dev) continue;
        if ((rc = make_dirs(root, relative, false)) || (rc = compose(path, root, relative))) break;
        rc = private_link(upper, path);
        if (rc < 0) break;
    }
    if (ferror(stream) && !rc) rc = -EIO;
    if (rc < 0) {
        /* Roll back this inode only. The caller still holds the copy-up lock. */
        struct stat copy;
        if (lstat(upper, &copy) == 0) {
            rewind(stream);
            while (getdelim(&relative, &capacity, 0, stream) > 0) {
                char path[PATH_MAX], name[NAME_MAX + 1];
                if (compose(path, root, relative)) continue;
                int parent = parent_fd(path, name);
                if (parent < 0) continue;
                struct stat linked;
                if (!fstatat(parent, name, &linked, AT_SYMLINK_NOFOLLOW) &&
                    linked.st_dev == copy.st_dev && linked.st_ino == copy.st_ino)
                    unlinkat(parent, name, 0);
                close(parent);
            }
        }
    }
    free(relative);
    fclose(stream);
    return rc;
}

static int copy_one(const char *base, const struct stat *st, int parent, const char *name) {
    if (S_ISDIR(st->st_mode))
        return mkdirat(parent, name, (st->st_mode & 07777) | 0700) && errno != EEXIST ? -errno : 0;
    if (S_ISLNK(st->st_mode)) {
        char target[PATH_MAX];
        ssize_t n = readlink(base, target, sizeof(target));
        if (n < 0) return -errno;
        if (n == sizeof(target)) return -ENAMETOOLONG;
        target[n] = 0;
        return symlinkat(target, parent, name) ? -errno : 0;
    }
    if (S_ISFIFO(st->st_mode)) return mkfifoat(parent, name, st->st_mode & 0777) ? -errno : 0;
    if (!S_ISREG(st->st_mode)) return -EOPNOTSUPP;
    int input = open(base, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    if (input < 0) return -errno;
    char temp[PATH_MAX];
    int rc = compose(temp, control, "/copy-XXXXXX");
    if (rc == 0) {
        int output = mkostemp(temp, O_CLOEXEC);
        if (output < 0) rc = -errno;
        else {
            rc = copy_file(input, output, st);
            if (close(output) && !rc) rc = -errno;
            if (!rc && linkat(AT_FDCWD, temp, parent, name, 0)) rc = -errno;
            if (!rc && st->st_nlink > 1) {
                rc = publish_aliases(temp, st);
                if (rc < 0) unlinkat(parent, name, 0);
            }
            unlink(temp);
        }
    }
    close(input);
    return rc;
}

/* Called with the per-guest lock. A rename of an inherited directory needs a
 * complete movable subtree. Regular lookup and directory listing never call this. */
static int prepare_entry(const char *relative, bool recursive, DIR **children) {
    char base[PATH_MAX], upper[PATH_MAX], selected[PATH_MAX];
    if (compose(base, lower, relative) || compose(upper, root, relative)) return -ENAMETOOLONG;
    strcpy(selected, base);
    int rc = select_layer(selected);
    if (rc < 0) return rc;
    struct stat st;
    if (lstat(selected, &st)) return -errno;
    if (!strcmp(selected, base)) {
        rc = make_dirs(root, relative, false);
        if (rc < 0) return rc;
        char name[NAME_MAX + 1];
        int parent = parent_fd(upper, name);
        if (parent < 0) return parent;
        rc = copy_one(base, &st, parent, name);
        close(parent);
        if (rc < 0) return rc;
    }
    if (!recursive || !S_ISDIR(st.st_mode)) return 0;
    rc = hidden(relative);
    if (rc != 0) return rc < 0 ? rc : 0;
    if (lstat(base, &st)) return errno == ENOENT || errno == ENOTDIR ? 0 : -errno;
    if (!S_ISDIR(st.st_mode)) return 0;
    *children = opendir(base);
    return *children ? 0 : -errno;
}

static int copy_visible(const char *relative, bool recursive) {
    DIR *dir = NULL;
    int rc = prepare_entry(relative, recursive, &dir);
    if (!dir) return rc;
    for (;;) {
        errno = 0;
        struct dirent *entry = readdir(dir);
        if (!entry) { rc = -errno; break; }
        if (!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
        char *child = NULL;
        if (asprintf(&child, "%s/%s", relative, entry->d_name) < 0) { rc = -ENOMEM; break; }
        rc = copy_visible(child, true);
        free(child);
        if (rc < 0 && rc != -ENOENT) break;
    }
    closedir(dir);
    return rc;
}

static int copy_up(const char *relative) {
    int fd = overlay_lock();
    if (fd < 0) return fd;
    int rc = copy_visible(relative, false);
    close(fd);
    return rc;
}

static int overlay_argument(Tracee *t, char path[PATH_MAX], Reg arg, bool copy) {
    const char *relative = suffix(lower, path);
    if (!relative) return 0;
    char upper[PATH_MAX];
    if (compose(upper, root, relative)) return -ENAMETOOLONG;
    struct stat st;
    bool exists = lstat(path, &st) == 0;
    if (!exists && errno != ENOENT) return -errno;
    word_t n = get_sysnum(t, ORIGINAL);
    bool open_call = n == PR_open || n == PR_openat || n == PR_creat;
    int flags = open_call ? (n == PR_creat ? O_CREAT | O_WRONLY | O_TRUNC : (int)peek_reg(t, ORIGINAL, n == PR_open ? SYSARG_2 : SYSARG_3)) : 0;
    if (exists && !copy) return -EEXIST;
    if (exists && (flags & (O_CREAT | O_EXCL)) == (O_CREAT | O_EXCL)) return -EEXIST;
    if (exists && open_call && (flags & O_CREAT) && !(flags & (O_WRONLY | O_RDWR | O_TRUNC))) return 0;
    if (!exists && copy && !(flags & O_CREAT)) return -ENOENT;
    size_t length = strlen(path);
    if (exists && S_ISDIR(st.st_mode) &&
        (path[length - 1] == '/' || (length >= 2 && !strcmp(path + length - 2, "/.")))) {
        chop_finality(path);
        relative = suffix(lower, path);
    }
    int rc = exists ? copy_up(relative) : make_dirs(root, relative, false);
    if (rc < 0) return rc;
    return set_sysarg_path(t, upper, arg);
}

static int translated_path(Tracee *t, char path[PATH_MAX]) {
    int rc = select_layer(path);
    if (rc < 0 || get_sysnum(t, ORIGINAL) != PR_bind) return rc;
    if (readonly(path)) return -EROFS;
    const char *relative = suffix(lower, path);
    if (!relative) return 0;
    struct stat st;
    if (!lstat(path, &st)) return -EADDRINUSE;
    if (errno != ENOENT) return -errno;
    rc = make_dirs(root, relative, false);
    if (rc < 0) return rc;
    char upper[PATH_MAX];
    rc = compose(upper, root, relative);
    if (!rc) strcpy(path, upper);
    return rc;
}

static int overlay_access(Tracee *t, const char *path, Reg mode_arg, word_t mode) {
    struct stat st;
    if (lstat(path, &st)) return 0;
    if (!S_ISDIR(st.st_mode) && (!S_ISREG(st.st_mode) || !(st.st_mode & S_IWUSR))) return 0;
    char parent[PATH_MAX];
    if (compose(parent, root, suffix(lower, path))) return -ENAMETOOLONG;
    while (strlen(parent) > strlen(root)) {
        *strrchr(parent, '/') = 0;
        if (!access(parent, W_OK | X_OK)) {
            poke_reg(t, mode_arg, mode & ~W_OK);
            break;
        }
        if (errno != ENOENT) break;
    }
    return 0;
}

static bool dot_entry(const char *name) {
    return !strcmp(name, ".") || !strcmp(name, "..");
}

static int directory_empty(const char *relative) {
    const char *layers[] = {root, lower};
    for (size_t i = 0; i < 2; i++) {
        char path[PATH_MAX];
        if (compose(path, layers[i], relative)) return -ENAMETOOLONG;
        if (i) {
            int masked = hidden(relative);
            if (masked) return masked < 0 ? masked : 0;
        }
        DIR *dir = opendir(path);
        if (!dir) {
            if (errno == ENOENT || errno == ENOTDIR) continue;
            return -errno;
        }
        int rc = 0;
        for (;;) {
            errno = 0;
            struct dirent *entry = readdir(dir);
            if (!entry) { rc = -errno; break; }
            if (dot_entry(entry->d_name)) continue;
            if (i) {
                char child[PATH_MAX];
                if (snprintf(child, sizeof(child), "%s/%s", relative, entry->d_name) >= PATH_MAX) { rc = -ENAMETOOLONG; break; }
                rc = hidden(child);
                if (rc < 0) break;
                if (rc) { rc = 0; continue; }
            }
            rc = -ENOTEMPTY;
            break;
        }
        closedir(dir);
        if (rc) return rc;
    }
    return 0;
}

static int writable_parent(const char *relative, const char *upper) {
    int rc = make_dirs(root, relative, false);
    if (rc < 0) return rc;
    char name[NAME_MAX + 1];
    int fd = parent_fd(upper, name);
    if (fd < 0) return fd;
    rc = faccessat(fd, ".", W_OK | X_OK, 0) ? -errno : 0;
    close(fd);
    return rc;
}

static int remove_name(const char *relative, bool directory) {
    if (!*relative) return -EBUSY;
    char base[PATH_MAX], upper[PATH_MAX], visible[PATH_MAX];
    if (compose(base, lower, relative) || compose(upper, root, relative)) return -ENAMETOOLONG;
    strcpy(visible, base);
    int rc = select_layer(visible);
    if (rc < 0) return rc;
    struct stat st;
    if (lstat(visible, &st)) return -errno;
    if (directory != !!S_ISDIR(st.st_mode)) return directory ? -ENOTDIR : -EISDIR;
    if (directory && (rc = directory_empty(relative))) return rc;
    rc = writable_parent(relative, upper);
    if (rc < 0) return rc;
    if (!lstat(base, &st) && (rc = mark_hidden(relative))) return rc;
    if (strcmp(visible, upper)) return 0;
    char name[NAME_MAX + 1];
    int parent = parent_fd(upper, name);
    if (parent < 0) return parent;
    rc = unlinkat(parent, name, directory ? AT_REMOVEDIR : 0) ? -errno : 0;
    close(parent);
    return rc;
}

static int rename_name(const char *from, const char *to, unsigned flags) {
    if (!*from || !*to) return -EBUSY;
    if (flags & ~(RENAME_NOREPLACE | RENAME_EXCHANGE)) return -EINVAL;
    char src[PATH_MAX], dst[PATH_MAX], a[PATH_MAX], b[PATH_MAX];
    if (compose(src, lower, from) || compose(dst, lower, to) ||
        compose(a, root, from) || compose(b, root, to)) return -ENAMETOOLONG;
    int rc = select_layer(src);
    if (!rc) rc = select_layer(dst);
    if (rc < 0) return rc;
    struct stat source, dest;
    if (lstat(src, &source)) return -errno;
    bool exists = !lstat(dst, &dest);
    if (!exists && errno != ENOENT) return -errno;
    if (exists && (flags & RENAME_NOREPLACE)) return -EEXIST;
    if (!exists && (flags & RENAME_EXCHANGE)) return -ENOENT;
    if (exists && source.st_dev == dest.st_dev && source.st_ino == dest.st_ino) return 0;
    const char *nested = suffix(from, to);
    if (S_ISDIR(source.st_mode) && nested && *nested) return -EINVAL;
    if (exists && !(flags & RENAME_EXCHANGE)) {
        if (S_ISDIR(source.st_mode) != S_ISDIR(dest.st_mode)) return S_ISDIR(source.st_mode) ? -ENOTDIR : -EISDIR;
        if (S_ISDIR(dest.st_mode) && (rc = directory_empty(to))) return rc;
    }
    if ((rc = writable_parent(from, a)) || (rc = writable_parent(to, b))) return rc;
    if ((rc = copy_visible(from, true))) return rc;
    if ((flags & RENAME_EXCHANGE) && (rc = copy_visible(to, true))) return rc;
    /* Mark the complete source before moving it. An ordinary replacement
     * already shadows its old destination, which must be empty if a directory. */
    struct stat st;
    if (compose(src, lower, from) || compose(dst, lower, to)) return -ENAMETOOLONG;
    if (!lstat(src, &st) && (rc = mark_hidden(from))) return rc;
    if ((flags & RENAME_EXCHANGE) && !lstat(dst, &st) && (rc = mark_hidden(to))) return rc;
    char old_name[NAME_MAX + 1], new_name[NAME_MAX + 1];
    int old_parent = parent_fd(a, old_name);
    if (old_parent < 0) return old_parent;
    int new_parent = parent_fd(b, new_name);
    rc = new_parent;
    if (new_parent >= 0) {
        rc = syscall(SYS_renameat2, old_parent, old_name, new_parent, new_name, flags) ? -errno : 0;
        close(new_parent);
    }
    close(old_parent);
    return rc;
}

/* Preserve the kernel's directory requirement before using canonical marker names. */
static int namespace_path(char *path, bool destination, bool *slash) {
    size_t n = strlen(path);
    if (n >= 2 && !strcmp(path + n - 2, "/.")) return -EINVAL;
    *slash = n && path[n - 1] == '/';
    if (*slash) {
        struct stat st;
        if (lstat(path, &st) && (!destination || errno != ENOENT)) return -errno;
        while (n && path[n - 1] == '/') path[--n] = 0;
    }
    return 0;
}

static int overlay_namespace(Tracee *t, word_t n) {
    bool removal = n == PR_unlink || n == PR_rmdir || n == PR_unlinkat;
    bool rename_op = n == PR_rename || n == PR_renameat || n == PR_renameat2;
    if (!removal && !rename_op) return 1;
    bool at = n == PR_unlinkat || n == PR_renameat || n == PR_renameat2;
    char source[PATH_MAX], dest[PATH_MAX];
    int rc = get_sysarg_path(t, source, at ? SYSARG_2 : SYSARG_1);
    if (rc < 0) return rc;
    if (readonly(source)) return -EROFS;
    const char *from = suffix(lower, source) ?: suffix(root, source);
    const char *to = NULL;
    if (rename_op) {
        rc = get_sysarg_path(t, dest, at ? SYSARG_4 : SYSARG_2);
        if (rc < 0) return rc;
        if (readonly(dest)) return -EROFS;
        to = suffix(lower, dest) ?: suffix(root, dest);
        if (!!from != !!to) return -EXDEV;
    }
    if (!from) return 1;
    bool slash;
    rc = namespace_path(source, false, &slash);
    if (rc < 0) return rc;
    if (rename_op) {
        rc = namespace_path(dest, true, &slash);
        if (rc < 0) return rc;
        struct stat st;
        if (slash && !lstat(source, &st) && !S_ISDIR(st.st_mode)) return -ENOTDIR;
    }
    unsigned flags = n == PR_unlinkat ? peek_reg(t, ORIGINAL, SYSARG_3) : 0;
    if (flags & ~AT_REMOVEDIR) return -EINVAL;
    int fd = overlay_lock();
    if (fd < 0) return fd;
    if (removal) rc = remove_name(from, n == PR_rmdir || (flags & AT_REMOVEDIR));
    else rc = rename_name(from, to, n == PR_renameat2 ? peek_reg(t, ORIGINAL, SYSARG_5) : 0);
    close(fd);
    if (rc == 0) set_sysnum(t, PR_void);
    return rc;
}

static int name_cmp(const struct dirent **a, const struct dirent **b) {
    return strcmp((*a)->d_name, (*b)->d_name);
}

static void free_listing(struct dirent **items, int count) {
    for (int i = 0; i < count; i++) free(items[i]);
    free(items);
}

/* Use the kernel directory description's offset for the merged listing.
 * dup, fork, rewinddir and seekdir therefore share the same cursor. */
static int merged_fd(Tracee *t, char upper[PATH_MAX], char base[PATH_MAX]) {
    int fd = peek_reg(t, ORIGINAL, SYSARG_1);
    if (readlink_proc_pid_fd(t->pid, fd, upper) < 0) return 0;
    const char *relative = suffix(root, upper);
    if (!relative) {
        relative = suffix(lower, upper);
        if (!relative) return 0;
        int rc = overlay_check_dirfd(upper);
        if (rc < 0) return rc;
        char private[PATH_MAX];
        if (compose(private, root, relative)) return -ENAMETOOLONG;
        strcpy(upper, private);
        relative = upper + strlen(root);
        struct stat st;
        if (lstat(upper, &st) || !S_ISDIR(st.st_mode)) return 0;
    }
    int masked = hidden(relative);
    if (masked) return masked < 0 ? masked : 0;
    if (compose(base, lower, relative)) return -ENAMETOOLONG;
    struct stat st;
    return !lstat(base, &st) && S_ISDIR(st.st_mode);
}

static int get_directory_offset(Tracee *t) {
    char upper[PATH_MAX], base[PATH_MAX];
    int rc = merged_fd(t, upper, base);
    if (rc <= 0) return rc;
    set_sysnum(t, PR_lseek);
    poke_reg(t, SYSARG_2, 0);
    poke_reg(t, SYSARG_3, SEEK_CUR);
    return 0;
}

static size_t put_entry(unsigned char *buf, size_t cap, const struct dirent *entry,
                        uint64_t next, bool modern, size_t word) {
    size_t header = modern ? 19 : 2 * word + 2;
    size_t align = modern ? 8 : word;
    size_t length = (header + strlen(entry->d_name) + 1 + !modern + align - 1) & ~(align - 1);
    if (length > cap) return 0;
    memset(buf, 0, length);
    uint64_t inode = entry->d_ino;
    size_t field = modern ? 8 : word;
    memcpy(buf, &inode, field);
    memcpy(buf + field, &next, field);
    uint16_t bytes = length;
    memcpy(buf + 2 * field, &bytes, sizeof(bytes));
    buf[modern ? 18 : length - 1] = entry->d_type;
    strcpy((char *)buf + header, entry->d_name);
    return length;
}

static int emit_directory(Tracee *t, bool modern, long offset) {
    if (offset < 0) return offset;
    char upper[PATH_MAX], base[PATH_MAX];
    int rc = merged_fd(t, upper, base);
    if (rc <= 0) return rc < 0 ? rc : -ESTALE;
    struct dirent **up = NULL, **down = NULL;
    int nu = scandir(upper, &up, NULL, name_cmp);
    if (nu < 0) return -errno;
    int nd = scandir(base, &down, NULL, name_cmp);
    if (nd < 0) { rc = -errno; free_listing(up, nu); return rc; }
    unsigned char buffer[32768];
    size_t cap = peek_reg(t, ORIGINAL, SYSARG_3);
    if (cap > sizeof(buffer)) cap = sizeof(buffer);
    size_t used = 0;
    char markers[PATH_MAX];
    if (compose(markers, whiteouts, suffix(root, upper))) {
        free_listing(up, nu);
        free_listing(down, nd);
        return -ENAMETOOLONG;
    }
    int marker_fd = open(markers, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    int marker_error = errno;
    long index = 0;
    int i = 0, j = 0;
    if (marker_fd < 0 && marker_error != ENOENT) rc = -marker_error;
    while (rc >= 0 && (i < nu || j < nd)) {
        int order = i == nu ? 1 : j == nd ? -1 : strcmp(up[i]->d_name, down[j]->d_name);
        const struct dirent *entry;
        if (order <= 0) {
            entry = up[i++];
            if (order == 0) j++;
        } else {
            entry = down[j++];
            if (marker_fd >= 0) {
                struct stat st;
                if (fstatat(marker_fd, entry->d_name, &st, AT_SYMLINK_NOFOLLOW) == 0) {
                    if (st.st_mode & S_ISVTX) continue;
                } else if (errno != ENOENT) { rc = -errno; break; }
            }
        }
        if (index < offset) { index++; continue; }
        size_t bytes = put_entry(buffer + used, cap - used, entry, index + 1, modern, sizeof_word(t));
        if (!bytes) { if (!used) rc = -EINVAL; break; }
        used += bytes;
        index++;
    }
    if (marker_fd >= 0) close(marker_fd);
    free_listing(up, nu);
    free_listing(down, nd);
    if (rc < 0) return rc;
    if (used) {
        rc = write_data(t, peek_reg(t, ORIGINAL, SYSARG_2), buffer, used);
        if (rc < 0) return rc;
        rc = register_chained_syscall(t, PR_lseek, peek_reg(t, ORIGINAL, SYSARG_1), index, SEEK_SET, 0, 0, 0);
        if (rc < 0) return rc;
        force_chain_final_result(t, used);
    }
    poke_reg(t, SYSARG_RESULT, used);
    return 0;
}

static int overlay_dir_exit(Tracee *t) {
    word_t original = get_sysnum(t, ORIGINAL);
    if (t->status < 0) return 0;
    if ((original == PR_getdents64 || original == PR_getdents) && get_sysnum(t, MODIFIED) == PR_lseek)
        return emit_directory(t, original == PR_getdents64, (long)peek_reg(t, CURRENT, SYSARG_RESULT));
    if ((original == PR_unlink || original == PR_unlinkat || original == PR_rmdir ||
         original == PR_rename || original == PR_renameat || original == PR_renameat2) &&
        get_sysnum(t, MODIFIED) == PR_void)
        poke_reg(t, SYSARG_RESULT, 0);
    return 0;
}
