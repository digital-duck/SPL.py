#!/usr/bin/env bash
# migrate_pocketflow.sh — thin conda wrapper for migrate_pocketflow.py
#
# Usage (from any directory):
#   bash cookbook-pocketflow/migrate_pocketflow.sh [subcommand] [options]
#
# Examples:
#   bash cookbook-pocketflow/migrate_pocketflow.sh list
#   bash cookbook-pocketflow/migrate_pocketflow.sh migrate --phase phase1
#   bash cookbook-pocketflow/migrate_pocketflow.sh migrate --recipe 001,002 --model qwen/qwen3.6-plus
#   bash cookbook-pocketflow/migrate_pocketflow.sh validate --phase phase1
#   bash cookbook-pocketflow/migrate_pocketflow.sh report

cd "$(dirname "$0")/.." || exit 1
conda run -n spl123 python cookbook-pocketflow/migrate_pocketflow.py "$@"
