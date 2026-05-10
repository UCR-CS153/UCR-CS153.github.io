#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  exec sudo --preserve-env=DEBIAN_FRONTEND "$0" "$@"
fi

export DEBIAN_FRONTEND=noninteractive

# Avoid stale third-party apt entries breaking `apt update` in some images.
rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn-stable.list || true

apt-get update
apt-get upgrade -y

# Core: xv6 is RISC-V (rv64). Needs qemu-system-riscv64 + riscv64-unknown-elf toolchain.
# gcc-riscv64-unknown-elf pulls binutils-riscv64-unknown-elf.
# gdb-multiarch: remote debug to QEMU's RISC-V stub ("target remote").
# build-essential + perl + python3: host gcc for mkfs/notxv6, usys.pl, grade scripts.
apt-get install -y --no-install-recommends \
  build-essential \
  ca-certificates \
  gcc-riscv64-unknown-elf \
  gdb-multiarch \
  git \
  make \
  perl \
  python3 \
  qemu-system-misc

# Allow loading project-local .gdbinit (GDB 8+ safe-path); xv6 generates ./.gdbinit for qemu-gdb.
if [[ ! -f /root/.gdbinit ]] || ! grep -q 'auto-load safe-path' /root/.gdbinit 2>/dev/null; then
  echo 'set auto-load safe-path /' >> /root/.gdbinit
fi

# Non-root login users (if any): allow project .gdbinit.
shopt -s nullglob
for homedir in /home/*; do
  [[ -d "$homedir" ]] || continue
  gfile="$homedir/.gdbinit"
  if [[ ! -f "$gfile" ]] || ! grep -q 'auto-load safe-path' "$gfile" 2>/dev/null; then
    echo 'set auto-load safe-path /' >> "$gfile"
    chown "$(stat -c '%u:%g' "$homedir")" "$gfile" 2>/dev/null || true
  fi
done
shopt -u nullglob

echo
echo "Sanity check (expect riscv64 / qemu-system-riscv64):"
command -v riscv64-unknown-elf-gcc && riscv64-unknown-elf-gcc --version | head -1
command -v qemu-system-riscv64 && qemu-system-riscv64 --version | head -1
command -v gdb-multiarch && gdb-multiarch --version | head -1
echo
echo "Done. Build from repo root: make qemu"
