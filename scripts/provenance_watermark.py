#!/usr/bin/env python3
"""Create and verify render-invisible Ed25519 provenance marks for a Skill bundle."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
except ImportError as exc:  # pragma: no cover - dependency gate
    raise SystemExit(
        "Missing dependency 'cryptography'. Run with: "
        "uv run --with cryptography python scripts/provenance_watermark.py ..."
    ) from exc


SCHEMA_VERSION = 1
MANIFEST_NAME = ".skill-watermark.json"
MARKER_PREFIX = "<!-- skill-provenance:v1;"
MARKER_RE = re.compile(r"(?m)^\s*<!-- skill-provenance:v1;[^\r\n]*-->\s*$")
TEXT_EXTENSIONS = {
    ".md",
    ".py",
    ".m",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".txt",
    ".toml",
    ".ini",
    ".cfg",
    ".gitattributes",
    ".gitignore",
}
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".log"}
IGNORED_NAMES = {MANIFEST_NAME, ".DS_Store"}


class VerificationError(RuntimeError):
    pass


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def strip_marker(text: str) -> str:
    cleaned = MARKER_RE.sub("", text)
    return cleaned.rstrip() + "\n"


def canonical_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS or path.name in {"SKILL.md", "README.md", ".gitignore", ".gitattributes"}:
        text = raw.decode("utf-8-sig")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return strip_marker(text).encode("utf-8")
    return raw


def digest_file(path: Path) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def iter_bundle_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.name in IGNORED_NAMES or path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def collect_hashes(root: Path) -> list[dict[str, str]]:
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": digest_file(path)}
        for path in iter_bundle_files(root)
    ]


def bundle_digest(entries: list[dict[str, str]]) -> str:
    payload = b"".join(
        entry["path"].encode("utf-8") + b"\0" + entry["sha256"].encode("ascii") + b"\n"
        for entry in entries
    )
    return hashlib.sha256(payload).hexdigest()


def file_message(watermark_id: str, relative_path: str, file_digest: str) -> bytes:
    return (
        b"skill-file-watermark-v1\0"
        + watermark_id.encode("utf-8")
        + b"\0"
        + relative_path.encode("utf-8")
        + b"\0"
        + bytes.fromhex(file_digest)
    )


def bundle_message(watermark_id: str, digest: str) -> bytes:
    return b"skill-bundle-watermark-v1\0" + watermark_id.encode("utf-8") + b"\0" + bytes.fromhex(digest)


def load_private_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("The private key is not an Ed25519 key")
    return key


def public_raw(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def create_key(private_key_path: Path, force: bool = False) -> None:
    if private_key_path.exists() and not force:
        raise FileExistsError(f"Private key already exists: {private_key_path}")
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    private_key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_path = private_key_path.with_suffix(".pub")
    public_path.write_text(b64(public_raw(key.public_key())) + "\n", encoding="ascii")
    print(f"Private key: {private_key_path}")
    print(f"Public key:  {public_path}")


def make_marker(
    *,
    owner: str,
    watermark_id: str,
    relative_path: str,
    file_digest: str,
    public_key: bytes,
    signature: bytes,
) -> str:
    values = {
        "owner": owner,
        "id": watermark_id,
        "path": relative_path,
        "sha256": file_digest,
        "pub": b64(public_key),
        "sig": b64(signature),
    }
    fields = ";".join(f"{key}={value}" for key, value in values.items())
    return f"{MARKER_PREFIX}{fields} -->"


def parse_marker(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    matches = MARKER_RE.findall(text)
    if len(matches) != 1:
        raise VerificationError(f"Expected one watermark marker in {path}, found {len(matches)}")
    marker = matches[0].strip()
    body = marker[len(MARKER_PREFIX) : -3].strip()
    values: dict[str, str] = {}
    for field in body.split(";"):
        key, separator, value = field.partition("=")
        if not separator:
            raise VerificationError(f"Malformed watermark field in {path}: {field}")
        values[key] = value
    required = {"owner", "id", "path", "sha256", "pub", "sig"}
    missing = required - values.keys()
    if missing:
        raise VerificationError(f"Missing watermark fields in {path}: {sorted(missing)}")
    return values


def write_marker(
    path: Path,
    *,
    owner: str,
    watermark_id: str,
    relative_path: str,
    private_key: Ed25519PrivateKey,
    public_key: bytes,
) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    canonical_text = strip_marker(text)
    file_digest = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    signature = private_key.sign(file_message(watermark_id, relative_path, file_digest))
    marker = make_marker(
        owner=owner,
        watermark_id=watermark_id,
        relative_path=relative_path,
        file_digest=file_digest,
        public_key=public_key,
        signature=signature,
    )
    path.write_text(canonical_text.rstrip() + "\n\n" + marker + "\n", encoding="utf-8", newline="\n")
    return {"path": relative_path, "sha256": file_digest, "signature": b64(signature)}


def stamp(
    *,
    root: Path,
    private_key_path: Path,
    owner: str,
    watermark_id: str,
    repository: str,
    marker_files: list[str],
) -> None:
    root = root.resolve()
    private_key = load_private_key(private_key_path)
    raw_public = public_raw(private_key.public_key())
    marked: list[dict[str, str]] = []
    for relative_path in marker_files:
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        marked.append(
            write_marker(
                path,
                owner=owner,
                watermark_id=watermark_id,
                relative_path=Path(relative_path).as_posix(),
                private_key=private_key,
                public_key=raw_public,
            )
        )

    entries = collect_hashes(root)
    digest = bundle_digest(entries)
    signature = private_key.sign(bundle_message(watermark_id, digest))
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "watermark_type": "render-invisible-ed25519-provenance",
        "owner": owner,
        "watermark_id": watermark_id,
        "repository": repository,
        "algorithm": "Ed25519",
        "canonical_hash": "SHA-256",
        "signed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "public_key_base64": b64(raw_public),
        "bundle_sha256": digest,
        "bundle_signature_base64": b64(signature),
        "file_count": len(entries),
        "signed_files": entries,
        "marker_files": marked,
        "private_key_committed": False,
    }
    (root / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Stamped {len(entries)} files with watermark {watermark_id}")
    print(f"Bundle SHA-256: {digest}")
    print(f"Manifest: {root / MANIFEST_NAME}")


def verify_marker(path: Path, expected_public_key: bytes | None = None) -> dict[str, str]:
    values = parse_marker(path)
    digest = digest_file(path)
    if digest != values["sha256"]:
        raise VerificationError(f"File digest mismatch: {path}")
    raw_public = unb64(values["pub"])
    if expected_public_key is not None and raw_public != expected_public_key:
        raise VerificationError(f"Public key mismatch: {path}")
    key = Ed25519PublicKey.from_public_bytes(raw_public)
    try:
        key.verify(
            unb64(values["sig"]),
            file_message(values["id"], values["path"], values["sha256"]),
        )
    except InvalidSignature as exc:
        raise VerificationError(f"Invalid file signature: {path}") from exc
    return values


def verify_bundle(root: Path) -> None:
    root = root.resolve()
    manifest_path = root / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise VerificationError("Unsupported watermark schema")
    raw_public = unb64(manifest["public_key_base64"])
    expected_entries = manifest["signed_files"]
    current_entries = collect_hashes(root)
    if current_entries != expected_entries:
        expected = {item["path"]: item["sha256"] for item in expected_entries}
        current = {item["path"]: item["sha256"] for item in current_entries}
        added = sorted(current.keys() - expected.keys())
        removed = sorted(expected.keys() - current.keys())
        changed = sorted(path for path in current.keys() & expected.keys() if current[path] != expected[path])
        raise VerificationError(f"Bundle changed; added={added}, removed={removed}, changed={changed}")

    digest = bundle_digest(current_entries)
    if digest != manifest["bundle_sha256"]:
        raise VerificationError("Bundle digest mismatch")
    key = Ed25519PublicKey.from_public_bytes(raw_public)
    try:
        key.verify(
            unb64(manifest["bundle_signature_base64"]),
            bundle_message(manifest["watermark_id"], digest),
        )
    except InvalidSignature as exc:
        raise VerificationError("Invalid bundle signature") from exc

    for marker in manifest["marker_files"]:
        values = verify_marker(root / marker["path"], expected_public_key=raw_public)
        if values["id"] != manifest["watermark_id"] or values["owner"] != manifest["owner"]:
            raise VerificationError(f"Marker identity mismatch: {marker['path']}")

    print("Watermark: VALID")
    print(f"Owner: {manifest['owner']}")
    print(f"Watermark ID: {manifest['watermark_id']}")
    print(f"Repository: {manifest['repository']}")
    print(f"Bundle SHA-256: {digest}")
    print(f"Signed files: {len(current_entries)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    key_parser = subparsers.add_parser("init-key", help="Generate an Ed25519 signing key")
    key_parser.add_argument("--private-key", type=Path, required=True)
    key_parser.add_argument("--force", action="store_true")

    stamp_parser = subparsers.add_parser("stamp", help="Stamp a Skill bundle")
    stamp_parser.add_argument("--root", type=Path, default=Path.cwd())
    stamp_parser.add_argument("--private-key", type=Path, required=True)
    stamp_parser.add_argument("--owner", default="YANG985-CMD")
    stamp_parser.add_argument("--watermark-id", default="YANG985-CMD-MMS-2026-v1")
    stamp_parser.add_argument("--repository", default="https://github.com/YANG985-CMD/Math-Modeling-Solver")
    stamp_parser.add_argument("--marker-file", action="append", dest="marker_files", default=[])

    verify_parser = subparsers.add_parser("verify", help="Verify a stamped Skill bundle")
    verify_parser.add_argument("--root", type=Path, default=Path.cwd())

    file_parser = subparsers.add_parser("verify-file", help="Verify one independently marked file")
    file_parser.add_argument("path", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "init-key":
            create_key(args.private_key, force=args.force)
        elif args.command == "stamp":
            marker_files = args.marker_files or ["SKILL.md", "README.md"]
            stamp(
                root=args.root,
                private_key_path=args.private_key,
                owner=args.owner,
                watermark_id=args.watermark_id,
                repository=args.repository,
                marker_files=marker_files,
            )
        elif args.command == "verify":
            verify_bundle(args.root)
        elif args.command == "verify-file":
            values = verify_marker(args.path)
            print("Watermark: VALID")
            print(f"Owner: {values['owner']}")
            print(f"Watermark ID: {values['id']}")
            print(f"Path claim: {values['path']}")
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, KeyError, json.JSONDecodeError, VerificationError) as exc:
        print(f"Watermark: INVALID ({exc})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
