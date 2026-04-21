# !/bin/bash

cd data/linux
make -j$(nproc) KCFLAGS="-fdump-rtl-expand" 2>/dev/null