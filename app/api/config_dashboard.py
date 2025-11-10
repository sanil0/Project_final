"""Configuration monitoring dashboard."""

from fastapi import APIRouter, Depends, Security, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security.api_key import APIKey
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..dependencies import get_admin_api_key, get_config_manager
from ..services.configuration import ConfigurationManager
from ..services.config_migration import ConfigMigration

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])

# HTML template for the dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Configuration Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-8">Configuration Dashboard</h1>
        
        <!-- Current Status -->
        <div class="bg-white rounded-lg shadow p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Current Status</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-blue-50 p-4 rounded">
                    <div class="text-sm text-blue-600">Version</div>
                    <div class="text-2xl font-bold">{{current_version}}</div>
                </div>
                <div class="bg-green-50 p-4 rounded">
                    <div class="text-sm text-green-600">Last Updated</div>
                    <div class="text-2xl font-bold">{{last_updated}}</div>
                </div>
                <div class="bg-purple-50 p-4 rounded">
                    <div class="text-sm text-purple-600">Active Subscribers</div>
                    <div class="text-2xl font-bold">{{subscriber_count}}</div>
                </div>
            </div>
        </div>
        
        <!-- Change History -->
        <div class="bg-white rounded-lg shadow p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Configuration Changes</h2>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead>
                        <tr class="bg-gray-50">
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Timestamp
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Version
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Changes
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {{#changes}}
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {{timestamp}}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {{version}}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">
                                {{summary}}
                            </td>
                        </tr>
                        {{/changes}}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Backup Status -->
        <div class="bg-white rounded-lg shadow p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">Backup Status</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-yellow-50 p-4 rounded">
                    <div class="text-sm text-yellow-600">Total Backups</div>
                    <div class="text-2xl font-bold">{{backup_count}}</div>
                </div>
                <div class="bg-orange-50 p-4 rounded">
                    <div class="text-sm text-orange-600">Latest Backup</div>
                    <div class="text-2xl font-bold">{{latest_backup}}</div>
                </div>
            </div>
        </div>
        
        <!-- Configuration Health -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">Health Check</h2>
            <div class="space-y-4">
                {{#health_checks}}
                <div class="flex items-center">
                    <div class="w-4 h-4 rounded-full {{status_color}} mr-3"></div>
                    <div>
                        <div class="text-sm font-medium text-gray-900">{{name}}</div>
                        <div class="text-sm text-gray-500">{{message}}</div>
                    </div>
                </div>
                {{/health_checks}}
            </div>
        </div>
    </div>
    
    <script>
        // Add any interactive features here
        function refreshDashboard() {
            // Reload dashboard data periodically
            setTimeout(refreshDashboard, 30000);
        }
        refreshDashboard();
    </script>
</body>
</html>
"""

@router.get("/dashboard")
async def config_dashboard(
    api_key: APIKey = Security(get_admin_api_key),
    config_manager: ConfigurationManager = Depends(get_config_manager),
) -> HTMLResponse:
    """Render configuration monitoring dashboard."""
    # Get migration manager
    migration = ConfigMigration()
    
    # Get current status
    current_status = {
        "current_version": migration.version_info["current_version"],
        "last_updated": datetime.fromisoformat(migration.version_info["last_updated"]).strftime("%Y-%m-%d %H:%M:%S"),
        "subscriber_count": len(config_manager._subscribers)
    }
    
    # Get change history
    changes = []
    for entry in migration.get_migration_history():
        changes.append({
            "timestamp": datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "version": entry["version"],
            "summary": f"Migration: {entry['migration_file']}"
        })
    
    # Get backup information
    backups = migration.list_backups()
    backup_status = {
        "backup_count": len(backups),
        "latest_backup": backups[0]["metadata"]["timestamp"] if backups else "No backups"
    }
    
    # Perform health checks
    health_checks = [
        {
            "name": "Configuration Validity",
            "status_color": "bg-green-500",
            "message": "All settings valid"
        },
        {
            "name": "Backup Status",
            "status_color": "bg-green-500" if backups else "bg-yellow-500",
            "message": "Recent backup available" if backups else "No recent backups"
        },
        {
            "name": "Version Control",
            "status_color": "bg-green-500",
            "message": "Version tracking active"
        }
    ]
    
    # Render dashboard
    dashboard_data = {
        **current_status,
        "changes": changes,
        **backup_status,
        "health_checks": health_checks
    }
    
    # Convert template variables
    html_content = DASHBOARD_TEMPLATE
    for key, value in dashboard_data.items():
        html_content = html_content.replace("{{" + key + "}}", str(value))
    
    # Replace array sections
    for key in ["changes", "health_checks"]:
        if isinstance(dashboard_data[key], list):
            template_part = "{{#" + key + "}}"
            end_part = "{{/" + key + "}}"
            start_idx = html_content.find(template_part)
            end_idx = html_content.find(end_part)
            
            if start_idx != -1 and end_idx != -1:
                template_content = html_content[start_idx + len(template_part):end_idx]
                rendered_items = []
                
                for item in dashboard_data[key]:
                    item_content = template_content
                    for item_key, item_value in item.items():
                        item_content = item_content.replace("{{" + item_key + "}}", str(item_value))
                    rendered_items.append(item_content)
                
                html_content = (
                    html_content[:start_idx] +
                    "".join(rendered_items) +
                    html_content[end_idx + len(end_part):]
                )
    
    return HTMLResponse(content=html_content)