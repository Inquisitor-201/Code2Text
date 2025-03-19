import os
import argparse

def is_text_file(file_path, chunk_size=1024):
    """检测文件是否为文本格式"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            if not chunk:
                return True  # 空文件视为文本
            
            # 检查二进制特征：空字节
            if b'\x00' in chunk:
                return False
            
            # 统计可打印字符比例
            text_chars = bytearray(
                {7, 8, 9, 10, 12, 13, 27} |  # 控制字符
                set(range(0x20, 0x7F)) |     # 可打印ASCII
                set(range(0x80, 0x100))      # 扩展ASCII（Latin-1）
            )
            non_text = sum(1 for byte in chunk if byte not in text_chars)
            return (non_text / len(chunk)) < 0.3  # 非文本字符占比阈值
    except Exception:
        return False

def save_project_to_txt(project_path, output_file, 
                        exclude_dirs=None, exclude_exts=None, 
                        include_exts=None, skip_hidden=True,
                        verbose=False, max_lines=None):
    """
    将项目目录结构及文件内容保存到单个文本文件
    
    :param project_path: 项目根目录路径
    :param output_file: 输出文件路径
    :param exclude_dirs: 要排除的目录列表
    :param exclude_exts: 要排除的文件扩展名列表
    :param include_exts: 要包含的文件扩展名列表（覆盖排除规则）
    :param skip_hidden: 是否跳过隐藏文件/目录
    :param verbose: 是否显示详细处理过程
    :param max_lines: 最大保留行数（None表示不限制）
    """
    # 参数默认值处理
    exclude_dirs = set([d.lower() for d in (exclude_dirs or [])])
    exclude_exts = set([e.lower() for e in (exclude_exts or [])])
    include_exts = set([e.lower() for e in (include_exts or [])])
    
    # 添加常见需要排除的目录和文件类型
    default_exclude_dirs = {'.git', '__pycache__', 'venv', 'node_modules'}
    default_exclude_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', 
                           '.ico', '.svg', '.pdf', '.zip', '.tar.gz', 
                           '.o', '.d', '.bin'}
    
    exclude_dirs |= default_exclude_dirs
    exclude_exts |= default_exclude_exts

    project_path = os.path.abspath(project_path)

    with open(output_file, 'w', encoding='utf-8') as out_f:
        for root, dirs, files in os.walk(project_path, topdown=True):
            # 过滤目录（直接修改dirs列表）
            dirs[:] = [d for d in dirs 
                      if not (d.lower() in exclude_dirs or 
                             (skip_hidden and d.startswith('.')))]

            # 处理文件过滤
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, project_path)

                # 跳过隐藏文件
                if skip_hidden and filename.startswith('.'):
                    continue

                # 处理文件扩展名
                file_ext = os.path.splitext(filename)[1].lower()
                if include_exts:
                    if file_ext not in include_exts:
                        continue
                elif file_ext in exclude_exts:
                    continue

                # 文本文件检测
                if not is_text_file(file_path):
                    if verbose:
                        print(f"🚫 跳过非文本文件: {rel_path}")
                    continue

                # 显示读取进度
                if verbose:
                    print(f"📖 正在读取: {rel_path}")

                # 尝试读取文件内容
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read().decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('latin-1')
                    except Exception as e:
                        if verbose:
                            print(f"⚠️ 无法解码文件 {rel_path} ({e})")
                        continue
                except Exception as e:
                    if verbose:
                        print(f"⛔ 读取文件 {rel_path} 失败 ({e})")
                    continue

                # 行数限制处理
                if max_lines is not None:
                    lines = content.splitlines()
                    original_line_count = len(lines)
                    
                    if original_line_count > max_lines:
                        content = '\n'.join(lines[:max_lines])
                        if verbose:
                            print(f"✂️ 截断文件 {rel_path} ({original_line_count} → {max_lines} 行)")

                # 写入输出文件
                out_f.write(f"// FILE: {rel_path}\n")
                out_f.write(f"{content}\n\n")
                out_f.write("//" + "="*78 + "\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将项目文件导出为LLM友好的文本格式")
    parser.add_argument("-i", required=True, help="项目根目录路径")
    parser.add_argument("-o", required=True, help="输出文件路径")
    parser.add_argument("--exclude_dirs", nargs="*", help="要排除的目录列表")
    parser.add_argument("--exclude_exts", nargs="*", help="要排除的文件扩展名列表")
    parser.add_argument("--include_exts", nargs="*", help="要包含的文件扩展名列表（覆盖排除规则）")
    parser.add_argument("--show_hidden", action="store_false", dest="skip_hidden",
                      help="包含隐藏文件/目录")
    parser.add_argument("-v", "--verbose", action="store_true",
                      help="显示详细处理过程")
    parser.add_argument("--max_lines", type=int, default=20000,
                        help="单个文件最大保留行数（默认20000行）")

    args = parser.parse_args()

    save_project_to_txt(
        args.i,
        args.o,
        exclude_dirs=args.exclude_dirs,
        exclude_exts=args.exclude_exts,
        include_exts=args.include_exts,
        skip_hidden=args.skip_hidden,
        verbose=args.verbose,
        max_lines=args.max_lines
    )