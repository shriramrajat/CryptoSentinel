"""
Core Discovery & Scanner Engine for ECDAT.
Recursively scans source files for cryptographic algorithms, libraries, keys, and parameters.
"""

import os
from pathlib import Path
from typing import List, Set, Union, Optional
from ecdat.models import CryptoAsset
from ecdat.rules import (
    REGEX_RULES,
    RegexRule,
    is_hardcoded_secret_candidate,
    redact_secret_literal,
)
from ecdat.ast_parser import scan_python_ast

DEFAULT_IGNORED_DIRS: Set[str] = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "build",
    "dist",
    ".idea",
    ".vscode",
    "target",       # Rust/Maven build output
    "vendor",       # Go vendor, PHP Composer
    ".gradle",
    "out",
    "bin",
    "obj",
}

# Extensions grouped by language (ordered by specificity)
SUPPORTED_EXTENSIONS: Set[str] = {
    # Python
    ".py",
    # Java
    ".java",
    # C / C++
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
    # JavaScript / TypeScript
    ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx",
    # Go
    ".go",
    # Rust
    ".rs",
    # PHP
    ".php",
    # C#
    ".cs",
    # Kotlin
    ".kt", ".kts",
    # Certificate / Key artefacts
    ".pem", ".crt", ".key", ".cer", ".der",
    # Configuration / Structured files
    ".yaml", ".yml", ".toml", ".json", ".xml",
    ".env", ".config", ".properties", ".ini", ".conf",
}


def strip_comments_from_lines(content_lines: List[str], language: str) -> List[str]:
    """
    Strips single-line and multi-line comments from code lines while preserving
    line positions and line count. Does not build a full language parser.
    """
    cleaned_lines = []
    in_block_comment = False

    for line in content_lines:
        if language == "python":
            stripped = line.strip()
            if stripped.startswith("#"):
                cleaned_lines.append(" " * len(line))
                continue
            # Strip trailing inline comments if '#' is outside string literals
            in_single_quote = False
            in_double_quote = False
            comment_start = -1
            for i, ch in enumerate(line):
                if ch == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                elif ch == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif ch == "#" and not in_single_quote and not in_double_quote:
                    comment_start = i
                    break
            if comment_start != -1:
                cleaned_lines.append(line[:comment_start] + " " * (len(line) - comment_start))
            else:
                cleaned_lines.append(line)
            continue

        if language in ["java", "c", "cpp", "javascript", "typescript", "go", "csharp", "kotlin", "rust", "php", "all", "pem"]:
            current_chars = list(line)
            i = 0
            n = len(current_chars)
            quote_char = None
            escaped = False
            while i < n:
                if in_block_comment:
                    if i + 1 < n and current_chars[i] == '*' and current_chars[i + 1] == '/':
                        current_chars[i] = ' '
                        current_chars[i + 1] = ' '
                        in_block_comment = False
                        i += 2
                    else:
                        current_chars[i] = ' '
                        i += 1
                else:
                    ch = current_chars[i]
                    if quote_char:
                        if escaped:
                            escaped = False
                        elif ch == '\\':
                            escaped = True
                        elif ch == quote_char:
                            quote_char = None
                        i += 1
                    elif ch in ['"', "'"]:
                        quote_char = ch
                        i += 1
                    elif i + 1 < n and current_chars[i] == '/' and current_chars[i + 1] == '*':
                        current_chars[i] = ' '
                        current_chars[i + 1] = ' '
                        in_block_comment = True
                        i += 2
                    elif i + 1 < n and current_chars[i] == '/' and current_chars[i + 1] == '/':
                        for j in range(i, n):
                            current_chars[j] = ' '
                        break
                    else:
                        i += 1
            cleaned_lines.append("".join(current_chars))

        elif language in ["config", "yaml", "toml", "php"]:
            # Strip # comments (YAML/TOML/shell-style config)
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith(";"):
                cleaned_lines.append(" " * len(line))
            else:
                cleaned_lines.append(line)

        elif language == "xml":
            # Strip XML comments <!-- ... -->
            cleaned_lines.append(line)  # XML comment stripping done per-block elsewhere

        else:
            cleaned_lines.append(line)

    return cleaned_lines


def _string_literal_masks(content_lines: List[str], language: str) -> List[List[bool]]:
    """Build per-line masks for string literal regions, preserving column positions."""
    if language in ["pem", "config", "yaml", "toml", "xml"]:
        return [[False] * len(line) for line in content_lines]

    masks: List[List[bool]] = []
    triple_quote = None

    for line in content_lines:
        mask = [False] * len(line)
        i = 0
        n = len(line)

        while i < n:
            if triple_quote:
                end = line.find(triple_quote, i)
                end_pos = n if end == -1 else end + 3
                for pos in range(i, end_pos):
                    mask[pos] = True
                if end == -1:
                    i = n
                else:
                    triple_quote = None
                    i = end_pos
                continue

            if language in ["python", "java", "kotlin"] and i + 2 < n and line[i:i + 3] in ['"""', "'''"]:
                triple_quote = line[i:i + 3]
                end = line.find(triple_quote, i + 3)
                end_pos = n if end == -1 else end + 3
                for pos in range(i, end_pos):
                    mask[pos] = True
                if end == -1:
                    i = n
                else:
                    triple_quote = None
                    i = end_pos
                continue

            if i < n and line[i] in ['"', "'"]:
                quote_char = line[i]
                start = i
                i += 1
                escaped = False
                while i < n:
                    ch = line[i]
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote_char:
                        i += 1
                        break
                    i += 1

                for pos in range(start, min(i, n)):
                    mask[pos] = True
                continue

            i += 1

        masks.append(mask)

    return masks


class Scanner:
    def __init__(
        self,
        ignored_dirs: Optional[Set[str]] = None,
        root_dir: Optional[Union[str, Path]] = None,
    ):
        self.ignored_dirs = ignored_dirs or DEFAULT_IGNORED_DIRS
        self.root_dir = root_dir

    def discover_files(self, root_path: Union[str, Path]) -> List[Path]:
        """Recursively discover supported source files while respecting ignore list."""
        path = Path(root_path).resolve()
        discovered: List[Path] = []

        if path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                return [path]
            return []

        if not path.is_dir():
            return []

        for root, dirs, files in os.walk(path):
            # Exclude ignored directories in-place
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    discovered.append(file_path)

        return sorted(discovered)

    def _determine_language(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        name = file_path.name.lower()

        if ext == ".py":
            return "python"
        elif ext == ".java":
            return "java"
        elif ext in [".c", ".h"]:
            return "c"
        elif ext in [".cpp", ".hpp", ".cc", ".cxx"]:
            return "cpp"
        elif ext in [".js", ".mjs", ".cjs", ".jsx"]:
            return "javascript"
        elif ext in [".ts", ".tsx"]:
            return "typescript"
        elif ext == ".go":
            return "go"
        elif ext == ".rs":
            return "rust"
        elif ext == ".php":
            return "php"
        elif ext == ".cs":
            return "csharp"
        elif ext in [".kt", ".kts"]:
            return "kotlin"
        elif ext in [".pem", ".crt", ".key", ".cer", ".der"]:
            return "pem"
        elif ext in [".yaml", ".yml"]:
            return "yaml"
        elif ext == ".toml":
            return "toml"
        elif ext == ".xml":
            return "xml"
        elif ext in [".json"]:
            return "json"
        elif ext in [".env", ".properties", ".ini", ".conf", ".config"] or name in [".env"]:
            return "config"
        return "all"

    def _language_for_rule_matching(self, language: str) -> str:
        """Map language to the set of language tags rules can use."""
        # TypeScript rules also apply JavaScript rules
        if language == "typescript":
            return "javascript"
        # cpp also applies c rules
        if language == "cpp":
            return "c"
        # yaml/toml/json/config/xml all use "config"
        if language in ["yaml", "toml", "json", "config", "xml"]:
            return "config"
        return language

    @staticmethod
    def _deduplicate_assets(assets: List[CryptoAsset]) -> List[CryptoAsset]:
        """
        Deduplicates assets on the same line with the same algorithm,
        preferring the hit with higher confidence or richer metadata.
        """
        grouped: Dict[tuple, List[CryptoAsset]] = {}
        for a in assets:
            key = (a.line_number, a.algorithm.upper())
            grouped.setdefault(key, []).append(a)

        deduped: List[CryptoAsset] = []
        for key, group in grouped.items():
            if len(group) == 1:
                deduped.append(group[0])
            else:
                sorted_group = sorted(
                    group,
                    key=lambda x: (
                        x.confidence,
                        1 if (x.key_length is not None or x.mode is not None) else 0,
                        0 if (x.detection_rule and x.detection_rule.startswith("generic-")) else 1,
                    ),
                    reverse=True,
                )
                deduped.append(sorted_group[0])

        return sorted(deduped, key=lambda x: x.line_number)

    def scan_file_regex(
        self,
        file_path: Path,
        content_lines: List[str],
        root_dir: Optional[Union[str, Path]] = None,
    ) -> List[CryptoAsset]:
        """Scan file content using regular expression rules."""
        language = self._determine_language(file_path)
        assets: List[CryptoAsset] = []
        effective_root = root_dir or self.root_dir
        rule_lang = self._language_for_rule_matching(language)

        cleaned_lines = strip_comments_from_lines(content_lines, language)
        string_masks = _string_literal_masks(cleaned_lines, language)

        for idx, (original_line, search_line, string_mask) in enumerate(
            zip(content_lines, cleaned_lines, string_masks),
            start=1,
        ):
            stripped_search = search_line.strip()
            if not stripped_search:
                continue

            for rule in REGEX_RULES:
                # Rule language matching: rule must match file language (or be 'all')
                if rule.language not in ["all", language, rule_lang]:
                    # Extra: allow 'c' rules for 'cpp', 'javascript' rules for 'typescript'
                    if not (rule.language == "c" and language == "cpp"):
                        if not (rule.language == "javascript" and language == "typescript"):
                            if not (rule.language == "config" and language in ["yaml", "toml", "json", "xml", "config"]):
                                continue

                match = None
                for candidate in rule.pattern.finditer(search_line):
                    if candidate.start() < len(string_mask) and string_mask[candidate.start()]:
                        continue
                    match = candidate
                    break

                if match:
                    algorithm = rule.algorithm
                    category = rule.category
                    library = rule.library
                    key_length = rule.key_length
                    mode = rule.mode
                    padding = rule.padding
                    confidence = rule.confidence
                    purpose = rule.purpose
                    protocol = rule.protocol
                    detection_mechanism = "pem_header" if library == "PEM" else "regex"
                    code_snippet = original_line.strip()

                    if rule.secret_name_group and rule.secret_value_group:
                        identifier = match.group(rule.secret_name_group)
                        literal_value = match.group(rule.secret_value_group)
                        if not is_hardcoded_secret_candidate(identifier, literal_value):
                            continue
                        code_snippet = redact_secret_literal(code_snippet)

                    # ── Dynamic parsing for Java / Kotlin JCE rules ──
                    if rule.rule_id in ["JAVA-JCE-CIPHER-001", "KT-JCE-CIPHER-001"]:
                        transform = match.group(1)
                        parts = transform.split("/")
                        if len(parts) >= 1:
                            algorithm = parts[0].upper()
                            if algorithm == "DESEDE":
                                algorithm = "3DES"
                            if algorithm in ["RSA", "EC", "DSA", "DH"]:
                                category = "asymmetric_encryption"
                            elif algorithm in ["AES", "DES", "3DES"]:
                                category = "symmetric_encryption"
                        if len(parts) >= 2:
                            mode = parts[1].upper()
                        if len(parts) >= 3:
                            padding = parts[2]

                    elif rule.rule_id in ["JAVA-JCE-KEYPAIRGEN-001", "KT-JCE-KEYPAIRGEN-001"]:
                        algo_match = match.group(1).upper()
                        algorithm = "ECC" if algo_match == "EC" else algo_match
                        category = "asymmetric_encryption"

                    elif rule.rule_id in ["JAVA-JCE-MESSAGEDIGEST-001", "KT-JCE-MESSAGEDIGEST-001"]:
                        algo_match = match.group(1).upper()
                        algorithm = algo_match
                        category = "hashing"
                        purpose = "hashing"

                    elif rule.rule_id in ["JAVA-JCE-KEYAGREEMENT-001"]:
                        algo_match = match.group(1).upper()
                        algorithm = algo_match
                        category = "key_exchange"

                    elif rule.rule_id in ["JAVA-JCE-SIGNATURE-001", "KT-JCE-SIGNATURE-001"]:
                        algo_match = match.group(1).upper()
                        if "ECDSA" in algo_match:
                            algorithm = "ECDSA"
                        elif "DSA" in algo_match:
                            algorithm = "DSA"
                        elif "RSA" in algo_match:
                            algorithm = "RSA"
                        else:
                            algorithm = algo_match
                        category = "digital_signature"
                        purpose = "signing"

                    # ── Dynamic parsing for Python RSA.generate regex ──
                    elif rule.rule_id == "PY-PYCRYPTO-RSA-GENERATE-001":
                        try:
                            key_length = int(match.group(1))
                        except (IndexError, ValueError):
                            key_length = None

                    # ── Dynamic parsing for JS/TS WebCrypto digest ──
                    elif rule.rule_id == "JS-WEBCRYPTO-DIGEST-001":
                        try:
                            algo_str = match.group(1)
                            algorithm = algo_str  # SHA-1, SHA-256, SHA-384, SHA-512
                            purpose = "hashing"
                        except (IndexError, AttributeError):
                            pass

                    # ── Dynamic parsing for JS/TS WebCrypto generateKey / encrypt ──
                    elif rule.rule_id in ["JS-WEBCRYPTO-GENERATE-001", "JS-WEBCRYPTO-ENCRYPT-001"]:
                        try:
                            algo_str = match.group(1).upper()
                            if "RSA" in algo_str:
                                algorithm = "RSA"
                                category = "asymmetric_encryption"
                            elif "EC" in algo_str:
                                algorithm = "ECC"
                                category = "asymmetric_encryption"
                            elif "AES" in algo_str:
                                algorithm = "AES"
                                if "-GCM" in algo_str:
                                    mode = "GCM"
                                elif "-CBC" in algo_str:
                                    mode = "CBC"
                            elif "HMAC" in algo_str:
                                algorithm = "HMAC"
                                category = "mac"
                        except (IndexError, AttributeError):
                            pass

                    # ── Dynamic parsing for Node.js crypto functions ──
                    elif rule.rule_id == "JS-CRYPTO-NODE-CREATEHASH-001":
                        try:
                            algo_str = match.group(1).lower()
                            _hash_map = {
                                "md5": "MD5", "sha1": "SHA-1", "sha224": "SHA-224",
                                "sha256": "SHA-256", "sha384": "SHA-384",
                                "sha512": "SHA-512", "sha3-256": "SHA-3",
                            }
                            algorithm = _hash_map.get(algo_str, algo_str.upper())
                            purpose = "hashing"
                        except (IndexError, AttributeError):
                            pass

                    elif rule.rule_id == "JS-CRYPTO-NODE-CREATECIPHER-001":
                        try:
                            algo_str = match.group(1).lower()
                            if "aes-256-gcm" in algo_str:
                                algorithm = "AES"; key_length = 256; mode = "GCM"
                            elif "aes-128-gcm" in algo_str:
                                algorithm = "AES"; key_length = 128; mode = "GCM"
                            elif "aes-256-cbc" in algo_str:
                                algorithm = "AES"; key_length = 256; mode = "CBC"
                            elif "aes-128-cbc" in algo_str:
                                algorithm = "AES"; key_length = 128; mode = "CBC"
                            elif "des" in algo_str:
                                algorithm = "DES"
                            elif "rc4" in algo_str:
                                algorithm = "RC4"
                            purpose = "encryption"
                        except (IndexError, AttributeError):
                            pass

                    elif rule.rule_id == "JS-CRYPTO-NODE-GENKEYPAIR-001":
                        try:
                            algo_str = match.group(1).lower()
                            _kp_map = {"rsa": "RSA", "ec": "ECC", "ed25519": "Ed25519", "dh": "DH"}
                            algorithm = _kp_map.get(algo_str, algo_str.upper())
                            if algo_str in ["rsa", "ec"]:
                                category = "asymmetric_encryption"
                        except (IndexError, AttributeError):
                            pass

                    # ── Dynamic parsing for PHP password_hash ──
                    elif rule.rule_id == "PHP-PASSWORD-HASH-001":
                        try:
                            algo_const = match.group(1).upper()
                            if "ARGON2" in algo_const:
                                algorithm = "Argon2"
                            elif "BCRYPT" in algo_const:
                                algorithm = "bcrypt"
                                category = "key_derivation"
                        except (IndexError, AttributeError):
                            pass

                    elif rule.rule_id == "PHP-HASH-001":
                        try:
                            algo_str = match.group(1).lower()
                            _ph_map = {
                                "md5": "MD5", "sha1": "SHA-1", "sha256": "SHA-256",
                                "sha384": "SHA-384", "sha512": "SHA-512",
                                "sha3-256": "SHA-3", "sha3-512": "SHA-3",
                            }
                            algorithm = _ph_map.get(algo_str, algo_str.upper())
                        except (IndexError, AttributeError):
                            pass

                    # ── Dynamic parsing for WebCrypto sign ──
                    elif rule.rule_id == "JS-WEBCRYPTO-SIGN-001":
                        try:
                            algo_str = match.group(1)
                            if "ECDSA" in algo_str:
                                algorithm = "ECDSA"
                            elif "Ed25519" in algo_str:
                                algorithm = "Ed25519"
                            elif "RSA" in algo_str:
                                algorithm = "RSA"
                            category = "digital_signature"
                            purpose = "signing"
                        except (IndexError, AttributeError):
                            pass

                    # Preserve backward-compatible rule IDs for legacy tests
                    matched_rule_id = rule.rule_id

                    asset = CryptoAsset.create(
                        name=f"{algorithm} Detection ({library})",
                        category=category,
                        algorithm=algorithm,
                        file_path=str(file_path),
                        line_number=idx,
                        code_snippet=code_snippet,
                        library=library,
                        confidence=confidence,
                        language=language,
                        detection_mechanism=detection_mechanism,
                        matched_rule_id=matched_rule_id,
                        key_length=key_length,
                        mode=mode,
                        padding=padding,
                        root_dir=effective_root,
                        purpose=purpose,
                        protocol=protocol,
                        detection_rule=rule.rule_id,
                    )
                    assets.append(asset)

        return self._deduplicate_assets(assets)

    def scan_file(
        self,
        file_path: Path,
        root_dir: Optional[Union[str, Path]] = None,
    ) -> List[CryptoAsset]:
        """Perform full scan on a single file combining AST, certificate, and Regex detection."""
        effective_root = root_dir or self.root_dir
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []

        lines = content.splitlines()
        language = self._determine_language(file_path)

        # Certificate / key file parsing (PEM/DER/CRT/KEY/CER files)
        if language == "pem":
            try:
                from ecdat.detectors.certificates import scan_certificate_file
                cert_assets = scan_certificate_file(file_path, content, root_dir=effective_root)
                if cert_assets:
                    return cert_assets
            except Exception:
                pass
            # Fallback to regex scan for PEM marker detection
            return self.scan_file_regex(file_path, lines, root_dir=effective_root)

        regex_assets = self.scan_file_regex(file_path, lines, root_dir=effective_root)

        # Run AST parser for Python files
        if language == "python":
            ast_assets = scan_python_ast(str(file_path), content, root_dir=effective_root)

            # Deduplicate / merge AST and Regex hits on the same line and algorithm
            ast_lines_algos = {(a.line_number, a.algorithm) for a in ast_assets}
            filtered_regex_assets = [
                r for r in regex_assets if (r.line_number, r.algorithm) not in ast_lines_algos
            ]
            return self._deduplicate_assets(ast_assets + filtered_regex_assets)

        return self._deduplicate_assets(regex_assets)

    def scan(self, target_path: Union[str, Path]) -> List[CryptoAsset]:
        """Scan target directory or file and return normalized CryptoAssets."""
        target = Path(target_path)
        effective_root = self.root_dir or (target if target.is_dir() else target.parent)
        files = self.discover_files(target_path)
        all_assets: List[CryptoAsset] = []

        for file_path in files:
            file_assets = self.scan_file(file_path, root_dir=effective_root)
            all_assets.extend(file_assets)

        return all_assets
