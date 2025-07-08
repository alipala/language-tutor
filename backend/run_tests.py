#!/usr/bin/env python3
"""
Language Tutor API Test Runner

This script provides a convenient way to run the comprehensive API integration tests
with various options and configurations.

Usage:
    python run_tests.py [options]

Examples:
    python run_tests.py                          # Run all tests
    python run_tests.py --auth                   # Run only authentication tests
    python run_tests.py --coverage               # Run with coverage report
    python run_tests.py --verbose --parallel     # Verbose output with parallel execution
    python run_tests.py --quick                  # Run quick smoke tests only
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, cwd=None, env=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-asyncio',
        'httpx',
        'motor',
        'fastapi'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r tests/requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_mongodb():
    """Check if MongoDB is running and accessible."""
    print("🔍 Checking MongoDB connection...")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_connection():
            client = AsyncIOMotorClient("mongodb://localhost:27017")
            try:
                await client.admin.command('ping')
                return True
            except Exception:
                return False
            finally:
                client.close()
        
        is_connected = asyncio.run(test_connection())
        
        if is_connected:
            print("✅ MongoDB is running and accessible")
            return True
        else:
            print("❌ MongoDB is not accessible")
            return False
            
    except ImportError:
        print("❌ Motor (MongoDB driver) is not installed")
        return False
    except Exception as e:
        print(f"❌ Error checking MongoDB: {e}")
        return False

def setup_test_environment():
    """Set up test environment variables."""
    print("🔧 Setting up test environment...")
    
    test_env = {
        'ENVIRONMENT': 'test',
        'DATABASE_NAME': 'language_tutor_test',
        'TEST_MONGODB_URL': 'mongodb://localhost:27017',
        'OPENAI_API_KEY': 'test_openai_key',
        'STRIPE_SECRET_KEY': 'sk_test_123',
        'STRIPE_WEBHOOK_SECRET': 'whsec_test_123',
        'JWT_SECRET_KEY': 'test_jwt_secret_key_for_testing_only',
        'EMAIL_HOST': 'localhost',
        'EMAIL_PORT': '587',
        'EMAIL_USERNAME': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password'
    }
    
    # Update environment
    os.environ.update(test_env)
    
    print("✅ Test environment configured")
    return test_env

def run_tests(args):
    """Run the tests based on provided arguments."""
    print("🧪 Starting API Integration Tests...")
    
    # Base pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Determine test path
    if args.auth:
        test_path = 'tests/integration/test_auth_routes.py'
    elif args.learning:
        test_path = 'tests/integration/test_learning_routes.py'
    elif args.stripe:
        test_path = 'tests/integration/test_stripe_routes.py'
    elif args.progress:
        test_path = 'tests/integration/test_progress_routes.py'
    elif args.quick:
        # Run a subset of quick tests
        test_path = 'tests/integration/'
        cmd.extend(['-k', 'test_get_learning_goals or test_register_new_user_success or test_get_subscription_plans'])
    else:
        test_path = 'tests/integration/'
    
    cmd.append(test_path)
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            '--cov=.',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--cov-report=xml'
        ])
        if args.coverage_fail:
            cmd.append(f'--cov-fail-under={args.coverage_fail}')
    
    # Add verbosity
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', str(args.parallel)])
    
    # Add other options
    if args.maxfail:
        cmd.extend(['--maxfail', str(args.maxfail)])
    
    if args.tb:
        cmd.extend(['--tb', args.tb])
    
    # Add output options
    if args.html_report:
        cmd.extend(['--html', 'test-report.html', '--self-contained-html'])
    
    if args.junit_xml:
        cmd.extend(['--junitxml', 'test-results.xml'])
    
    # Add benchmark options
    if args.benchmark:
        cmd.extend(['--benchmark-only', '--benchmark-json=benchmark-results.json'])
    
    # Run the tests
    start_time = time.time()
    success, stdout, stderr = run_command(cmd, cwd=Path(__file__).parent)
    end_time = time.time()
    
    # Print results
    print(f"\n{'='*60}")
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print(f"⏱️  Test execution time: {end_time - start_time:.2f} seconds")
    
    if stdout:
        print("\nSTDOUT:")
        print(stdout)
    
    if stderr:
        print("\nSTDERR:")
        print(stderr)
    
    return success

def run_linting():
    """Run code linting checks."""
    print("🔍 Running linting checks...")
    
    # Run flake8
    print("\n📝 Running flake8...")
    success, stdout, stderr = run_command([
        'flake8', '.', '--count', '--select=E9,F63,F7,F82', '--show-source', '--statistics'
    ])
    
    if not success:
        print("❌ Flake8 found critical issues:")
        print(stderr)
        return False
    
    # Run flake8 with warnings
    print("\n📝 Running flake8 (warnings)...")
    run_command([
        'flake8', '.', '--count', '--exit-zero', '--max-complexity=10', 
        '--max-line-length=127', '--statistics'
    ])
    
    print("✅ Linting checks completed")
    return True

def run_security_scan():
    """Run security scans."""
    print("🔒 Running security scans...")
    
    # Run bandit
    print("\n🛡️  Running bandit security scan...")
    success, stdout, stderr = run_command([
        'bandit', '-r', '.', '-ll'
    ])
    
    if not success:
        print("⚠️  Bandit found security issues:")
        print(stdout)
        print(stderr)
    else:
        print("✅ No critical security issues found")
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Language Tutor API Integration Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Test selection
    test_group = parser.add_argument_group('Test Selection')
    test_group.add_argument('--auth', action='store_true', help='Run authentication tests only')
    test_group.add_argument('--learning', action='store_true', help='Run learning routes tests only')
    test_group.add_argument('--stripe', action='store_true', help='Run Stripe/subscription tests only')
    test_group.add_argument('--progress', action='store_true', help='Run progress tracking tests only')
    test_group.add_argument('--quick', action='store_true', help='Run quick smoke tests only')
    
    # Coverage options
    coverage_group = parser.add_argument_group('Coverage Options')
    coverage_group.add_argument('--coverage', action='store_true', help='Generate coverage report')
    coverage_group.add_argument('--coverage-fail', type=int, metavar='N', help='Fail if coverage below N%%')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    output_group.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    output_group.add_argument('--html-report', action='store_true', help='Generate HTML test report')
    output_group.add_argument('--junit-xml', action='store_true', help='Generate JUnit XML report')
    
    # Execution options
    exec_group = parser.add_argument_group('Execution Options')
    exec_group.add_argument('--parallel', '-n', type=int, metavar='N', help='Run tests in N parallel processes')
    exec_group.add_argument('--maxfail', type=int, metavar='N', help='Stop after N failures')
    exec_group.add_argument('--tb', choices=['short', 'long', 'line', 'no'], default='short', help='Traceback style')
    
    # Additional options
    additional_group = parser.add_argument_group('Additional Options')
    additional_group.add_argument('--benchmark', action='store_true', help='Run performance benchmarks only')
    additional_group.add_argument('--lint', action='store_true', help='Run linting checks')
    additional_group.add_argument('--security', action='store_true', help='Run security scans')
    additional_group.add_argument('--skip-deps', action='store_true', help='Skip dependency checks')
    additional_group.add_argument('--skip-mongo', action='store_true', help='Skip MongoDB connection check')
    
    args = parser.parse_args()
    
    print("🚀 Language Tutor API Test Runner")
    print("=" * 50)
    
    # Check dependencies
    if not args.skip_deps and not check_dependencies():
        sys.exit(1)
    
    # Check MongoDB
    if not args.skip_mongo and not check_mongodb():
        print("💡 Tip: Start MongoDB with: mongod --dbpath /path/to/data")
        sys.exit(1)
    
    # Setup test environment
    setup_test_environment()
    
    success = True
    
    # Run linting if requested
    if args.lint:
        if not run_linting():
            success = False
    
    # Run security scans if requested
    if args.security:
        if not run_security_scan():
            success = False
    
    # Run tests (unless only linting/security was requested)
    if not (args.lint and args.security and not any([
        args.auth, args.learning, args.stripe, args.progress, args.quick, args.benchmark
    ])):
        if not run_tests(args):
            success = False
    
    # Final summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All checks passed successfully!")
        sys.exit(0)
    else:
        print("💥 Some checks failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
