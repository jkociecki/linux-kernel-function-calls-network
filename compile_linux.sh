#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LINUX_DIR="$ROOT_DIR/data/linux"
CONFIG_TARGET="defconfig"
JOBS="$(nproc)"

usage() {
	cat <<EOF
Usage: bash compile_linux.sh [--config defconfig|allmodconfig|allyesconfig|existing] [--jobs N]

Options:
	--config   Kernel config target to use before build (default: defconfig)
						 existing = do not regenerate config, require data/linux/.config
	--jobs     Number of parallel jobs for make (default: nproc)
	-h, --help Show this help
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--config)
			CONFIG_TARGET="$2"
			shift 2
			;;
		--jobs)
			JOBS="$2"
			shift 2
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown argument: $1" >&2
			usage
			exit 1
			;;
	esac
done

cd "$LINUX_DIR"

# Ensure we have a valid kernel config before building.
case "$CONFIG_TARGET" in
	defconfig|allmodconfig|allyesconfig)
		make "$CONFIG_TARGET"
		;;
	existing)
		if [[ ! -f .config ]]; then
			echo "Missing .config and --config existing was requested" >&2
			exit 1
		fi
		make olddefconfig
		;;
	*)
		echo "Unsupported --config value: $CONFIG_TARGET" >&2
		usage
		exit 1
		;;
esac

# Remove old dumps to avoid mixing previous runs with current results.
find . -type f -name "*.expand" -delete

make -j"$JOBS" KCFLAGS="-fdump-rtl-expand"