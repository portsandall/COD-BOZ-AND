#!/usr/bin/env python3
"""Inventory Marmalade DTRZ (.dz) assets for the BOZ Nuketown feasibility pass.

Read-only: never extracts, decrypts, edits or republishes third-party assets.
Only DTRZ header/index metadata is parsed; .group.bin payloads remain opaque.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

MAX_ENTRIES = 65535
MAX_NAME_BYTES = 4096


class DTRZError(ValueError):
    pass


def _exact(f, length: int) -> bytes:
    data = f.read(length)
    if len(data) != length:
        raise DTRZError("truncated DTRZ index")
    return data


def _u16(f) -> int:
    return struct.unpack("<H", _exact(f, 2))[0]


def _u32(f) -> int:
    return struct.unpack("<I", _exact(f, 4))[0]


def _zstr(f, size: int) -> str:
    raw = bytearray()
    for _ in range(MAX_NAME_BYTES):
        ch = _exact(f, 1)
        if ch == b"\x00":
            return raw.decode("utf-8", errors="replace")
        raw.extend(ch)
        if f.tell() >= size:
            raise DTRZError("unterminated DTRZ name")
    raise DTRZError("DTRZ name exceeds safety limit")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_dtrz(path: Path) -> dict:
    size = path.stat().st_size
    with path.open("rb") as f:
        if _exact(f, 4) != b"DTRZ":
            raise DTRZError("not a DTRZ Marmalade resource archive")
        count = _u16(f)
        folder_count = _u16(f)
        if not (0 < count <= MAX_ENTRIES):
            raise DTRZError("DTRZ index contains no files")
        if not (1 <= folder_count <= MAX_ENTRIES):
            raise DTRZError("invalid folder count")
        if _exact(f, 1) != b"\x00":
            raise DTRZError("unsupported DTRZ string table header")
        names = [_zstr(f, size) for _ in range(count)]
        folders = [""] + [_zstr(f, size) for _ in range(folder_count - 1)]
        attrs = [(_u16(f), _u16(f), _u16(f)) for _ in range(count)]
        index_reserved = _u16(f)
        length_count = _u16(f)
        spans = [(_u32(f), _u32(f), _u32(f), _u32(f)) for _ in range(count)]
        index_end = f.tell()
        if index_end > size:
            raise DTRZError("DTRZ index extends beyond archive")
        files = []
        for i, (folder, slot, flags) in enumerate(attrs):
            offset, length0, length1, marker = spans[i]
            if folder >= len(folders):
                raise DTRZError(f"file {i}: invalid folder index {folder}")
            if offset < index_end or offset >= size:
                raise DTRZError(f"file {i}: offset {offset} outside payload region")
            next_offset = spans[i + 1][0] if i + 1 < count else size
            if next_offset <= offset or next_offset > size:
                raise DTRZError(f"file {i}: invalid following file offset")
            raw_folder = folders[folder]
            files.append({
                "name": names[i],
                "folder": raw_folder,
                "path": (raw_folder.strip("\\/") + "/" if raw_folder else "") + names[i],
                "offset": offset,
                "compressed_span_bytes": next_offset - offset,
                "reported_length0": length0,
                "reported_length1": length1,
                "flags": flags,
                "slot": slot,
                "marker": marker,
            })
        for entry in files:
            f.seek(entry["offset"])
            entry["gzip_header"] = f.read(2) == b"\x1f\x8b"

    groups = [x["path"] for x in files if x["name"].lower().endswith(".group.bin")]
    map_names = ["kino", "ascension", "callofthedead", "nuketown", "zm_nuked"]
    map_candidates = {map_name: sorted(path for path in groups if map_name in path.lower())
                      for map_name in map_names}
    return {
        "schema_version": 1,
        "archive": str(path),
        "format": "Marmalade DTRZ",
        "size_bytes": size,
        "sha256": sha256_file(path),
        "file_count": count,
        "folder_count_including_root": folder_count,
        "length_count_field": length_count,
        "index_reserved": index_reserved,
        "index_end": index_end,
        "group_bin_count": len(groups),
        "map_candidates": map_candidates,
        "files": files,
    }


def fingerprint_source(path: Path) -> dict:
    """Fingerprint a user-provided BO2 fastfile without interpreting its format."""
    with path.open("rb") as f:
        header = f.read(32)
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "header_hex": header.hex(),
        "format": "opaque BO2 input (not converted)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="Existing legally acquired Black Ops Zombies .dz archive")
    parser.add_argument("--bo2-fastfile", type=Path,
                        help="Optional source zm_nuked.ff (fingerprint only)")
    parser.add_argument("--json-out", type=Path, default=Path("nuketown-inventory.json"))
    args = parser.parse_args(argv)
    try:
        result = {"mobile_dz": read_dtrz(args.archive)}
        if args.bo2_fastfile:
            result["bo2_fastfile"] = fingerprint_source(args.bo2_fastfile)
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (DTRZError, FileNotFoundError, PermissionError, OSError) as exc:
        print(f"Inventory failed: {exc}", file=sys.stderr)
        return 2
    dz = result["mobile_dz"]
    print(f"DTRZ index: {dz['file_count']} files, {dz['group_bin_count']} .group.bin files")
    for map_name, groups in dz["map_candidates"].items():
        print(f"  {map_name}: {len(groups)} candidate(s)")
    print(f"Wrote metadata only: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
