#!/usr/bin/env bash
# Bash-first infrastructure heartbeat for rumahgadang
# Runs every 30 minutes. Zero LLM calls if all OK.
# Only calls nanobot agent when issues are detected.

set -euo pipefail

ISSUES=()

# ─── 1. Service checks ────────────────────────────────────────────────────────
SERVICES=(
    "whatsapp-bot"
    "cuk-infra"
    "agent-os"
    "hermes-shim"
    "meridian"
    "paperclip"
    "meutia-shim"
    "meridian-shim"
)

for svc in "${SERVICES[@]}"; do
    status=$(systemctl is-active "$svc" 2>/dev/null || echo "unknown")
    if [[ "$status" != "active" ]]; then
        ISSUES+=("[critical] Service $svc is $status")
    fi
done

# ─── 2. Health endpoint checks ────────────────────────────────────────────────
declare -A ENDPOINTS=(
    ["whatsapp-bot"]="http://localhost:8000/health"
    ["agent-os"]="http://localhost:7777/health"
    ["meutia-shim"]="http://localhost:8642/health"
    ["meridian-shim"]="http://localhost:8643/health"
    ["paperclip"]="http://localhost:3100/api/health"
)

for name in "${!ENDPOINTS[@]}"; do
    url="${ENDPOINTS[$name]}"
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null || echo "000")
    if [[ "$code" != "200" ]]; then
        ISSUES+=("[warning] Health endpoint $name ($url) returned $code")
    fi
done

# ─── 3. Disk check ────────────────────────────────────────────────────────────
while IFS= read -r line; do
    usage=$(echo "$line" | awk '{print $5}' | tr -d '%')
    mount=$(echo "$line" | awk '{print $6}')
    if [[ -n "$usage" && "$usage" -gt 80 ]]; then
        ISSUES+=("[warning] Disk $mount at ${usage}% used")
    fi
done < <(df -h --output=source,size,used,avail,pcent,target 2>/dev/null | tail -n +2 | grep -v tmpfs | grep -v udev)

# ─── 4. Memory check ─────────────────────────────────────────────────────────
avail_mb=$(free -m 2>/dev/null | awk 'NR==2 {print $7}')
if [[ -n "$avail_mb" && "$avail_mb" -lt 200 ]]; then
    ISSUES+=("[critical] Memory critically low: ${avail_mb}MB available")
elif [[ -n "$avail_mb" && "$avail_mb" -lt 500 ]]; then
    ISSUES+=("[warning] Memory low: ${avail_mb}MB available")
fi

# ─── 5. Failed systemd units ─────────────────────────────────────────────────
failed_units=$(systemctl --failed --no-pager --no-legend 2>/dev/null | grep -v "^$" | wc -l)
if [[ "$failed_units" -gt 0 ]]; then
    unit_list=$(systemctl --failed --no-pager --no-legend 2>/dev/null | awk '{print $1}' | tr '\n' ' ')
    ISSUES+=("[warning] $failed_units failed systemd unit(s): $unit_list")
fi

# ─── 6. Decision ─────────────────────────────────────────────────────────────
if [[ ${#ISSUES[@]} -eq 0 ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Heartbeat OK — all checks passed"
    exit 0
fi

# ─── 7. Issues found — build report and call nanobot ─────────────────────────
REPORT="Infrastructure heartbeat detected issues on rumahgadang:\n\n"
for issue in "${ISSUES[@]}"; do
    REPORT+="• $issue\n"
done
REPORT+="\nTimestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Heartbeat ISSUES found: ${#ISSUES[@]}"
echo -e "$REPORT"

# Call nanobot agent to diagnose and send Telegram alert
# nanobot processes the message through the full agent loop
# which has access to exec tools and will send the alert via configured channels
doppler run -p cuk_infra -c prd -- /opt/cuk_infra/venv/bin/nanobot agent \
    --config /opt/cuk_infra/.nanobot/config.json \
    -m "$(echo -e "$REPORT")" 2>&1 || true

exit 0
