/* SPDX-License-Identifier: GPL-2.0-or-later
 * File-data CoW over a private hard-link tree. Linux UIDs enforce ownership. */
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/xattr.h>
#include <sys/socket.h>
#include <unistd.h>
#include "extension/extension.h"
#include "tracee/mem.h"
#include "tracee/reg.h"
#include "tracee/abi.h"
#include "syscall/syscall.h"
#include "syscall/sysnum.h"
#include "path/path.h"

static const char *root, *control;
static char *readonly_paths;

/* Fake-root credentials are for installers; Unix IPC must send real kernel IDs. */
static int send_credentials(Tracee *tracee) {
    if (get_abi(tracee) != ABI_DEFAULT) return 0;
    struct msghdr message;
    int status = read_data(tracee, &message, peek_reg(tracee, CURRENT, SYSARG_2), sizeof(message));
    if (status < 0 || !message.msg_control || !message.msg_controllen) return status;
    if (message.msg_controllen > 1048576) return -EINVAL;
    void *buffer = malloc(message.msg_controllen);
    if (!buffer) return -ENOMEM;
    status = read_data(tracee, buffer, (word_t)message.msg_control, message.msg_controllen);
    if (status < 0) { free(buffer); return status; }
    message.msg_control = buffer;
    int changed = 0;
    for (struct cmsghdr *header = CMSG_FIRSTHDR(&message); header; header = CMSG_NXTHDR(&message, header)) {
        size_t remaining = (char *)buffer + message.msg_controllen - (char *)header;
        if (header->cmsg_len < sizeof(*header) || header->cmsg_len > remaining) { free(buffer); return -EINVAL; }
        if (header->cmsg_level == SOL_SOCKET && header->cmsg_type == SCM_CREDENTIALS && header->cmsg_len == CMSG_LEN(sizeof(struct ucred))) {
            struct ucred *credentials = (struct ucred *)CMSG_DATA(header);
            credentials->uid = getuid(); credentials->gid = getgid();
            changed = 1;
        }
    }
    if (changed) {
        word_t address = alloc_mem(tracee, message.msg_controllen);
        if (!address) { free(buffer); return -EFAULT; }
        status = write_data(tracee, address, buffer, message.msg_controllen);
        if (status >= 0) {
            message.msg_control = (void *)address;
            address = alloc_mem(tracee, sizeof(message));
            status = address ? write_data(tracee, address, &message, sizeof(message)) : -EFAULT;
            if (status >= 0) poke_reg(tracee, SYSARG_2, address);
        }
    }
    free(buffer);
    return status;
}

static int readonly(const char *path) {
    if (!readonly_paths) return 0;
    const char *start = readonly_paths;
    while (*start) {
        const char *end = strchr(start, '\n');
        size_t n = end ? (size_t)(end - start) : strlen(start);
        if (n && !strncmp(path, start, n) && (!path[n] || path[n] == '/')) return 1;
        if (!end) break;
        start = end + 1;
    }
    return 0;
}


static int inside(const char *path) {
    size_t n = strlen(root);
    return !strncmp(path, root, n) && path[n] == '/';
}

/* Resolve parents by descriptors so a concurrent symlink cannot escape the tree. */
static int parent_fd(const char *path, char name[NAME_MAX + 1]) {
    char relative[PATH_MAX];
    if (!inside(path)) return -EXDEV;
    snprintf(relative, sizeof(relative), "%s", path + strlen(root) + 1);
    char *last = strrchr(relative, '/');
    const char *base = last ? last + 1 : relative;
    if (!*base || strlen(base) > NAME_MAX || !strcmp(base, ".") || !strcmp(base, "..")) return -EINVAL;
    strcpy(name, base);
    if (last) *last = 0;
    int fd = open(root, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return -errno;
    if (last) {
        char *save, *part = strtok_r(relative, "/", &save);
        while (part) {
            if (!strcmp(part, ".") || !strcmp(part, "..")) { close(fd); return -EINVAL; }
            int next = openat(fd, part, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
            if (next < 0) { int error = errno; close(fd); return -error; }
            close(fd); fd = next; part = strtok_r(NULL, "/", &save);
        }
    }
    return fd;
}

/* Rare original hard-link groups retain aliasing; ordinary files never scan the tree. */
static int relink_aliases(const char *dir, const char *source, const struct stat *old) {
    DIR *stream = opendir(dir);
    if (!stream) return -errno;
    struct dirent *entry;
    int status = 0;
    while ((entry = readdir(stream))) {
        if (!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
        char path[PATH_MAX];
        if (snprintf(path, sizeof(path), "%s/%s", dir, entry->d_name) >= PATH_MAX) { status = -ENAMETOOLONG; break; }
        struct stat st;
        if (lstat(path, &st)) { if (errno == ENOENT) continue; status = -errno; break; }
        if (S_ISDIR(st.st_mode)) status = relink_aliases(path, source, old);
        else if (S_ISREG(st.st_mode) && st.st_dev == old->st_dev && st.st_ino == old->st_ino) {
            char name[NAME_MAX + 1], temp[64];
            int fd = parent_fd(path, name);
            if (fd < 0) { status = fd; break; }
            snprintf(temp, sizeof(temp), ".a0-cow-link-%ld", (long)getpid());
            if (linkat(AT_FDCWD, source, fd, temp, 0)) status = -errno;
            else if (renameat(fd, temp, fd, name)) { status = -errno; unlinkat(fd, temp, 0); }
            close(fd);
        }
        if (status < 0) break;
    }
    closedir(stream);
    return status;
}

static int materialize(const char *path) {
    if (!inside(path)) return 0;
    struct stat before;
    if (lstat(path, &before)) return errno == ENOENT ? 0 : -errno;
    if (!S_ISREG(before.st_mode) || before.st_uid == getuid()) return 0;
    char lockpath[PATH_MAX], name[NAME_MAX + 1], temp[80];
    snprintf(lockpath, sizeof(lockpath), "%s/lock", control);
    int lock = open(lockpath, O_RDWR | O_NOFOLLOW | O_CLOEXEC);
    if (lock < 0) return -errno;
    if (flock(lock, LOCK_EX)) { int error = errno; close(lock); return -error; }
    int parent = parent_fd(path, name), input = -1, output = -1, status = 0;
    temp[0] = 0;
    if (parent < 0) { status = parent; goto done; }
    input = openat(parent, name, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    if (input < 0) { status = -errno; goto done; }
    if (fstat(input, &before)) { status = -errno; goto done; }
    if (!S_ISREG(before.st_mode)) { status = -EINVAL; goto done; }
    if (before.st_uid == getuid()) goto done;
    snprintf(temp, sizeof(temp), ".a0-cow-%ld-%llu", (long)getpid(), (unsigned long long)before.st_ino);
    output = openat(parent, temp, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (output < 0) { status = -errno; temp[0] = 0; goto done; }
    char buffer[65536];
    ssize_t count;
    while ((count = read(input, buffer, sizeof(buffer))) != 0) {
        if (count < 0) { if (errno == EINTR) continue; status = -errno; goto done; }
        ssize_t at = 0;
        while (at < count) {
            ssize_t wrote = write(output, buffer + at, count - at);
            if (wrote < 0) { if (errno == EINTR) continue; status = -errno; goto done; }
            at += wrote;
        }
    }
    if (fchmod(output, before.st_mode & 0777)) { status = -errno; goto done; }
    /* User attributes belong to file data; host ACLs/capabilities do not. */
    ssize_t names_size = flistxattr(input, NULL, 0);
    if (names_size > 0) {
        char *names = malloc(names_size);
        if (!names) { status = -ENOMEM; goto done; }
        ssize_t size = flistxattr(input, names, names_size);
        if (size < 0) status = -errno;
        for (char *key = names; status == 0 && key < names + size; key += strlen(key) + 1) {
            if (strncmp(key, "user.", 5)) continue;
            ssize_t length = fgetxattr(input, key, NULL, 0);
            if (length < 0) { status = -errno; break; }
            void *value = malloc(length ? length : 1);
            if (!value) { status = -ENOMEM; break; }
            if (fgetxattr(input, key, value, length) != length || fsetxattr(output, key, value, length, 0)) status = -errno;
            free(value);
        }
        free(names);
        if (status < 0) goto done;
    } else if (names_size < 0 && errno != ENOTSUP) { status = -errno; goto done; }
    struct timespec times[2] = {before.st_atim, before.st_mtim};
    if (futimens(output, times)) { status = -errno; goto done; }
    struct stat current;
    if (fstatat(parent, name, &current, AT_SYMLINK_NOFOLLOW) || current.st_ino != before.st_ino || current.st_dev != before.st_dev) { status = -EAGAIN; goto done; }
    if (renameat(parent, temp, parent, name)) { status = -errno; goto done; }
    temp[0] = 0;
    char aliases[PATH_MAX];
    snprintf(aliases, sizeof(aliases), "%s/aliases/%llu-%llu", control,
             (unsigned long long)before.st_dev, (unsigned long long)before.st_ino);
    if (!access(aliases, F_OK)) status = relink_aliases(root, path, &before);
done:
    if (output >= 0) close(output);
    if (input >= 0) close(input);
    if (parent >= 0) { if (temp[0]) unlinkat(parent, temp, 0); close(parent); }
    close(lock);
    return status;
}

static int path_argument(Tracee *tracee, Reg argument, int copy) {
    char path[PATH_MAX];
    int status = get_sysarg_path(tracee, path, argument);
    if (status < 0) return status;
    if (readonly(path)) return -EROFS;
    return copy ? materialize(path) : 0;
}

/* Permission probes must describe copy-up without allocating a private copy. */
static int access_mode(Tracee *tracee, word_t number) {
    Reg path_arg = number == PR_access ? SYSARG_1 : SYSARG_2;
    Reg mode_arg = number == PR_access ? SYSARG_2 : SYSARG_3;
    word_t mode = peek_reg(tracee, CURRENT, mode_arg);
    if (!(mode & W_OK) || (mode & ~(R_OK | W_OK | X_OK))) return 0;
    if (number == PR_faccessat2 && (peek_reg(tracee, CURRENT, SYSARG_4) & ~AT_EACCESS)) return 0;
    char path[PATH_MAX], name[NAME_MAX + 1];
    int status = get_sysarg_path(tracee, path, path_arg);
    if (status < 0) return status;
    if (readonly(path)) return -EROFS;
    struct stat info;
    if (!inside(path) || lstat(path, &info) || !S_ISREG(info.st_mode)
        || info.st_uid == getuid() || !(info.st_mode & S_IWUSR) || access(path, R_OK)) return 0;
    int parent = parent_fd(path, name);
    if (parent < 0) return 0;
    int writable = faccessat(parent, ".", W_OK | X_OK, 0) == 0;
    close(parent);
    /* The kernel still checks existence, traversal, read/execute bits and flags. */
    if (writable) poke_reg(tracee, mode_arg, mode & ~W_OK);
    return 0;
}

static int descriptor(Tracee *tracee, word_t number) {
    char link[80], path[PATH_MAX];
    struct stat opened, current;
    snprintf(link, sizeof(link), "/proc/%ld/fd/%ld", (long)tracee->pid,
             (long)peek_reg(tracee, ORIGINAL, SYSARG_1));
    ssize_t length = readlink(link, path, sizeof(path) - 1);
    if (length < 0) return 0; /* Let the kernel report EBADF. */
    path[length] = 0;
    if (readonly(path)) return -EROFS;
    if (!inside(path) || stat(link, &opened) || !S_ISREG(opened.st_mode) || opened.st_uid == getuid()) return 0;
    /* A lower FD is read-only: ftruncate must retain its normal kernel error. */
    if (number == PR_ftruncate || number == PR_ftruncate64) return 0;
    /* shortcut: deleted/replaced lower descriptors retain their old inode, as after overlay copy-up. */
    if (lstat(path, &current) || current.st_ino != opened.st_ino || current.st_dev != opened.st_dev) return -ESTALE;
    int status = materialize(path);
    if (status < 0) return status;
    word_t a = peek_reg(tracee, CURRENT, SYSARG_2), b = peek_reg(tracee, CURRENT, SYSARG_3);
    if (number == PR_fchmod) {
        set_sysnum(tracee, PR_fchmodat);
        poke_reg(tracee, SYSARG_1, AT_FDCWD);
        poke_reg(tracee, SYSARG_3, a);
        return set_sysarg_path(tracee, path, SYSARG_2);
    }
    if (number == PR_fchown || number == PR_fchown32) {
        set_sysnum(tracee, PR_fchownat);
        poke_reg(tracee, SYSARG_1, AT_FDCWD);
        poke_reg(tracee, SYSARG_3, a); poke_reg(tracee, SYSARG_4, b); poke_reg(tracee, SYSARG_5, 0);
        return set_sysarg_path(tracee, path, SYSARG_2);
    }
    if (number == PR_utimensat || number == PR_utimensat_time64 || number == PR_futimesat) {
        poke_reg(tracee, SYSARG_1, AT_FDCWD);
        return set_sysarg_path(tracee, path, SYSARG_2);
    }
    set_sysnum(tracee, number == PR_fsetxattr ? PR_setxattr : PR_removexattr);
    return set_sysarg_path(tracee, path, SYSARG_1);
}

int cow_callback(Extension *extension, ExtensionEvent event, intptr_t data1, intptr_t data2) {
    (void)data2;
    if (event == INITIALIZATION) {
        root = getenv("A0_COW_ROOT"); control = getenv("A0_COW_CONTROL");
        readonly_paths = getenv("A0_READONLY_PATHS");
        if (!root || !control || getuid() == 0) return -EINVAL;
        static const FilteredSysnum calls[] = {
            {PR_sendmsg, FILTER_SYSEXIT},
            {PR_access, FILTER_SYSEXIT}, {PR_faccessat, FILTER_SYSEXIT}, {PR_faccessat2, FILTER_SYSEXIT},
            {PR_fchmod, FILTER_SYSEXIT}, {PR_fchown, FILTER_SYSEXIT}, {PR_fchown32, FILTER_SYSEXIT},
            {PR_ftruncate, FILTER_SYSEXIT}, {PR_ftruncate64, FILTER_SYSEXIT},
            {PR_fsetxattr, FILTER_SYSEXIT}, {PR_fremovexattr, FILTER_SYSEXIT}, FILTERED_SYSNUM_END
        };
        extension->filtered_sysnums = calls;
        return 0;
    }
    if (event != SYSCALL_ENTER_END || data1 < 0) return 0;
    Tracee *tracee = TRACEE(extension);
    Reg argument = SYSARG_1;
    word_t number = get_sysnum(tracee, ORIGINAL);
    int copy = 1, status;
    switch (number) {
    case PR_sendmsg: return send_credentials(tracee);
    case PR_access: case PR_faccessat: case PR_faccessat2: return access_mode(tracee, number);
    case PR_open:
        if (!(peek_reg(tracee, ORIGINAL, SYSARG_2) & (O_WRONLY | O_RDWR | O_TRUNC | O_CREAT))) return 0;
        break;
    case PR_openat:
        if (!(peek_reg(tracee, ORIGINAL, SYSARG_3) & (O_WRONLY | O_RDWR | O_TRUNC | O_CREAT))) return 0;
        argument = SYSARG_2; break;
    case PR_creat: case PR_truncate: case PR_truncate64: case PR_chmod: case PR_chown: case PR_chown32:
    case PR_lchown: case PR_lchown32: case PR_utime: case PR_utimes:
    case PR_setxattr: case PR_lsetxattr: case PR_removexattr: case PR_lremovexattr:
        break;
    case PR_fchmodat: case PR_fchmodat2: case PR_fchownat: case PR_utimensat: case PR_utimensat_time64: case PR_futimesat:
        if (!peek_reg(tracee, ORIGINAL, SYSARG_2)) {
            return descriptor(tracee, number);
        }
        argument = SYSARG_2; break;
    case PR_unlink: case PR_rmdir: case PR_mkdir: case PR_mknod:
        copy = 0; break;
    case PR_unlinkat: case PR_mkdirat: case PR_mknodat:
        argument = SYSARG_2; copy = 0; break;
    case PR_symlink:
        argument = SYSARG_2; copy = 0; break;
    case PR_symlinkat:
        argument = SYSARG_3; copy = 0; break;
    case PR_rename: case PR_link:
        status = path_argument(tracee, SYSARG_2, 0);
        if (status < 0) return status;
        copy = number == PR_link; break;
    case PR_renameat: case PR_renameat2: case PR_linkat:
        status = path_argument(tracee, SYSARG_4, 0);
        if (status < 0) return status;
        argument = SYSARG_2; copy = number == PR_linkat; break;
    case PR_fchmod: case PR_fchown: case PR_fchown32: case PR_ftruncate: case PR_ftruncate64:
    case PR_fsetxattr: case PR_fremovexattr:
        return descriptor(tracee, number);
    default: return 0;
    }
    return path_argument(tracee, argument, copy);
}
