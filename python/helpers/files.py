from abc import ABC, abstractmethod
from fnmatch import fnmatch
import json
from ntpath import isabs
import os
import sys
import re
import base64
import shutil
import tempfile
from typing import Any, Literal
import zipfile
import importlib
import importlib.util
import inspect
import glob
import mimetypes
from simpleeval import simple_eval


class VariablesPlugin(ABC):
    @abstractmethod
    def get_variables(self, file: str, backup_dirs: list[str] | None = None, **kwargs) -> dict[str, Any]:  # type: ignore
        pass


def load_plugin_variables(
    file: str, backup_dirs: list[str] | None = None, **kwargs
) -> dict[str, Any]:
    if not file.endswith(".md"):
        return {}

    if backup_dirs is None:
        backup_dirs = []

    try:
        # Create filename and directories list
        plugin_filename = basename(file, ".md") + ".py"
        directories = [dirname(file)] + backup_dirs
        plugin_file = find_file_in_dirs(plugin_filename, directories)
    except FileNotFoundError:
        plugin_file = None

    if plugin_file and exists(plugin_file):

        from python.helpers import extract_tools

        classes = extract_tools.load_classes_from_file(
            plugin_file, VariablesPlugin, one_per_file=False
        )
        for cls in classes:
            return cls().get_variables(file, backup_dirs, **kwargs)  # type: ignore < abstract class here is ok, it is always a subclass

        # load python code and extract variables variables from it
        # module = None
        # module_name = dirname(plugin_file).replace("/", ".") + "." + basename(plugin_file, '.py')

        # try:
        #     spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        #     if not spec:
        #         return {}
        #     module = importlib.util.module_from_spec(spec)
        #     sys.modules[spec.name] = module
        #     spec.loader.exec_module(module)  # type: ignore
        # except ImportError:
        #     return {}

        # if module is None:
        #     return {}

        # # Get all classes in the module
        # class_list = inspect.getmembers(module, inspect.isclass)
        # # Filter for classes that are subclasses of VariablesPlugin
        # # iterate backwards to skip imported superclasses
        # for cls in reversed(class_list):
        #     if cls[1] is not VariablesPlugin and issubclass(cls[1], VariablesPlugin):
        #         return cls[1]().get_variables()  # type: ignore
    return {}


from python.helpers.strings import sanitize_string


def parse_file(
    _filename: str, _directories: list[str] | None = None, _encoding="utf-8", **kwargs
):
    if _directories is None:
        _directories = []

    # Find the file in the directories
    absolute_path = find_file_in_dirs(_filename, _directories)

    # Read the file content
    with open(absolute_path, "r", encoding=_encoding) as f:
        # content = remove_code_fences(f.read())
        content = f.read()

    is_json = is_full_json_template(content)
    content = remove_code_fences(content)
    variables = load_plugin_variables(absolute_path, _directories, **kwargs) or {}  # type: ignore
    variables.update(kwargs)
    if is_json:
        content = replace_placeholders_json(content, **variables)
        obj = json.loads(content)
        # obj = replace_placeholders_dict(obj, **variables)
        return obj
    else:
        content = replace_placeholders_text(content, **variables)
        # Process include statements
        content = process_includes(
            # here we use kwargs, the plugin variables are not inherited
            content,
            _directories,
            **kwargs,
        )
        return content


def read_prompt_file(
    _file: str, _directories: list[str] | None = None, _encoding="utf-8", **kwargs
):
    if _directories is None:
        _directories = []

    # If filename contains folder path, extract it and add to directories
    if os.path.dirname(_file):
        folder_path = os.path.dirname(_file)
        _file = os.path.basename(_file)
        _directories = [folder_path] + _directories

    # Find the file in the directories
    absolute_path = find_file_in_dirs(_file, _directories)

    # Read the file content
    with open(absolute_path, "r", encoding=_encoding) as f:
        # content = remove_code_fences(f.read())
        content = f.read()

    variables = load_plugin_variables(_file, _directories, **kwargs) or {}  # type: ignore
    variables.update(kwargs)

    # evaluate conditions
    content = evaluate_text_conditions(content, **variables)

    # Replace placeholders with values from kwargs
    content = replace_placeholders_text(content, **variables)

    # Process include statements
    content = process_includes(
        # here we use kwargs, the plugin variables are not inherited
        content,
        _directories,
        **kwargs,
    )

    return content


def evaluate_text_conditions(_content: str, **kwargs):
    # search for {{if ...}} ... {{endif}} blocks and evaluate conditions with nesting support
    if_pattern = re.compile(r"{{\s*if\s+(.*?)}}", flags=re.DOTALL)
    token_pattern = re.compile(r"{{\s*(if\b.*?|endif)\s*}}", flags=re.DOTALL)

    def _process(text: str) -> str:
        m_if = if_pattern.search(text)
        if not m_if:
            return text

        depth = 1
        pos = m_if.end()
        while True:
            m = token_pattern.search(text, pos)
            if not m:
                # Unterminated if-block, do not modify text
                return text
            token = m.group(1)
            depth += 1 if token.startswith("if ") else -1
            if depth == 0:
                break
            pos = m.end()

        before = text[: m_if.start()]
        condition = m_if.group(1).strip()
        inner = text[m_if.end() : m.start()]
        after = text[m.end() :]

        try:
            result = simple_eval(condition, names=kwargs)
        except Exception:
            # On evaluation error, do not modify this block
            return text

        if result:
            # Keep inner content (processed recursively), remove if/endif markers
            kept = before + _process(inner)
        else:
            # Skip entire block, including inner content and markers
            kept = before

        # Continue processing the remaining text after this block
        return kept + _process(after)

    return _process(_content)


def read_file(relative_path: str, encoding="utf-8"):
    # Try to get the absolute path for the file from the original directory or backup directories
    absolute_path = get_abs_path(relative_path)

    # Read the file content
    with open(absolute_path, "r", encoding=encoding) as f:
        return f.read()


def read_file_bin(relative_path: str):
    # Try to get the absolute path for the file from the original directory or backup directories
    absolute_path = get_abs_path(relative_path)

    # read binary content
    with open(absolute_path, "rb") as f:
        return f.read()


def read_file_base64(relative_path):
    # get absolute path
    absolute_path = get_abs_path(relative_path)

    # read binary content and encode to base64
    with open(absolute_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def is_probably_binary_bytes(data: bytes, threshold: float = 0.3) -> bool:
    """
    Binary detection.

    - Fast path: NUL bytes => binary
    - Otherwise: treat high ratio of suspicious ASCII control bytes as binary.
      (We intentionally do NOT treat bytes >= 0x80 as binary to avoid false
      positives for UTF-8 text.)
    """
    if not data:
        return False
    if b"\x00" in data:
        return True

    # Count suspicious control bytes
    allowed = {8, 9, 10, 12, 13}  # \b \t \n \f \r
    suspicious = sum(
        1
        for b in data
        if ((b < 32 and b not in allowed) or b == 127)
    )
    return (suspicious / len(data)) > threshold


def is_probably_binary_file(
    file_path: str, sample_size: int = 10 * 1024, threshold: float = 0.3
) -> bool:
    """Binary detection by reading only the first ~sample_size bytes of a file."""
    try:
        with open(file_path, "rb") as f:
            sample = f.read(sample_size)
    except (FileNotFoundError, PermissionError, OSError):
        raise OSError(f"Unable to read file for binary detection: {file_path}")
    return is_probably_binary_bytes(sample, threshold=threshold)


def replace_placeholders_text(_content: str, **kwargs):
    # Replace placeholders with values from kwargs
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        strval = str(value)
        _content = _content.replace(placeholder, strval)
    return _content


def replace_placeholders_json(_content: str, **kwargs):
    # Replace placeholders with values from kwargs
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        if placeholder in _content:
            strval = json.dumps(value)
            _content = _content.replace(placeholder, strval)
    return _content


def replace_placeholders_dict(_content: dict, **kwargs):
    def replace_value(value):
        if isinstance(value, str):
            placeholders = re.findall(r"{{(\w+)}}", value)
            if placeholders:
                for placeholder in placeholders:
                    if placeholder in kwargs:
                        replacement = kwargs[placeholder]
                        if value == f"{{{{{placeholder}}}}}":
                            return replacement
                        elif isinstance(replacement, (dict, list)):
                            value = value.replace(
                                f"{{{{{placeholder}}}}}", json.dumps(replacement)
                            )
                        else:
                            value = value.replace(
                                f"{{{{{placeholder}}}}}", str(replacement)
                            )
            return value
        elif isinstance(value, dict):
            return {k: replace_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [replace_value(item) for item in value]
        else:
            return value

    return replace_value(_content)


def process_includes(_content: str, _directories: list[str], **kwargs):
    # Regex to find {{ include 'path' }} or {{include'path'}}
    include_pattern = re.compile(r"{{\s*include\s*['\"](.*?)['\"]\s*}}")

    def replace_include(match):
        include_path = match.group(1)
        # if the path is absolute, do not process it
        if os.path.isabs(include_path):
            return match.group(0)
        # Search for the include file in the directories
        try:
            included_content = read_prompt_file(include_path, _directories, **kwargs)
            return included_content
        except FileNotFoundError:
            return match.group(0)  # Return original if file not found

    # Replace all includes with the file content
    return re.sub(include_pattern, replace_include, _content)


def find_file_in_dirs(_filename: str, _directories: list[str]):
    """
    This function searches for a filename in a list of directories in order.
    Returns the absolute path of the first found file.
    """
    # Loop through the directories in order
    for directory in _directories:
        # Create full path
        full_path = get_abs_path(directory, _filename)
        if exists(full_path):
            return full_path

    # If the file is not found, raise FileNotFoundError
    raise FileNotFoundError(
        f"File '{_filename}' not found in any of the provided directories."
    )


def get_unique_filenames_in_dirs(dir_paths: list[str], pattern: str = "*", type: Literal["file", "dir", "any"] = "file"):
    # returns absolute paths for unique filenames, priority by order in dir_paths
    seen = set()
    result = []
    for dir_path in dir_paths:
        full_dir = get_abs_path(dir_path)
        for file_path in glob.glob(os.path.join(full_dir, pattern)):
            fname = os.path.basename(file_path)
            if fname not in seen and (type == "any" or (type == "file" and os.path.isfile(file_path)) or (type == "dir" and os.path.isdir(file_path))):
                seen.add(fname)
                result.append(get_abs_path(file_path))
    # sort by filename (basename), not the full path
    result.sort(key=lambda path: os.path.basename(path))
    return result


def find_existing_paths_by_pattern(pattern: str):
    if not pattern:
        return []

    search_pattern = get_abs_path(pattern)
    matches = glob.glob(search_pattern, recursive=True)
    matches.sort()
    return matches


def remove_code_fences(text):
    # Pattern to match code fences with optional language specifier
    pattern = r"(```|~~~)(.*?\n)(.*?)(\1)"

    # Function to replace the code fences
    def replacer(match):
        return match.group(3)  # Return the code without fences

    # Use re.DOTALL to make '.' match newlines
    result = re.sub(pattern, replacer, text, flags=re.DOTALL)

    return result


def is_full_json_template(text):
    # Pattern to match the entire text enclosed in ```json or ~~~json fences
    pattern = r"^\s*(```|~~~)\s*json\s*\n(.*?)\n\1\s*$"
    # Use re.DOTALL to make '.' match newlines
    match = re.fullmatch(pattern, text.strip(), flags=re.DOTALL)
    return bool(match)


def write_file(relative_path: str, content: str, encoding: str = "utf-8"):
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    content = sanitize_string(content, encoding)
    with open(abs_path, "w", encoding=encoding) as f:
        f.write(content)


def write_file_bin(relative_path: str, content: bytes):
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)


def write_file_base64(relative_path: str, content: str):
    # decode base64 string to bytes
    data = base64.b64decode(content)
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(data)


def delete_dir(relative_path: str):
    # ensure deletion of directory without propagating errors
    abs_path = get_abs_path(relative_path)
    if os.path.exists(abs_path):
        # first try with ignore_errors=True which is the safest option
        shutil.rmtree(abs_path, ignore_errors=True)

        # if directory still exists, try more aggressive methods
        if os.path.exists(abs_path):
            try:
                # try to change permissions and delete again
                for root, dirs, files in os.walk(abs_path, topdown=False):
                    for name in files:
                        file_path = os.path.join(root, name)
                        os.chmod(file_path, 0o777)
                    for name in dirs:
                        dir_path = os.path.join(root, name)
                        os.chmod(dir_path, 0o777)

                # try again after changing permissions
                shutil.rmtree(abs_path, ignore_errors=True)
            except:
                # suppress all errors - we're ensuring no errors propagate
                pass


def move_dir(old_path: str, new_path: str):
    # rename/move the directory from old_path to new_path (both relative)
    abs_old = get_abs_path(old_path)
    abs_new = get_abs_path(new_path)
    if not os.path.isdir(abs_old):
        return  # nothing to rename
    
    # ensure parent directory exists
    os.makedirs(os.path.dirname(abs_new), exist_ok=True)
    
    try:
        os.rename(abs_old, abs_new)
    except Exception:
        pass  # suppress all errors, keep behavior consistent


# move dir safely, remove with number if needed
def move_dir_safe(src, dst, rename_format="{name}_{number}"):
    base_dst = dst
    i = 2
    while exists(dst):
        dst = rename_format.format(name=base_dst, number=i)
        i += 1
    move_dir(src, dst)
    return dst


# create dir safely, add number if needed
def create_dir_safe(dst, rename_format="{name}_{number}"):
    base_dst = dst
    i = 2
    while exists(dst):
        dst = rename_format.format(name=base_dst, number=i)
        i += 1
    create_dir(dst)
    return dst


def create_dir(relative_path: str):
    abs_path = get_abs_path(relative_path)
    os.makedirs(abs_path, exist_ok=True)


def list_files(relative_path: str, filter: str = "*"):
    abs_path = get_abs_path(relative_path)
    if not os.path.exists(abs_path):
        return []
    return [file for file in os.listdir(abs_path) if fnmatch(file, filter)]


def make_dirs(relative_path: str):
    abs_path = get_abs_path(relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)


def get_abs_path(*relative_paths):
    "Convert relative paths to absolute paths based on the base directory."
    return os.path.join(get_base_dir(), *relative_paths)


def deabsolute_path(path: str):
    "Convert absolute paths to relative paths based on the base directory."
    return os.path.relpath(path, get_base_dir())


def fix_dev_path(path: str):
    "On dev environment, convert /a0/... paths to local absolute paths"
    from python.helpers.runtime import is_development

    if is_development():
        if path.startswith("/a0/"):
            path = path.replace("/a0/", "")
    return get_abs_path(path)


def normalize_a0_path(path: str):
    "Convert absolute paths into /a0/... paths"
    if is_in_base_dir(path):
        deabs = deabsolute_path(path)
        return "/a0/" + deabs
    return path


def exists(*relative_paths):
    path = get_abs_path(*relative_paths)
    return os.path.exists(path)


def get_base_dir():
    # Get the base directory from the current file path
    base_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, "../../")))
    return base_dir


def basename(path: str, suffix: str | None = None):
    if suffix:
        return os.path.basename(path).removesuffix(suffix)
    return os.path.basename(path)


def dirname(path: str):
    return os.path.dirname(path)


def is_in_base_dir(path: str):
    return is_in_dir(path,get_base_dir())


def is_in_dir(path:str,dir:str):
    # check if the given path is within the directory
    abs_path = os.path.abspath(path)
    abs_dir = os.path.abspath(dir)
    return os.path.commonpath([abs_path, abs_dir]) == abs_dir


def get_subdirectories(
    relative_path: str,
    include: str | list[str] = "*",
    exclude: str | list[str] | None = None,
):
    abs_path = get_abs_path(relative_path)
    if not os.path.exists(abs_path):
        return []
    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]
    return [
        subdir
        for subdir in os.listdir(abs_path)
        if os.path.isdir(os.path.join(abs_path, subdir))
        and any(fnmatch(subdir, inc) for inc in include)
        and (exclude is None or not any(fnmatch(subdir, exc) for exc in exclude))
    ]


def zip_dir(dir_path: str):
    full_path = get_abs_path(dir_path)
    zip_file_path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False).name
    base_name = os.path.basename(full_path)
    with zipfile.ZipFile(zip_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zip:
        for root, _, files in os.walk(full_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, full_path)
                zip.write(file_path, os.path.join(base_name, rel_path))
    return zip_file_path


def move_file(relative_path: str, new_path: str):
    abs_path = get_abs_path(relative_path)
    new_abs_path = get_abs_path(new_path)
    os.makedirs(os.path.dirname(new_abs_path), exist_ok=True)
    os.rename(abs_path, new_abs_path)


def safe_file_name(filename: str) -> str:
    # Replace any character that's not alphanumeric, dash, underscore, or dot with underscore
    return re.sub(r"[^a-zA-Z0-9-._]", "_", filename)


def read_text_files_in_dir(
    dir_path: str, max_size: int = 1024 * 1024, pattern: str = "*"
) -> dict[str, str]:

    abs_path = get_abs_path(dir_path)
    if not os.path.exists(abs_path):
        return {}
    result = {}
    for file_path in [os.path.join(abs_path, f) for f in os.listdir(abs_path)]:
        try:
            if not os.path.isfile(file_path):
                continue
            if not fnmatch(os.path.basename(file_path), pattern):
                continue
            if max_size > 0 and os.path.getsize(file_path) > max_size:
                continue
            mime, _ = mimetypes.guess_type(file_path)
            if mime is not None and not mime.startswith("text"):
                continue
            # Check if file is binary by reading a small chunk
            content = read_file(file_path)
            result[os.path.basename(file_path)] = content
        except Exception:
            continue
    return result

def list_files_in_dir_recursively(relative_path: str) -> list[str]:
    abs_path = get_abs_path(relative_path)
    if not os.path.exists(abs_path):
        return []
    result = []
    for root, dirs, files in os.walk(abs_path):
        for file in files:
            file_path = os.path.join(root, file)
            # Return relative path from the base directory
            rel_path = os.path.relpath(file_path, abs_path)
            result.append(rel_path)
    return result
    