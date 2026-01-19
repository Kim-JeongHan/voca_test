#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
build_dir="$root_dir/build"
mode="${MODE:-}"

usage() {
  echo "Usage: $0 <simple|multiple> [file_numbers...]"
  echo "       $0 --test"
  echo "Example: $0 simple 1"
  echo "         $0 multiple 1 2 3"
  echo "Optional: MODE=1 $0 simple 1"
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if [[ ! -d "$build_dir" ]]; then
  echo "Build directory not found. Run ./build.sh first."
  exit 1
fi

if [[ "$1" == "--test" ]]; then
  (cd "$build_dir" && ctest --output-on-failure)
  exit 0
fi

cmd=""
case "$1" in
  simple)
    cmd="./simple"
    ;;
  multiple)
    cmd="./multiple"
    ;;
  *)
    echo "Unknown target: $1"
    usage
    exit 1
    ;;
esac
shift

if [[ -n "$mode" ]]; then
  (cd "$build_dir" && printf "%s\n" "$mode" | "$cmd" "$@")
else
  (cd "$build_dir" && "$cmd" "$@")
fi
