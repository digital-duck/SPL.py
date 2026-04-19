#!/usr/bin/env bash

python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog.json 2>&1 | tee cookbook/logs/run_all_single-GPU-spl3_$(date +%Y%m%d_%H%M%S).md

python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-go.json 2>&1 | tee cookbook/logs/run_all_single-GPU-go_$(date +%Y%m%d_%H%M%S).md

python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog-ts.json 2>&1 | tee cookbook/logs/run_all_single-GPU-ts_$(date +%Y%m%d_%H%M%S).md