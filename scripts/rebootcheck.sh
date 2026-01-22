#!/bin/bash
LOADED_KERNEL=$(uname -r)
INSTALLED_KERNEL=$(file /boot/vmlinuz-linux | awk '{print $9}')

  if [ ! "${LOADED_KERNEL}" = "${INSTALLED_KERNEL}" ]; then
    echo "Reboot required $LOADED_KERNEL is outdated."
else
	echo "No reboot required."
  fi
