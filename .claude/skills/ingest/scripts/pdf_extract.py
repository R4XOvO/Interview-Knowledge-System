#!/usr/bin/env python3
"""
PDF 文本提取工具

封装 pdftotext CLI (poppler-utils) 调用。
将 PDF 转换为纯文本以节省 Token（避免 Read 直接读取 PDF 导致图片渲染）。

用法:
    python pdf_extract.py <input.pdf> <output.txt>

要求:
    pdftotext 已安装（macOS: brew install poppler, Linux: apt-get install poppler-utils, Windows: choco install poppler）

完整规格见 DEV_SPEC 8.1.1
"""

import shutil
import subprocess
import sys
from pathlib import Path


def extract_pdf(input_path: str, output_path: str | None = None) -> str:
    """
    将 PDF 提取为纯文本

    Args:
        input_path: 输入 PDF 文件路径
        output_path: 输出 txt 路径，若为 None 则返回文本内容

    Returns:
        若 output_path 为 None，返回提取的文本内容；否则返回输出路径

    Raises:
        RuntimeError: pdftotext 未安装或提取失败
    """
    pdf_path = Path(input_path).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # 检查 pdftotext 是否可用
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError(
            "pdftotext not found. Please install poppler-utils:\n"
            "  macOS: brew install poppler\n"
            "  Linux: apt-get install poppler-utils\n"
            "  Windows: choco install poppler"
        )

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [pdftotext, "-layout", str(pdf_path), str(out)],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftotext failed: {result.stderr}")
        return str(out)
    else:
        # 输出到 stdout 并捕获
        result = subprocess.run(
            [pdftotext, "-layout", "-", str(pdf_path)],
            capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftotext failed: {result.stderr}")
        return result.stdout


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_extract.py <input.pdf> [output.txt]", file=sys.stderr)
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        result = extract_pdf(inp, out)
        if out:
            print(f"[OK] Extracted to {result}")
        else:
            print(result)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
