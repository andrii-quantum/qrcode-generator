#!/usr/bin/env python3
"""Generate QR codes for websites from their DNS names.

Examples:
    python qrcode_generator.py example.com quantum.media
    python qrcode_generator.py -f domains.txt -o qrcodes --scheme http
    python qrcode_generator.py example.com --format svg --fill "#1a1a1a"
"""

import argparse
import re
import sys
from pathlib import Path

import qrcode
import qrcode.image.svg
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

ERROR_LEVELS = {
    "L": ERROR_CORRECT_L,  # ~7% recovery
    "M": ERROR_CORRECT_M,  # ~15% recovery
    "Q": ERROR_CORRECT_Q,  # ~25% recovery
    "H": ERROR_CORRECT_H,  # ~30% recovery
}

# One DNS label: 1-63 chars, alphanumeric or hyphen, no leading/trailing hyphen.
LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


def normalize_domain(raw: str) -> str:
    """Strip scheme, path, port and trailing dot; return a lowercase DNS name."""
    domain = raw.strip().lower()
    domain = re.sub(r"^[a-z][a-z0-9+.-]*://", "", domain)
    domain = domain.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    domain = domain.split(":", 1)[0].rstrip(".")
    try:
        domain = domain.encode("idna").decode("ascii")  # support internationalized names
    except UnicodeError as exc:
        raise ValueError(f"invalid DNS name: {raw!r}") from exc
    return domain


def validate_domain(domain: str) -> None:
    labels = domain.split(".")
    if len(domain) > 253 or len(labels) < 2 or not all(LABEL_RE.match(label) for label in labels):
        raise ValueError(f"invalid DNS name: {domain!r}")


def build_url(domain: str, scheme: str) -> str:
    return f"{scheme}://{domain}"


def make_qr(data: str, args: argparse.Namespace):
    qr = qrcode.QRCode(
        error_correction=ERROR_LEVELS[args.error_correction],
        box_size=args.box_size,
        border=args.border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    if args.format == "svg":
        return qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    return qr.make_image(fill_color=args.fill, back_color=args.background)


def read_domains(args: argparse.Namespace) -> list[str]:
    domains = list(args.domains)
    if args.file:
        for line in Path(args.file).read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                domains.append(line)
    return domains


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate QR codes for websites by DNS name.")
    parser.add_argument("domains", nargs="*", help="DNS names, e.g. example.com www.example.org")
    parser.add_argument("-f", "--file", help="text file with one DNS name per line (# for comments)")
    parser.add_argument("-o", "--output-dir", default="qrcodes", help="output directory (default: qrcodes)")
    parser.add_argument("--scheme", choices=["https", "http"], default="https", help="URL scheme (default: https)")
    parser.add_argument("--format", choices=["png", "svg"], default="png", help="image format (default: png)")
    parser.add_argument("--box-size", type=int, default=10, help="pixels per QR module (default: 10)")
    parser.add_argument("--border", type=int, default=4, help="quiet-zone width in modules (default: 4)")
    parser.add_argument("--error-correction", choices=ERROR_LEVELS, default="M", help="error correction level (default: M)")
    parser.add_argument("--fill", default="black", help="foreground color, PNG only (default: black)")
    parser.add_argument("--background", default="white", help="background color, PNG only (default: white)")
    args = parser.parse_args(argv)
    if not args.domains and not args.file:
        parser.error("provide at least one DNS name or --file")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    seen = set()
    for raw in read_domains(args):
        try:
            domain = normalize_domain(raw)
            validate_domain(domain)
        except ValueError as exc:
            print(f"skip: {exc}", file=sys.stderr)
            failures += 1
            continue
        if domain in seen:
            continue
        seen.add(domain)

        url = build_url(domain, args.scheme)
        path = output_dir / f"{domain}.{args.format}"
        make_qr(url, args).save(path)
        print(f"{url} -> {path}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
