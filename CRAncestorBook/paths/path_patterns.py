# paths/path_patterns.py
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Chapter paths
def chapter_output(filename: str, ext: str = ".txt") -> str:
    if ext not in (".txt", ".md", ".json"):
        raise ValueError(f"Unsupported ext: {ext}")
    if filename.endswith((".txt", ".md", ".json")):
        raise ValueError(f"filename must be a stem, not include an extension: {filename}")
    return f"Chapters/Chapter_{{N}}/{filename}{ext}"


def chapter_output_md(filename: str) -> str:
    return f"Chapters/Chapter_{{N}}/{filename}.md"

def chapter_payload(code: str) -> str:
    return f"Ledger/payloads/Chapter_{{N}}_{code}_payload.txt"

def chapter_glob(stem: str, ext: str = ".txt") -> str:
    if ext not in (".txt", ".md", ".json"):
        raise ValueError(f"Unsupported ext: {ext}")
    if stem.endswith((".txt", ".md", ".json")):
        raise ValueError(f"stem must not include extension: {stem}")
    return f"Chapters/Chapter_*/{stem}{ext}"


def chapter_path(root: Path, chapter_n: int, stem: str, ext: str = ".txt") -> Path:
    return root / chapter_output(stem, ext=ext).format(N=chapter_n)

# TOC paths
def planning_output(filename: str) -> str:
    return f"Planning/{filename}"

def planning_payload(code: str) -> str:
    return f"Planning/payloads/{code}_payload.txt"

def planning_path(self, filename: str) -> Path:
    return self.planning_dir / filename


# Global paths
def global_output(filename: str) -> str:
    return f"Ledger/{filename}.txt"

def global_payload(code: str) -> str:
    return f"Ledger/payloads/{code}_payload.txt"

def global_path(root:Path, stem:str) -> Path:
    return root / global_output(stem)


