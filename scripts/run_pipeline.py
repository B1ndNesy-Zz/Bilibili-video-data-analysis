from __future__ import annotations

import argparse

import path_setup  # noqa: F401
from config.settings import COMMENT_TARGET_COUNT, ensure_directories
from scripts.collect_bilibili import collect_all
from scripts.import_to_mysql import import_all
from scripts.process_data import process_all


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect, process, analyze and load Bilibili public video data."
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=COMMENT_TARGET_COUNT,
        help="Maximum public comments to collect.",
    )
    parser.add_argument(
        "--skip-collect",
        action="store_true",
        help="Use existing raw/processed collection files and rerun analysis only.",
    )
    parser.add_argument(
        "--no-mysql",
        action="store_true",
        help="Skip MySQL import and only generate CSV outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_directories()
    if not args.skip_collect:
        collect_all(max_comments=args.max_comments)
    else:
        print("[pipeline] skip collection, reuse existing files")

    process_all()

    if not args.no_mysql:
        import_all()
    else:
        print("[pipeline] skip MySQL import")

    print("[pipeline] done")


if __name__ == "__main__":
    main()
