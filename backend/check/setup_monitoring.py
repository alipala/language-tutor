#!/usr/bin/env python3
"""
Setup script for automated webhook monitoring
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_cron_job():
    """Setup daily cron job for webhook monitoring"""
    
    # Get the absolute path to the monitoring script
    script_dir = Path(__file__).parent.absolute()
    monitor_script = script_dir / "monitor_slack_webhook.py"
    
    # Create cron job command
    # Run daily at 9 AM
    cron_command = f"0 9 * * * cd {script_dir} && /usr/bin/python3 {monitor_script} >> webhook_monitor.log 2>&1"
    
    print("🔧 SETTING UP AUTOMATED WEBHOOK MONITORING")
    print("=" * 50)
    print(f"Script location: {monitor_script}")
    print(f"Cron command: {cron_command}")
    print()
    
    # Check if running on macOS/Linux
    if os.name != 'posix':
        print("❌ This setup script is for macOS/Linux only")
        print("For Windows, use Task Scheduler to run the monitoring script daily")
        return False
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        # Check if our job already exists
        if "monitor_slack_webhook.py" in current_crontab:
            print("✅ Webhook monitoring cron job already exists")
            print("Current crontab entries:")
            print(current_crontab)
            return True
        
        # Add our cron job
        new_crontab = current_crontab + cron_command + "\n"
        
        # Write new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Cron job added successfully!")
            print("The webhook monitor will run daily at 9:00 AM")
            return True
        else:
            print("❌ Failed to add cron job")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up cron job: {str(e)}")
        return False

def create_systemd_service():
    """Create systemd service for continuous monitoring (Linux only)"""
    
    script_dir = Path(__file__).parent.absolute()
    monitor_script = script_dir / "monitor_slack_webhook.py"
    
    service_content = f"""[Unit]
Description=Slack Webhook Monitor
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={script_dir}
ExecStart=/usr/bin/python3 {monitor_script} --continuous
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
"""
    
    service_file = "/etc/systemd/system/webhook-monitor.service"
    
    print("\n🔧 CREATING SYSTEMD SERVICE (Optional)")
    print("=" * 50)
    print("This will create a service that runs continuous monitoring")
    print(f"Service file: {service_file}")
    print()
    
    try:
        # Write service file (requires sudo)
        print("Writing systemd service file...")
        print("You may be prompted for sudo password:")
        
        process = subprocess.run([
            'sudo', 'tee', service_file
        ], input=service_content, text=True, capture_output=True)
        
        if process.returncode == 0:
            print("✅ Service file created")
            
            # Reload systemd and enable service
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
            subprocess.run(['sudo', 'systemctl', 'enable', 'webhook-monitor'])
            
            print("✅ Service enabled")
            print("To start the service: sudo systemctl start webhook-monitor")
            print("To check status: sudo systemctl status webhook-monitor")
            return True
        else:
            print("❌ Failed to create service file")
            return False
            
    except Exception as e:
        print(f"❌ Error creating systemd service: {str(e)}")
        return False

def show_manual_setup():
    """Show manual setup instructions"""
    
    script_dir = Path(__file__).parent.absolute()
    monitor_script = script_dir / "monitor_slack_webhook.py"
    
    print("\n📋 MANUAL SETUP INSTRUCTIONS")
    print("=" * 50)
    print()
    print("1. **Daily Monitoring (Recommended)**:")
    print(f"   Add this to your crontab (run 'crontab -e'):")
    print(f"   0 9 * * * cd {script_dir} && python3 {monitor_script}")
    print()
    print("2. **Test the Monitor**:")
    print(f"   python3 {monitor_script}")
    print()
    print("3. **Continuous Monitoring**:")
    print(f"   python3 {monitor_script} --continuous")
    print()
    print("4. **Check Logs**:")
    print(f"   tail -f {script_dir}/webhook_monitor.log")
    print()
    print("5. **Update Webhook URL** (when needed):")
    print(f"   Edit WEBHOOK_URL in {monitor_script}")

def main():
    """Main setup function"""
    
    print("🚀 WEBHOOK MONITORING SETUP")
    print("=" * 50)
    
    # Test the monitoring script first
    script_dir = Path(__file__).parent.absolute()
    monitor_script = script_dir / "monitor_slack_webhook.py"
    
    if not monitor_script.exists():
        print(f"❌ Monitor script not found: {monitor_script}")
        return
    
    print("Testing monitoring script...")
    result = subprocess.run([sys.executable, str(monitor_script)], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Monitoring script test successful")
    else:
        print("❌ Monitoring script test failed:")
        print(result.stderr)
        return
    
    # Setup options
    print("\nSetup options:")
    print("1. Daily cron job (recommended)")
    print("2. Systemd service (continuous monitoring)")
    print("3. Show manual setup instructions")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            setup_cron_job()
        elif choice == "2":
            create_systemd_service()
        elif choice == "3":
            show_manual_setup()
        elif choice == "4":
            print("Setup cancelled")
        else:
            print("Invalid choice")
            show_manual_setup()
            
    except KeyboardInterrupt:
        print("\nSetup cancelled")
    except Exception as e:
        print(f"Error: {str(e)}")
        show_manual_setup()

if __name__ == "__main__":
    main()
