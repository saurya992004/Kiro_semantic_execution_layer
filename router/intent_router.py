from tools.app_tools import open_app
from tools.web_tools import search_web
from tools.system_tools import (
    shutdown_pc,
    restart_pc,
    sleep_pc,
    lock_pc,
    kill_process,
    clean_temp,
    empty_recycle_bin,
)
from tools.diagnostics_tools import (
    get_cpu_usage,
    get_ram_usage,
    get_disk_usage,
    get_system_health,
    analyze_disk_usage,
    find_large_folders,
    get_disk_alerts,
    check_health_alerts,
    scan_cleanup_files,
    execute_cleanup,
    clean_temp_files,
    clean_old_files,
)
from troubleshooter.screenshot_tool import capture_screen_base64
from troubleshooter.vision_analyzer import VisionAnalyzer
from troubleshooter.solution_parser import parse_solution
from troubleshooter.auto_fix_engine import execute_fixes


def route_intent(command: dict):

    intent = command.get("intent")
    action = command.get("action")
    params = command.get("parameters", {})

    if intent == "open_app":
        open_app(params.get("app_name"))

    elif intent == "web_search":
        search_web(params.get("query"))

    elif intent == "system_control":
        if action == "shutdown":
          shutdown_pc()

        elif action == "restart":
            restart_pc()

        elif action == "sleep":
            sleep_pc()

        elif action == "lock":
            lock_pc()

        elif action == "kill_process":
            kill_process(params.get("process_name"))

        elif action == "clean_temp":
            clean_temp()

        elif action == "empty_recycle_bin":
            empty_recycle_bin()

    elif intent == "diagnostics":
        if action == "check_cpu":
            result = get_cpu_usage()
            if "error" not in result:
                print(f"\n🖥️ CPU Usage: {result['cpu_percent']}%")
                print(f"CPU Cores: {result['cpu_count']}")
            else:
                print(f"Error: {result['error']}")

        elif action == "check_ram":
            result = get_ram_usage()
            if "error" not in result:
                print(f"\n💾 RAM Usage: {result['percent']}%")
                print(f"Used: {result['used_gb']}GB / {result['total_gb']}GB")
                print(f"Available: {result['available_gb']}GB")
            else:
                print(f"Error: {result['error']}")

        elif action == "check_disk":
            drive = params.get("drive", "C:")
            result = get_disk_usage(drive)
            if "error" not in result:
                print(f"\n💿 Disk Usage ({result['drive']}): {result['percent']}%")
                print(f"Used: {result['used_gb']}GB / {result['total_gb']}GB")
                print(f"Free: {result['free_gb']}GB")
            else:
                print(f"Error: {result['error']}")

        elif action == "full_health_check":
            result = get_system_health()
            print(f"\n🏥 System Health Check - {result['timestamp']}")
            print(f"\nCPU: {result['cpu']['cpu_percent']}%")
            print(f"RAM: {result['ram']['percent']}% ({result['ram']['used_gb']}GB / {result['ram']['total_gb']}GB)")
            print(f"Disk: {result['disk']['percent']}% ({result['disk']['used_gb']}GB / {result['disk']['total_gb']}GB)")

    elif intent == "disk_analysis":
        if action == "analyze_usage":
            path = params.get("path", "C:\\")
            result = analyze_disk_usage(path)
            if "error" not in result:
                print(f"\n📊 Disk Analysis: {result['path']}")
                print(f"Total Size: {result['total_size_gb']}GB\n")
                print("Top Folders:")
                for folder in result['folders'][:10]:  # Show top 10
                    print(f"  {folder['name']}: {folder['size_gb']}GB ({folder['percent_of_total']}%)")
            else:
                print(f"Error: {result['error']}")

        elif action == "find_large_folders":
            path = params.get("path", "C:\\")
            threshold = params.get("threshold_gb", 1.0)
            result = find_large_folders(path, threshold)
            print(f"\n📁 Large Folders (>{threshold}GB):")
            for folder in result:
                print(f"  {folder['path']}: {folder['size_gb']}GB")

        elif action == "check_alerts":
            result = get_disk_alerts()
            print(f"\n⚠️ Disk Alerts - Status: {result['status'].upper()}")
            if result['alerts']:
                for alert in result['alerts']:
                    icon = "🔴" if alert['level'] == "critical" else "🟡"
                    print(f"  {icon} {alert['message']}")
            else:
                print("  ✅ All disks are healthy")

    elif intent == "maintenance":
        if action == "scan_temp":
            result = clean_temp_files()
            if "error" not in result:
                print(f"\n🧹 Temp Files Scan: {result['target_folder']}")
                print(f"Files found: {result['file_count']}")
                print(f"Total size: {result['total_size_mb']}MB")
                if result['file_count'] > 0:
                    print("\nFiles to delete:")
                    for file in result['files_to_delete'][:10]:  # Show first 10
                        print(f"  {file['path']} ({file['size_mb']}MB)")
                    print("\n⚠️ Use 'confirm cleanup' to delete these files")
            else:
                print(f"Error: {result['error']}")

        elif action == "scan_old_files":
            folder = params.get("folder", "test_cleanup/old_files")
            days = params.get("days", 30)
            result = clean_old_files(folder, days)
            if "error" not in result:
                print(f"\n🗑️ Old Files Scan: {result['target_folder']}")
                print(f"Files older than {result['days_threshold']} days: {result['file_count']}")
                print(f"Total size: {result['total_size_mb']}MB")
                if result['file_count'] > 0:
                    print("\nFiles to delete:")
                    for file in result['files_to_delete'][:10]:
                        print(f"  {file['path']} ({file['days_old']} days old, {file['size_mb']}MB)")
                    print("\n⚠️ Use 'confirm cleanup' to delete these files")
            else:
                print(f"Error: {result['error']}")

        elif action == "scan_cleanup":
            folder = params.get("folder", "test_cleanup")
            result = scan_cleanup_files(folder)
            if "error" not in result:
                print(f"\n🔍 Cleanup Scan: {result['target_folder']}")
                print(f"Files found: {result['file_count']}")
                print(f"Total size: {result['total_size_mb']}MB")
            else:
                print(f"Error: {result['error']}")

    elif intent == "health_check":
        result = check_health_alerts()
        print(f"\n🏥 Health Alerts - Overall Status: {result['overall_status'].upper()}")
        if result['alerts']:
            for alert in result['alerts']:
                icon = "🔴" if alert['severity'] == "critical" else "🟡" if alert['severity'] == "warning" else "ℹ️"
                print(f"  {icon} [{alert['type'].upper()}] {alert['message']}")
        else:
            print("  ✅ System is healthy")

    elif intent == "troubleshoot_screen":
        print("\n📸 Capturing screenshot...")
        base64_image = capture_screen_base64()
        if not base64_image:
            print("❌ Failed to capture screen.")
            return

        print("🧠 Analyzing error with Groq Vision (this may take a few seconds)...")
        analyzer = VisionAnalyzer()
        raw_response = analyzer.analyze_error(base64_image)
        
        if not raw_response:
             print("❌ Failed to get response from Groq API.")
             return
             
        solution = parse_solution(raw_response)
        if not solution:
             print("❌ Failed to parse solution.")
             return
             
        print("\n💡 Explanation:")
        print(solution.get("explanation", "No explanation provided."))
        
        commands = solution.get("commands", [])
        if commands:
             execute_fixes(commands)
        else:
             print("\n✅ No automated commands needed to fix this issue.")

    else:
        print("Intent not recognized.")

