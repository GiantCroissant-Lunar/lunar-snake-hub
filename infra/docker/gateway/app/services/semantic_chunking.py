"""
Semantic Chunking Service
Advanced document chunking using semantic boundaries and code structure awareness
"""

import logging
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tiktoken

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Semantic chunk with metadata"""

    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # 'function', 'class', 'section', 'paragraph'
    language: str
    metadata: Dict[str, Any]


class SemanticChunkingService:
    """Advanced semantic chunking for code and documentation"""

    def __init__(self):
        self.sentence_model = None
        self.tokenizer = None
        self._initialize_models()

    def _initialize_models(self):
        """Initialize NLP models for semantic chunking"""
        try:
            # Initialize sentence transformer for semantic boundaries
            self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✅ Sentence transformer initialized")

            # Initialize tokenizer for token counting
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("✅ Tokenizer initialized")

        except Exception as e:
            logger.warning(f"⚠️ Model initialization failed: {e}")
            self.sentence_model = None
            self.tokenizer = None

    async def chunk_document(self, file_path: str, content: str) -> List[Chunk]:
        """Chunk document using semantic analysis"""
        try:
            file_ext = Path(file_path).suffix.lower()
            language = self._detect_language(file_ext)

            logger.info(f"📄 Chunking {file_path} (language: {language})")

            # Choose chunking strategy based on file type
            if language == "python":
                chunks = await self._chunk_python_code(file_path, content)
            elif language in ["javascript", "typescript"]:
                chunks = await self._chunk_javascript_code(file_path, content)
            elif language in ["markdown", "text"]:
                chunks = await self._chunk_markdown(file_path, content)
            elif language in ["yaml", "yml", "json"]:
                chunks = await self._chunk_config_file(file_path, content)
            else:
                chunks = await self._chunk_generic(file_path, content)

            logger.info(f"✅ Generated {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"❌ Chunking failed for {file_path}: {e}")
            return await self._fallback_chunking(file_path, content)

    def _detect_language(self, file_ext: str) -> str:
        """Detect programming language from file extension"""
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".rb": "ruby",
            ".php": "php",
            ".md": "markdown",
            ".txt": "text",
            ".rst": "text",
            ".adoc": "text",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".toml": "toml",
            ".cfg": "text",
            ".ini": "text",
            ".conf": "text",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".fish": "bash",
            ".ps1": "powershell",
            ".bat": "batch",
            ".cmd": "batch",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".scss": "css",
            ".sass": "css",
            ".less": "css",
            ".xml": "xml",
            ".dockerfile": "dockerfile",
        }
        return language_map.get(file_ext, "text")

    async def _chunk_python_code(self, file_path: str, content: str) -> List[Chunk]:
        """Chunk Python code using AST analysis"""
        chunks = []
        lines = content.split("\n")

        try:
            tree = ast.parse(content)

            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    chunk = await self._extract_python_node(node, lines, file_path)
                    if chunk:
                        chunks.append(chunk)

            # If no structured chunks found, fall back to semantic chunking
            if not chunks:
                chunks = await self._semantic_chunk_text(file_path, content, "python")

        except SyntaxError:
            # Fallback for syntax errors
            logger.warning(
                f"⚠️ Python syntax error in {file_path}, using fallback chunking"
            )
            chunks = await self._semantic_chunk_text(file_path, content, "python")

        return chunks

    async def _extract_python_node(
        self, node: ast.AST, lines: List[str], file_path: str
    ) -> Optional[Chunk]:
        """Extract function or class as a chunk"""
        try:
            start_line = node.lineno - 1
            end_line = (
                node.end_lineno - 1 if hasattr(node, "end_lineno") else start_line + 10
            )

            # Ensure we don't go out of bounds
            end_line = min(end_line, len(lines) - 1)

            content_lines = lines[start_line : end_line + 1]
            content = "\n".join(content_lines)

            # Create chunk ID
            node_type = (
                "function"
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                else "class"
            )
            node_name = getattr(node, "name", "unknown")
            chunk_id = f"{file_path}:{node_type}:{node_name}:{start_line}-{end_line}"

            # Extract metadata
            metadata = {
                "node_type": node_type,
                "name": node_name,
                "docstring": ast.get_docstring(node),
                "decorators": [
                    ast.unparse(d) for d in getattr(node, "decorator_list", [])
                ],
                "arguments": [],
            }

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metadata["arguments"] = [arg.arg for arg in node.args.args]

            return Chunk(
                id=chunk_id,
                content=content,
                file_path=file_path,
                start_line=start_line + 1,
                end_line=end_line + 1,
                chunk_type=node_type,
                language="python",
                metadata=metadata,
            )

        except Exception as e:
            logger.warning(f"⚠️ Failed to extract Python node: {e}")
            return None

    async def _chunk_javascript_code(self, file_path: str, content: str) -> List[Chunk]:
        """Chunk JavaScript/TypeScript code using regex patterns"""
        chunks = []
        lines = content.split("\n")

        # Regex patterns for functions and classes
        function_pattern = r"(?:async\s+)?(?:function\s+\w+|=>|\w+\s*=\s*(?:function\s+\w+|\([^)]*\)\s*=>)|(?:const|let|var)\s+\w+\s*=\s*(?:function\s+\w+|\([^)]*\)\s*=>))"
        class_pattern = r"(?:class\s+\w+|interface\s+\w+|type\s+\w+\s*=)"

        # Find all matches with line numbers
        function_matches = list(re.finditer(function_pattern, content, re.MULTILINE))
        class_matches = list(re.finditer(class_pattern, content, re.MULTILINE))

        # Combine and sort by position
        all_matches = []
        for match in function_matches:
            all_matches.append(("function", match))
        for match in class_matches:
            all_matches.append(("class", match))

        all_matches.sort(key=lambda x: x[1].start())

        # Create chunks
        for chunk_type, match in all_matches:
            start_line = content[: match.start()].count("\n")
            end_line = content[: match.end()].count("\n") + 5  # Add some context

            # Find the end of the block
            brace_count = 0
            for i in range(match.start(), len(content)):
                if content[i] == "{":
                    brace_count += 1
                elif content[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_line = content[:i].count("\n")
                        break

            # Ensure bounds
            end_line = min(end_line, len(lines) - 1)

            content_lines = lines[start_line : end_line + 1]
            chunk_content = "\n".join(content_lines)

            # Extract name
            name_match = re.search(
                r"(?:function|class|interface|type)\s+(\w+)", match.group()
            )
            name = name_match.group(1) if name_match else "anonymous"

            chunk_id = f"{file_path}:{chunk_type}:{name}:{start_line}-{end_line}"

            chunks.append(
                Chunk(
                    id=chunk_id,
                    content=chunk_content,
                    file_path=file_path,
                    start_line=start_line + 1,
                    end_line=end_line + 1,
                    chunk_type=chunk_type,
                    language="javascript",
                    metadata={
                        "name": name,
                        "signature": match.group(),
                        "is_async": "async" in match.group(),
                    },
                )
            )

        # Fallback if no structured chunks
        if not chunks:
            chunks = await self._semantic_chunk_text(file_path, content, "javascript")

        return chunks

    async def _chunk_markdown(self, file_path: str, content: str) -> List[Chunk]:
        """Chunk Markdown by sections and semantic boundaries"""
        chunks = []
        lines = content.split("\n")

        # Split by headers
        sections = re.split(r"^(#{1,6})\s+(.+)$", content, flags=re.MULTILINE)

        current_pos = 0
        section_number = 1

        for i in range(1, len(sections), 3):  # Headers are at positions 1, 4, 7, ...
            if i + 1 < len(sections):
                header = sections[i]
                title = sections[i + 1]
                section_content = sections[i + 2] if i + 2 < len(sections) else ""

                # Calculate line numbers
                start_line = content[:current_pos].count("\n")
                section_start = current_pos + len(header) + len(title)
                end_line = content[: section_start + len(section_content)].count("\n")

                chunk_id = (
                    f"{file_path}:section:{section_number}:{start_line}-{end_line}"
                )

                chunks.append(
                    Chunk(
                        id=chunk_id,
                        content=header + title + section_content,
                        file_path=file_path,
                        start_line=start_line + 1,
                        end_line=end_line + 1,
                        chunk_type="section",
                        language="markdown",
                        metadata={
                            "section_number": section_number,
                            "title": title.strip(),
                            "level": len(header),
                        },
                    )
                )

                current_pos = section_start + len(section_content)
                section_number += 1

        # Add any remaining content
        if current_pos < len(content):
            start_line = content[:current_pos].count("\n")
            end_line = content.count("\n")
            remaining_content = content[current_pos:]

            if remaining_content.strip():
                chunk_id = (
                    f"{file_path}:paragraph:{section_number}:{start_line}-{end_line}"
                )

                chunks.append(
                    Chunk(
                        id=chunk_id,
                        content=remaining_content,
                        file_path=file_path,
                        start_line=start_line + 1,
                        end_line=end_line + 1,
                        chunk_type="paragraph",
                        language="markdown",
                        metadata={"section_number": section_number, "is_footer": True},
                    )
                )

        return chunks

    async def _chunk_config_file(self, file_path: str, content: str) -> List[Chunk]:
        """Chunk configuration files by sections"""
        chunks = []
        lines = content.split("\n")

        # Try to parse as YAML/JSON structure
        try:
            import yaml

            data = yaml.safe_load(content)

            # Create chunks for top-level keys
            if isinstance(data, dict):
                for key, value in data.items():
                    # Find the line where this key starts
                    key_pattern = re.compile(rf"^{re.escape(key)}\s*:", re.MULTILINE)
                    match = key_pattern.search(content)

                    if match:
                        start_line = content[: match.start()].count("\n")
                        # Estimate end line (simplified)
                        end_line = min(start_line + 10, len(lines) - 1)

                        chunk_content = "\n".join(lines[start_line : end_line + 1])

                        chunk_id = f"{file_path}:section:{key}:{start_line}-{end_line}"

                        chunks.append(
                            Chunk(
                                id=chunk_id,
                                content=chunk_content,
                                file_path=file_path,
                                start_line=start_line + 1,
                                end_line=end_line + 1,
                                chunk_type="section",
                                language="yaml",
                                metadata={
                                    "key": key,
                                    "value_type": type(value).__name__,
                                },
                            )
                        )

        except Exception:
            # Fallback to line-based chunking
            chunks = await self._chunk_by_lines(file_path, content, "yaml")

        return chunks

    async def _chunk_generic(self, file_path: str, content: str) -> List[Chunk]:
        """Generic semantic chunking for unknown file types"""
        return await self._semantic_chunk_text(file_path, content, "text")

    async def _semantic_chunk_text(
        self, file_path: str, content: str, language: str
    ) -> List[Chunk]:
        """Semantic chunking using sentence boundaries"""
        chunks = []
        lines = content.split("\n")

        if not self.sentence_model:
            # Fallback to line-based chunking
            return await self._chunk_by_lines(file_path, content, language)

        try:
            # Split into sentences (simplified)
            sentences = re.split(r"[.!?]+[\s\n]+", content)

            # Group sentences into chunks of appropriate size
            chunk_size = 3  # sentences per chunk
            overlap = 1  # sentence overlap

            for i in range(0, len(sentences), chunk_size - overlap):
                chunk_sentences = sentences[i : i + chunk_size]
                chunk_content = ". ".join(chunk_sentences).strip()

                if not chunk_content:
                    continue

                # Find line numbers
                start_pos = content.find(chunk_content)
                if start_pos == -1:
                    continue

                start_line = content[:start_pos].count("\n")
                end_line = content[: start_pos + len(chunk_content)].count("\n")

                chunk_id = (
                    f"{file_path}:semantic:{i // chunk_size}:{start_line}-{end_line}"
                )

                chunks.append(
                    Chunk(
                        id=chunk_id,
                        content=chunk_content,
                        file_path=file_path,
                        start_line=start_line + 1,
                        end_line=end_line + 1,
                        chunk_type="semantic",
                        language=language,
                        metadata={
                            "sentence_count": len(chunk_sentences),
                            "chunk_index": i // chunk_size,
                        },
                    )
                )

        except Exception as e:
            logger.warning(f"⚠️ Semantic chunking failed: {e}")
            return await self._chunk_by_lines(file_path, content, language)

        return chunks

    async def _chunk_by_lines(
        self, file_path: str, content: str, language: str, chunk_size: int = 50
    ) -> List[Chunk]:
        """Fallback line-based chunking"""
        chunks = []
        lines = content.split("\n")

        for i in range(0, len(lines), chunk_size):
            end_line = min(i + chunk_size, len(lines))
            chunk_lines = lines[i:end_line]
            chunk_content = "\n".join(chunk_lines)

            if not chunk_content.strip():
                continue

            chunk_id = f"{file_path}:lines:{i // chunk_size}:{i + 1}-{end_line}"

            chunks.append(
                Chunk(
                    id=chunk_id,
                    content=chunk_content,
                    file_path=file_path,
                    start_line=i + 1,
                    end_line=end_line,
                    chunk_type="lines",
                    language=language,
                    metadata={
                        "line_count": len(chunk_lines),
                        "chunk_index": i // chunk_size,
                    },
                )
            )

        return chunks

    async def _fallback_chunking(self, file_path: str, content: str) -> List[Chunk]:
        """Ultimate fallback chunking method"""
        logger.warning(f"⚠️ Using fallback chunking for {file_path}")
        return await self._chunk_by_lines(file_path, content, "text", chunk_size=30)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not self.tokenizer:
            return len(text.split())  # Fallback to word count

        try:
            return len(self.tokenizer.encode(text))
        except Exception:
            return len(text.split())

    async def optimize_chunk_size(
        self, chunks: List[Chunk], max_tokens: int = 512
    ) -> List[Chunk]:
        """Optimize chunk sizes to stay within token limits"""
        optimized_chunks = []

        for chunk in chunks:
            token_count = self.count_tokens(chunk.content)

            if token_count <= max_tokens:
                optimized_chunks.append(chunk)
            else:
                # Split large chunks
                sub_chunks = await self._split_large_chunk(chunk, max_tokens)
                optimized_chunks.extend(sub_chunks)

        return optimized_chunks

    async def _split_large_chunk(self, chunk: Chunk, max_tokens: int) -> List[Chunk]:
        """Split a large chunk into smaller ones"""
        content = chunk.content
        lines = content.split("\n")

        sub_chunks = []
        current_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.count_tokens(line)

            if current_tokens + line_tokens > max_tokens and current_lines:
                # Create sub-chunk
                sub_content = "\n".join(current_lines)
                sub_chunk = Chunk(
                    id=f"{chunk.id}_sub_{len(sub_chunks)}",
                    content=sub_content,
                    file_path=chunk.file_path,
                    start_line=chunk.start_line + len(sub_chunks),
                    end_line=chunk.start_line + len(current_lines),
                    chunk_type=chunk.chunk_type,
                    language=chunk.language,
                    metadata={**chunk.metadata, "parent_chunk": chunk.id},
                )
                sub_chunks.append(sub_chunk)

                current_lines = [line]
                current_tokens = line_tokens
            else:
                current_lines.append(line)
                current_tokens += line_tokens

        # Add remaining lines
        if current_lines:
            sub_content = "\n".join(current_lines)
            sub_chunk = Chunk(
                id=f"{chunk.id}_sub_{len(sub_chunks)}",
                content=sub_content,
                file_path=chunk.file_path,
                start_line=chunk.end_line - len(current_lines) + 1,
                end_line=chunk.end_line,
                chunk_type=chunk.chunk_type,
                language=chunk.language,
                metadata={**chunk.metadata, "parent_chunk": chunk.id},
            )
            sub_chunks.append(sub_chunk)

        return sub_chunks
