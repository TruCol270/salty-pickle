#!/usr/bin/env bash

set -euo pipefail

api_base="${1:-${API_PUBLIC_URL:-}}"

if [[ -z "$api_base" ]]; then
  echo "Usage: $0 https://api.yourdomain.com"
  echo "   or set API_PUBLIC_URL env var."
  exit 1
fi

api_base="${api_base%/}"

echo "Set these callback URLs in provider dashboards (must match STRAVA_/GOOGLE_/WHOOP_REDIRECT_URI):"
echo
echo "Strava: ${api_base}/auth/strava/callback"
echo "Google: ${api_base}/auth/google/callback"
echo "Whoop:  ${api_base}/auth/whoop/callback"
echo
echo "Docs: docs/deploy/oauth-provider-setup.md"
