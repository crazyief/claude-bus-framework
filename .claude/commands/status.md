# Status Command

Show current project status and active alerts.

## Usage
```
/status
```

## Steps

1. **Read Project Status**
   ```bash
   cat todo/PROJECT_STATUS.md | head -50
   ```

2. **Check Active Alerts**
   ```bash
   python3 .claude-bus/scripts/alert_manager.py list
   ```

3. **Show Current Position**
   - Current Stage
   - Current Phase
   - Phase status (in progress / completed)

4. **List Recent Activity**
   - Last 5 events from events.jsonl (if exists)

5. **Show Blockers**
   - Any critical/high alerts
   - Any pending gate requirements

## Output Format
```
=== Project Status ===
Stage: {N} | Phase: {P} | Status: {status}

Active Alerts: {count}
- [severity] message

Next Steps:
- {recommended action}
```
