#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

cd "$repo_root/apps/api"
pip install -r requirements.txt

cd "$repo_root/apps/web"
npm install
