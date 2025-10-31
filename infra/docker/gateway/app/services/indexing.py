import re
import logging
import time
from typing import List, Dict, Any
from pathlib import Path
import ast

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing repositories into Qdrant"""

    def __init__(self):
        self.supported_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".rb",
            ".php",
            ".md",
            ".txt",
            ".rst",
            ".adoc",
            ".yml",
            ".yaml",
            ".json",
            ".toml",
            ".cfg",
            ".ini",
            ".conf",
            ".sh",
            ".bat",
            ".ps1",
        }

        # Patterns to exclude
        self.exclude_patterns = [
            ".*",
            "__pycache__",
            "node_modules",
            ".git",
            "target",
            "build",
            "dist",
            "out",
            ".vscode",
            ".idea",
            "*.min.js",
            "*.min.css",
            "package-lock.json",
            "yarn.lock",
            "*.pyc",
            "*.pyo",
            "*.pyd",
        ]

    def is_indexable_file(self, file_path: Path) -> bool:
        """Check if file should be indexed"""
        # Skip directories
        if file_path.is_dir():
            return False

        # Check extension
        if file_path.suffix.lower() not in self.supported_extensions:
            return False

        # Check exclude patterns
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern in file_str or file_path.match(pattern):
                return False

        # Check file size (skip very large files > 1MB)
        try:
            if file_path.stat().st_size > 1024 * 1024:
                return False
        except OSError:
            return False

        return True

    def discover_files(
        self,
        repo_path: str,
        file_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ) -> List[Path]:
        """Discover indexable files in repository"""
        repo = Path(repo_path)
        if not repo.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        files = []

        # Custom file patterns
        include_patterns = file_patterns or ["**/*"]
        exclude_patterns = exclude_patterns or self.exclude_patterns

        for pattern in include_patterns:
            for file_path in repo.glob(pattern):
                if self.is_indexable_file(file_path):
                    # Check custom exclude patterns
                    should_exclude = False
                    file_str = str(file_path)
                    for excl_pattern in exclude_patterns:
                        if excl_pattern in file_str or file_path.match(excl_pattern):
                            should_exclude = True
                            break

                    if not should_exclude:
                        files.append(file_path)

        logger.info(f"Discovered {len(files)} indexable files in {repo_path}")
        return files

    def chunk_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Chunk a file into manageable pieces"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return []

        if not content.strip():
            return []

        # Get relative path from repo root
        relative_path = str(
            file_path.relative_to(
                file_path.parents[-2]
                if len(file_path.parents) > 1
                else file_path.parent
            )
        )
        file_ext = file_path.suffix.lower()

        # Different chunking strategies based on file type
        if file_ext in [
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rs",
            ".swift",
            ".kt",
            ".scala",
            ".rb",
            ".php",
        ]:
            return self._chunk_code_file(content, relative_path, file_path)
        elif file_ext in [".md", ".txt", ".rst", ".adoc"]:
            return self._chunk_markdown_file(content, relative_path, file_path)
        else:
            return self._chunk_plain_file(content, relative_path, file_path)

    def _chunk_code_file(
        self, content: str, relative_path: str, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Chunk code files by functions/classes"""
        chunks = []
        lines = content.split("\n")

        # Try to parse as Python for function/class extraction
        if file_path.suffix == ".py":
            try:
                tree = ast.parse(content)
                chunks.extend(self._extract_python_chunks(tree, lines, relative_path))
            except Exception as e:
                logger.warning(f"Failed to parse Python file {relative_path}: {e}")
                # Fallback to line-based chunking
                chunks.extend(self._chunk_by_lines(content, relative_path, file_path))
        else:
            # For other languages, use simple line-based chunking
            chunks.extend(self._chunk_by_lines(content, relative_path, file_path))

        return chunks

    def _extract_python_chunks(
        self, tree: ast.AST, lines: List[str], relative_path: str
    ) -> List[Dict[str, Any]]:
        """Extract functions and classes from Python AST"""
        chunks = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                start_line = node.lineno - 1  # 0-based
                end_line = (
                    node.end_lineno - 1
                    if hasattr(node, "end_lineno")
                    else min(start_line + 20, len(lines) - 1)
                )

                if start_line < len(lines):
                    chunk_lines = lines[start_line : end_line + 1]
                    chunk_content = "\n".join(chunk_lines)

                    # Add context lines before and after
                    context_start = max(0, start_line - 3)
                    context_end = min(len(lines), end_line + 3)
                    context_lines = lines[context_start : context_end + 1]
                    context_content = "\n".join(context_lines)

                    chunks.append(
                        {
                            "id": f"{relative_path}:{start_line}-{end_line}",
                            "content": context_content,
                            "start_line": context_start + 1,  # 1-based for display
                            "end_line": context_end + 1,
                            "type": "function"
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                            else "class",
                            "name": node.name,
                            "language": "python",
                        }
                    )

        return chunks

    def _chunk_markdown_file(
        self, content: str, relative_path: str, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Chunk markdown files by sections"""
        chunks = []
        lines = content.split("\n")

        # Split by headers (##, ###, etc.)
        current_section = []
        current_header = "Introduction"
        start_line = 0

        for i, line in enumerate(lines):
            if re.match(r"^#{1,6}\s+(.+)$", line):
                # Save previous section if it has content
                if current_section:
                    section_content = "\n".join(current_section)
                    if len(section_content.strip()) > 50:  # Skip very short sections
                        chunks.append(
                            {
                                "id": f"{relative_path}:{start_line}-{i - 1}",
                                "content": section_content,
                                "start_line": start_line + 1,
                                "end_line": i,
                                "type": "section",
                                "name": current_header,
                                "language": "markdown",
                            }
                        )

                # Start new section
                current_section = [line]
                current_header = re.sub(r"^#{1,6}\s+", "", line).strip()
                start_line = i
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            section_content = "\n".join(current_section)
            if len(section_content.strip()) > 50:
                chunks.append(
                    {
                        "id": f"{relative_path}:{start_line}-{len(lines) - 1}",
                        "content": section_content,
                        "start_line": start_line + 1,
                        "end_line": len(lines),
                        "type": "section",
                        "name": current_header,
                        "language": "markdown",
                    }
                )

        return chunks

    def _chunk_by_lines(
        self, content: str, relative_path: str, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Generic chunking by lines with overlap"""
        chunks = []
        lines = content.split("\n")
        chunk_size = 50  # lines per chunk
        overlap = 5  # overlapping lines

        for start in range(0, len(lines), chunk_size - overlap):
            end = min(start + chunk_size, len(lines))
            chunk_lines = lines[start:end]
            chunk_content = "\n".join(chunk_lines)

            if len(chunk_content.strip()) > 20:  # Skip very short chunks
                chunks.append(
                    {
                        "id": f"{relative_path}:{start}-{end - 1}",
                        "content": chunk_content,
                        "start_line": start + 1,
                        "end_line": end,
                        "type": "chunk",
                        "language": file_path.suffix[1:]
                        if file_path.suffix
                        else "text",
                    }
                )

        return chunks

    def _chunk_plain_file(
        self, content: str, relative_path: str, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Chunk plain text/config files"""
        chunks = []

        # For config files, keep whole file as one chunk if not too large
        if len(content) < 5000:  # Less than ~5KB
            chunks.append(
                {
                    "id": f"{relative_path}:0-0",
                    "content": content,
                    "start_line": 1,
                    "end_line": len(content.split("\n")),
                    "type": "file",
                    "language": file_path.suffix[1:] if file_path.suffix else "text",
                }
            )
        else:
            # Split larger files
            chunks.extend(self._chunk_by_lines(content, relative_path, file_path))

        return chunks

    def extract_metadata(
        self, file_path: Path, chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract metadata for a chunk"""
        metadata = {
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "extension": file_path.suffix,
            "language": chunk.get("language", "unknown"),
            "chunk_type": chunk.get("type", "unknown"),
            "indexed_at": time.time(),
        }

        # Add specific metadata based on chunk type
        if chunk.get("name"):
            metadata["symbol_name"] = chunk["name"]

        if chunk.get("type") in ["function", "class"]:
            metadata["code_entity"] = chunk["type"]

        return metadata

    async def index_repository(
        self, repo_path: str, collection_name: str, force_reindex: bool = False
    ) -> Dict[str, Any]:
        """Index entire repository into Qdrant"""
        start_time = time.time()

        try:
            # Discover files
            files = self.discover_files(repo_path)

            if not files:
                return {
                    "success": False,
                    "error": "No indexable files found",
                    "chunks_indexed": 0,
                    "files_processed": 0,
                }

            # Process all files and create chunks
            all_chunks = []
            total_files = len(files)
            processed_files = 0

            for file_path in files:
                try:
                    file_chunks = self.chunk_file(file_path)
                    for chunk in file_chunks:
                        # Add metadata
                        metadata = self.extract_metadata(file_path, chunk)
                        chunk.update({"payload": metadata})
                        all_chunks.append(chunk)

                    processed_files += 1

                    if processed_files % 10 == 0:
                        logger.info(
                            f"Processed {processed_files}/{total_files} files, {len(all_chunks)} chunks so far"
                        )

                except Exception as e:
                    logger.error(f"Failed to process file {file_path}: {e}")
                    continue

            indexing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Indexing completed: {processed_files} files, {len(all_chunks)} chunks in {indexing_time_ms}ms"
            )

            return {
                "success": True,
                "chunks": all_chunks,
                "chunks_indexed": len(all_chunks),
                "files_processed": processed_files,
                "indexing_time_ms": indexing_time_ms,
                "collection_name": collection_name,
            }

        except Exception as e:
            logger.error(f"Repository indexing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks_indexed": 0,
                "files_processed": 0,
            }
