#!/usr/bin/env bash

set -euo pipefail

API_BASE=""
APP_BASE=""
DRY_RUN=false
ACCESS_TOKEN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-base)
      API_BASE="${2:-}"
      shift 2
      ;;
    --app-base)
      APP_BASE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --access-token)
      ACCESS_TOKEN="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$API_BASE" || -z "$APP_BASE" ]]; then
  echo "Usage: $0 --api-base https://api.example.com --app-base https://app.example.com [--access-token <jwt>] [--dry-run]"
  exit 1
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run mode"
  echo "  API health URL: ${API_BASE%/}/live"
  echo "  API ready URL:  ${API_BASE%/}/healthz"
  echo "  App login URL:  ${APP_BASE%/}/login"
  echo "  Strava auth:    ${API_BASE%/}/auth/strava/authorize?redirect_url=${APP_BASE%/}/integrations"
  echo "  Google auth:    POST ${API_BASE%/}/auth/google/authorize-url (Bearer required)"
  echo "  Whoop auth:     POST ${API_BASE%/}/auth/whoop/authorize-url (Bearer required)"
  exit 0
fi

echo "== API Liveness =="
curl -fsS "${API_BASE%/}/live" | sed 's/^/  /'
echo

echo "== API Readiness =="
curl -fsS "${API_BASE%/}/healthz" | sed 's/^/  /'
echo

echo "== App Reachability =="
curl -fsSI "${APP_BASE%/}/login" | grep -Ei "HTTP/|location|content-type" || true
echo

echo "== OAuth Authorize Endpoint Reachability =="
strava_url="${API_BASE%/}/auth/strava/authorize?redirect_url=${APP_BASE%/}/integrations"

curl -fsSI "$strava_url" | grep -Ei "HTTP/|location" || true
if [[ -n "$ACCESS_TOKEN" ]]; then
  google_payload="{\"redirect_url\":\"${APP_BASE%/}/integrations\"}"
  whoop_payload="{\"redirect_url\":\"${APP_BASE%/}/integrations\"}"
  curl -fsS -X POST "${API_BASE%/}/auth/google/authorize-url" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$google_payload" | grep -Ei "auth_url" || true
  curl -fsS -X POST "${API_BASE%/}/auth/whoop/authorize-url" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$whoop_payload" | grep -Ei "auth_url" || true
else
  echo "Skipping Google/Whoop authorize-url checks (no --access-token provided)."
fi
echo

echo "Smoke checks completed. Run manual OAuth and plan-sync checks in browser."
