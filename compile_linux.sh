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

# IKHEADERS tars all kernel headers into a module; it fails when some header
# files lack read permissions in this environment.  We don't need it for the
# call-graph pipeline, so disable it unconditionally.
scripts/config --disable IKHEADERS
make olddefconfig

# Ensure header files are readable so the build doesn't abort on permission errors.
find include -type f ! -readable -exec chmod a+r {} +

# Remove old dumps and object files to force full recompilation.
# Without this, make skips already-built .o files and generates no .expand dumps.
# Remove old dumps and all compiled artifacts to force full recompilation.
# We cannot rely on "make clean" because Documentation/Kbuild is a directory
# in this tree and causes make clean to abort early.
find . -type f \( -name "*.expand" -o -name "*.o" -o -name "*.a" \
	-o -name "*.ko" -o -name "*.mod" -o -name "*.mod.c" \
	-o -name "vmlinux" -o -name "vmlinux.o" \) -delete

make -k -j"$JOBS" KCFLAGS="-fdump-rtl-expand" || true