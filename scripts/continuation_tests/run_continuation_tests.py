#!/usr/bin/env python3
"""
Continuation Test Runner for Debbie

This script runs continuation tests using Debbie to validate conversation
and continuation behavior across different scenarios.
"""

import json
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ContinuationTestRunner:
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.results = []
        self.config_path = project_root / "config" / "main.yaml"
        
    def load_test(self, test_file: Path) -> Dict[str, Any]:
        """Load a test configuration from JSON file"""
        with open(test_file, 'r') as f:
            return json.load(f)
    
    def run_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test using Debbie"""
        test_name = test_config['name']
        print(f"\n🧪 Running test: {test_name}")
        print(f"   Description: {test_config['description']}")
        
        result = {
            'name': test_name,
            'start_time': datetime.now().isoformat(),
            'steps': []
        }
        
        # Create a temporary script for Debbie
        script_path = self.test_dir / f"_temp_{test_name}.json"
        
        try:
            # For each step in the test
            for step in test_config['steps']:
                step_result = self.run_test_step(test_config, step, script_path)
                result['steps'].append(step_result)
                
                # Check if step failed
                if not step_result['success']:
                    result['success'] = False
                    result['error'] = f"Step '{step['name']}' failed"
                    break
            else:
                result['success'] = True
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
        finally:
            # Clean up temp file
            if script_path.exists():
                script_path.unlink()
        
        result['end_time'] = datetime.now().isoformat()
        return result
    
    def run_test_step(self, test_config: Dict[str, Any], step: Dict[str, Any], script_path: Path) -> Dict[str, Any]:
        """Run a single test step"""
        # Prepare Debbie script
        debbie_script = {
            'name': step['name'],
            'config': test_config.get('config', {}),
            'steps': [{
                'user_message': step['user_message'],
                'expected_behavior': step.get('expected_behavior', {})
            }]
        }
        
        # Override agent if specified in step
        if 'agent' in step:
            debbie_script['config']['agent'] = step['agent']
        
        # Write script
        with open(script_path, 'w') as f:
            json.dump(debbie_script, f, indent=2)
        
        # Run with Debbie
        cmd = [
            sys.executable, '-m', 'ai_whisperer.interfaces.cli.main',
            '--config', str(self.config_path),
            'batch', str(script_path)
        ]
        
        print(f"\n   📍 Step: {step['name']}")
        print(f"   🗣️  User: {step['user_message'][:80]}...")
        
        try:
            # Run the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=test_config.get('config', {}).get('timeout', 300))
            
            # Analyze results
            step_result = {
                'name': step['name'],
                'success': process.returncode == 0,
                'stdout': stdout,
                'stderr': stderr,
                'validations': {}
            }
            
            # Perform validations
            expected = step.get('expected_behavior', {})
            if expected:
                step_result['validations'] = self.validate_behavior(stdout, expected)
                
                # Check if all validations passed
                all_passed = all(v['passed'] for v in step_result['validations'].values())
                step_result['success'] = step_result['success'] and all_passed
            
            # Print summary
            if step_result['success']:
                print(f"   ✅ Step passed")
            else:
                print(f"   ❌ Step failed")
                for val_name, val_result in step_result['validations'].items():
                    if not val_result['passed']:
                        print(f"      - {val_name}: {val_result.get('reason', 'Failed')}")
            
            return step_result
            
        except subprocess.TimeoutExpired:
            return {
                'name': step['name'],
                'success': False,
                'error': 'Timeout expired',
                'validations': {}
            }
        except Exception as e:
            return {
                'name': step['name'],
                'success': False,
                'error': str(e),
                'validations': {}
            }
    
    def validate_behavior(self, output: str, expected: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the behavior against expectations"""
        validations = {}
        
        # Check continuation behavior
        if 'should_continue' in expected:
            # Look for continuation signals in output
            continuation_found = any(phrase in output for phrase in [
                '"status": "CONTINUE"',
                '"continuation": true',
                'Continuing with',
                'iteration 2',
                'Please continue'
            ])
            
            validations['continuation'] = {
                'passed': continuation_found == expected['should_continue'],
                'expected': expected['should_continue'],
                'actual': continuation_found,
                'reason': f"Expected continuation={expected['should_continue']}, found={continuation_found}"
            }
        
        # Check tools used
        if 'tools_used' in expected:
            tools_found = []
            for tool in expected['tools_used']:
                if f'"{tool}"' in output or f"'{tool}'" in output or f"Tool: {tool}" in output:
                    tools_found.append(tool)
            
            validations['tools_used'] = {
                'passed': set(tools_found) == set(expected['tools_used']),
                'expected': expected['tools_used'],
                'actual': tools_found,
                'reason': f"Expected tools {expected['tools_used']}, found {tools_found}"
            }
        
        # Check response pattern
        if 'response_pattern' in expected:
            import re
            pattern_found = bool(re.search(expected['response_pattern'], output, re.IGNORECASE))
            validations['response_pattern'] = {
                'passed': pattern_found,
                'expected': expected['response_pattern'],
                'actual': pattern_found,
                'reason': f"Pattern '{expected['response_pattern']}' {'found' if pattern_found else 'not found'}"
            }
        
        return validations
    
    def run_all_tests(self, test_filter: str = None) -> None:
        """Run all tests in the test directory"""
        test_files = sorted(self.test_dir.glob("test_*.json"))
        
        if test_filter:
            test_files = [f for f in test_files if test_filter in f.name]
        
        print(f"\n🚀 Running {len(test_files)} continuation tests...")
        print(f"   Config: {self.config_path}")
        print(f"   Test directory: {self.test_dir}")
        
        for test_file in test_files:
            # Skip temp files
            if test_file.name.startswith("_temp_"):
                continue
                
            test_config = self.load_test(test_file)
            result = self.run_test(test_config)
            self.results.append(result)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 CONTINUATION TEST RESULTS SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - passed
        
        print(f"\n✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📝 Total: {len(self.results)}")
        
        if failed > 0:
            print("\n❌ Failed tests:")
            for result in self.results:
                if not result['success']:
                    print(f"   - {result['name']}: {result.get('error', 'Unknown error')}")
        
        # Save detailed results
        results_file = self.test_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {results_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run continuation tests with Debbie')
    parser.add_argument('--filter', help='Filter tests by name')
    parser.add_argument('--test', help='Run a specific test file')
    
    args = parser.parse_args()
    
    test_dir = Path(__file__).parent
    runner = ContinuationTestRunner(test_dir)
    
    if args.test:
        # Run specific test
        test_file = test_dir / args.test
        if test_file.exists():
            test_config = runner.load_test(test_file)
            result = runner.run_test(test_config)
            runner.results = [result]
            runner.print_summary()
        else:
            print(f"❌ Test file not found: {test_file}")
    else:
        # Run all tests
        runner.run_all_tests(args.filter)


if __name__ == "__main__":
    main()