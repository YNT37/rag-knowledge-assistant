from pathlib import Path, PureWindowsPath


INVALID_CHARS = set('<>:"/\\|?*')
RESERVED_CATEGORY_NAMES = {"未分类", "全部资料"}


def normalize_category_name(name: str) -> str:
    name = name.strip()
    if not 1 <= len(name) <= 20:
        raise ValueError("分类名须为1—20个字符")
    if name in RESERVED_CATEGORY_NAMES:
        raise ValueError("不能使用保留分类名")
    if any(char in INVALID_CHARS or ord(char) < 32 for char in name):
        raise ValueError("分类名不能含路径或无效字符")
    return name


def normalize_source(source: str) -> str:
    source = source.strip()
    if not 1 <= len(source) <= 100 or not source.endswith(".md"):
        raise ValueError("文件名须在100字符内并以小写.md结尾")
    if any(char in INVALID_CHARS or ord(char) < 32 for char in source):
        raise ValueError("只允许文件名，不能包含路径或无效字符")
    if PureWindowsPath(source).is_reserved():
        raise ValueError("不能使用Windows保留设备名")
    return source


def get_document_path(directory_path: Path, source: str) -> Path:
    if normalize_source(source) != source:
        raise ValueError("已登记文件名存在异常空白")
    if directory_path.is_symlink() or directory_path.is_junction():
        raise ValueError("正文根目录不能是链接")

    root = directory_path.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("正文根目录不可用")

    path = root / source
    if path.is_symlink() or path.is_junction():
        raise ValueError("正文不能是链接")
    if path.resolve(strict=False).parent != root:
        raise ValueError("文件超出正文根目录")
    return path
