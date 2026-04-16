#!/usr/bin/env bash

set -u

finish() {
  exit "$1"
}

kernel="$(uname -r 2>/dev/null || true)"
os="$(uname -s 2>/dev/null || true)"

[ -n "$kernel" ] && [ -n "$os" ] || finish 2

case "$os" in
  Linux)
    [ -f /run/reboot-required ] || [ -f /var/run/reboot-required ] && finish 1

    [ -d /lib/modules ] || finish 2

    latest_kernel="$(
      find /lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null |
        sort -V |
        tail -n 1
    )"

    [ -n "$latest_kernel" ] || finish 2
    [ "$kernel" = "$latest_kernel" ] && finish 0
    finish 1
    ;;
  *)
    finish 2
    ;;
esac
