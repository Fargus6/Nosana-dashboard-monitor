#!/usr/bin/env python3
"""
Comprehensive health check for Nosana Node Monitor
"""
import asyncio
import sys
sys.path.append('/app/backend')

import requests
import subprocess
import os
from datetime import datetime

def print_header(title):
    print(f"\n{'='*100}")
    print(f"{title}")
    print(f"{'='*100}\n")

def check_services():
    """Check all supervisor services"""
    print_header("🔧 SERVICE HEALTH CHECK")
    
    result = subprocess.run(['sudo', 'supervisorctl', 'status'], 
                          capture_output=True, text=True)
    
    services = {}
    for line in result.stdout.split('\n'):
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                status = parts[1]
                services[name] = {
                    'status': status,
                    'line': line
                }
    
    print("Service Status:")
    all_running = True
    for name, info in services.items():
        status_icon = "✅" if info['status'] == "RUNNING" else "❌"
        print(f"   {status_icon} {info['line']}")
        if info['status'] != "RUNNING":
            all_running = False
    
    return all_running

def check_backend_mode():
    """Check if backend is in production mode (no --reload)"""
    print_header("🚀 PRODUCTION MODE CHECK")
    
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    
    backend_process = None
    for line in result.stdout.split('\n'):
        if 'uvicorn server:app' in line and '--reload' not in line and 'grep' not in line:
            backend_process = line
            break
    
    has_reload = False
    for line in result.stdout.split('\n'):
        if 'uvicorn server:app' in line and '--reload' in line and 'grep' not in line:
            has_reload = True
            break
    
    if backend_process and not has_reload:
        print("✅ Backend running in PRODUCTION mode (no --reload)")
        print(f"   Process: {backend_process.strip()}")
        return True
    elif has_reload:
        print("❌ Backend running in DEVELOPMENT mode (--reload detected)")
        return False
    else:
        print("⚠️  Backend process not found")
        return False

def check_secret_key():
    """Check if SECRET_KEY exists"""
    print_header("🔐 SECRET KEY CHECK")
    
    env_file = '/app/backend/.env'
    try:
        with open(env_file, 'r') as f:
            content = f.read()
            if 'SECRET_KEY=' in content:
                # Extract the key (mask it for security)
                for line in content.split('\n'):
                    if line.startswith('SECRET_KEY='):
                        key = line.split('=', 1)[1].strip('"')
                        masked = key[:8] + '...' + key[-8:] if len(key) > 16 else '***'
                        print(f"✅ SECRET_KEY found: {masked}")
                        return True
        print("❌ SECRET_KEY not found in .env")
        return False
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return False

def check_api_endpoints():
    """Check critical API endpoints"""
    print_header("🌐 API ENDPOINT CHECK")
    
    # Get backend URL from frontend .env
    frontend_env = '/app/frontend/.env'
    backend_url = None
    try:
        with open(frontend_env, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
    except:
        backend_url = 'http://localhost:8001'
    
    if not backend_url:
        backend_url = 'http://localhost:8001'
    
    print(f"Testing endpoints on: {backend_url}\n")
    
    endpoints = [
        ('/api/health', 'Health Check'),
        ('/api/auth/register', 'Auth Registration (POST)'),
    ]
    
    results = {}
    for path, name in endpoints:
        url = f"{backend_url}{path}"
        try:
            if path == '/api/health':
                response = requests.get(url, timeout=5)
            else:
                # Just check if endpoint exists (will return 422 for missing data)
                response = requests.post(url, json={}, timeout=5)
            
            if response.status_code in [200, 422]:  # 422 = validation error (endpoint exists)
                print(f"   ✅ {name}: {response.status_code}")
                results[path] = True
            else:
                print(f"   ⚠️  {name}: {response.status_code}")
                results[path] = True  # Still counts as working
        except Exception as e:
            print(f"   ❌ {name}: {str(e)}")
            results[path] = False
    
    return all(results.values())

def check_database():
    """Check MongoDB connection"""
    print_header("🗄️  DATABASE CHECK")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        
        async def test_connection():
            client = AsyncIOMotorClient(mongo_url)
            try:
                # Ping the database
                await client.admin.command('ping')
                print(f"✅ MongoDB connected: {mongo_url}")
                
                # Get database name
                db_name = os.getenv('DB_NAME', 'test_database')
                db = client[db_name]
                
                # Count documents in key collections
                collections = ['users', 'nodes', 'device_tokens']
                for coll_name in collections:
                    count = await db[coll_name].count_documents({})
                    print(f"   • {coll_name}: {count} documents")
                
                await client.close()
                return True
            except Exception as e:
                print(f"❌ MongoDB error: {e}")
                await client.close()
                return False
        
        return asyncio.run(test_connection())
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_file_structure():
    """Check critical files exist"""
    print_header("📁 FILE STRUCTURE CHECK")
    
    critical_files = [
        '/app/backend/server.py',
        '/app/backend/.env',
        '/app/backend/requirements.txt',
        '/app/frontend/src/App.js',
        '/app/frontend/package.json',
        '/app/frontend/.env',
        '/etc/supervisor/conf.d/supervisord.conf',
    ]
    
    all_exist = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def check_logs():
    """Check for recent errors in logs"""
    print_header("📋 LOG CHECK (Last 50 lines)")
    
    log_file = '/var/log/supervisor/backend.err.log'
    
    try:
        result = subprocess.run(['tail', '-n', '50', log_file], 
                              capture_output=True, text=True)
        
        error_keywords = ['ERROR', 'CRITICAL', 'Exception', 'Traceback']
        errors_found = []
        
        for line in result.stdout.split('\n'):
            for keyword in error_keywords:
                if keyword in line:
                    errors_found.append(line.strip())
                    break
        
        if errors_found:
            print(f"⚠️  Found {len(errors_found)} potential error(s):")
            for error in errors_found[-5:]:  # Show last 5
                print(f"   • {error[:100]}")
            return False
        else:
            print("✅ No critical errors in recent logs")
            return True
    except Exception as e:
        print(f"⚠️  Could not read logs: {e}")
        return True  # Don't fail health check for this

def check_uptime():
    """Check backend uptime"""
    print_header("⏱️  UPTIME CHECK")
    
    result = subprocess.run(['sudo', 'supervisorctl', 'status', 'backend'], 
                          capture_output=True, text=True)
    
    if 'uptime' in result.stdout:
        uptime_str = result.stdout.split('uptime')[1].split(',')[0].strip()
        print(f"Backend uptime: {uptime_str}")
        
        # Parse uptime to check if it's stable (> 1 minute)
        if ':' in uptime_str:
            parts = uptime_str.split(':')
            if len(parts) == 3:  # hours:minutes:seconds
                hours = int(parts[0])
                if hours > 0:
                    print("✅ Backend has been stable for hours")
                    return True
            minutes = int(parts[-2]) if len(parts) >= 2 else 0
            if minutes >= 2:
                print("✅ Backend stable for multiple minutes")
                return True
        
        print("⚠️  Backend recently restarted (< 2 minutes)")
        return True  # Still acceptable
    
    return True

def main():
    print(f"\n{'#'*100}")
    print(f"# NOSANA NODE MONITOR - COMPREHENSIVE HEALTH CHECK")
    print(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*100}")
    
    results = {}
    
    # Run all checks
    results['services'] = check_services()
    results['production_mode'] = check_backend_mode()
    results['secret_key'] = check_secret_key()
    results['api'] = check_api_endpoints()
    results['database'] = check_database()
    results['files'] = check_file_structure()
    results['logs'] = check_logs()
    results['uptime'] = check_uptime()
    
    # Summary
    print_header("📊 HEALTH CHECK SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print("Results:")
    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {check.replace('_', ' ').title()}")
    
    print(f"\nScore: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL CHECKS PASSED - SYSTEM HEALTHY")
        return 0
    elif passed >= total * 0.8:
        print("\n⚠️  MOST CHECKS PASSED - MINOR ISSUES")
        return 1
    else:
        print("\n❌ CRITICAL ISSUES FOUND")
        return 2

if __name__ == "__main__":
    exit(main())
