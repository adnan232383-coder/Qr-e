import requests
import sys
import json
from datetime import datetime

class UGUniversityAPITester:
    def __init__(self, base_url="https://question-bank-import-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if self.session_token:
            test_headers['Authorization'] = f'Bearer {self.session_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })

            return success, response.json() if success and response.text else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n=== TESTING HEALTH ENDPOINTS ===")
        
        # Test root endpoint
        self.run_test("API Root", "GET", "", 200)
        
        # Test health endpoint
        self.run_test("Health Check", "GET", "health", 200)

    def test_seed_database(self):
        """Test database seeding"""
        print("\n=== TESTING DATABASE SEEDING ===")
        
        success, response = self.run_test("Seed Database", "POST", "seed", 200)
        if success and "courses_count" in response:
            print(f"   Seeded {response['courses_count']} courses")
        return success

    def test_catalog_endpoints(self):
        """Test catalog-related endpoints"""
        print("\n=== TESTING CATALOG ENDPOINTS ===")
        
        # Test universities
        success, universities = self.run_test("Get Universities", "GET", "universities", 200)
        university_id = None
        if success and universities:
            university_id = universities[0].get("external_id")
            print(f"   Found university: {universities[0].get('name')}")

        # Test majors
        success, majors = self.run_test("Get Majors", "GET", "majors", 200)
        major_id = None
        if success and majors:
            major_id = majors[0].get("external_id")
            print(f"   Found {len(majors)} majors")
            for major in majors:
                print(f"     - {major.get('name')} ({major.get('degree')}, {major.get('years')} years)")

        # Test specific major
        if major_id:
            self.run_test("Get Specific Major", "GET", f"majors/{major_id}", 200)

        # Test years for major
        year_id = None
        if major_id:
            success, years = self.run_test("Get Years for Major", "GET", f"years?major_id={major_id}", 200)
            if success and years:
                year_id = years[0].get("external_id")
                print(f"   Found {len(years)} years for major")

        # Test courses for year
        course_id = None
        if year_id:
            success, courses = self.run_test("Get Courses for Year", "GET", f"courses?year_id={year_id}", 200)
            if success and courses:
                course_id = courses[0].get("external_id")
                print(f"   Found {len(courses)} courses for year")

        # Test courses filtered by semester
        if year_id:
            success, semester_courses = self.run_test("Get Semester 1 Courses", "GET", f"courses?year_id={year_id}&semester=1", 200)
            if success:
                print(f"   Found {len(semester_courses)} courses in semester 1")

        # Test specific course
        if course_id:
            self.run_test("Get Specific Course", "GET", f"courses/{course_id}", 200)

        # Test course content
        if course_id:
            self.run_test("Get Course Content", "GET", f"courses/{course_id}/content", 200)

        return major_id, year_id, course_id

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== TESTING AUTH ENDPOINTS ===")
        
        # Test /auth/me without authentication (should fail)
        self.run_test("Get Me (Unauthenticated)", "GET", "auth/me", 401)
        
        # Test logout without session
        self.run_test("Logout (No Session)", "POST", "auth/logout", 200)

    def test_content_generation_endpoints(self, course_id):
        """Test content generation system endpoints"""
        print("\n=== TESTING CONTENT GENERATION ENDPOINTS ===")
        
        if not course_id:
            print("⚠️  No course ID available, skipping content generation tests")
            return
        
        # Test course status endpoint
        success, status = self.run_test("Get Course Status", "GET", f"courses/{course_id}/status", 200)
        if success:
            print(f"   Course status: {status.get('status', 'unknown')}")
            print(f"   Has summary: {status.get('has_summary', False)}")
            print(f"   Questions count: {status.get('questions_count', 0)}")
            print(f"   Scripts count: {status.get('scripts_count', 0)}")
        
        # Test course questions endpoint
        success, questions_data = self.run_test("Get Course Questions", "GET", f"courses/{course_id}/questions?limit=50", 200)
        if success:
            questions = questions_data.get('questions', [])
            print(f"   Found {len(questions)} questions")
            if questions:
                # Test difficulty breakdown
                difficulties = {}
                for q in questions:
                    diff = q.get('difficulty', 'unknown')
                    difficulties[diff] = difficulties.get(diff, 0) + 1
                print(f"   Difficulty breakdown: {difficulties}")
                
                # Test first question structure
                first_q = questions[0]
                required_fields = ['question_id', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation']
                missing_fields = [field for field in required_fields if field not in first_q]
                if missing_fields:
                    print(f"   ⚠️  Missing question fields: {missing_fields}")
                else:
                    print(f"   ✅ Question structure complete")
        
        # Test course scripts endpoint
        success, scripts = self.run_test("Get Course Scripts", "GET", f"courses/{course_id}/scripts", 200)
        if success and scripts:
            print(f"   Found {len(scripts)} module scripts")
            for script in scripts[:3]:  # Show first 3
                duration = script.get('estimated_duration_minutes', 0)
                word_count = script.get('word_count', 0)
                print(f"     - Module {script.get('module_id', 'unknown')}: {duration}min, {word_count} words")
        
        # Test course modules endpoint
        success, modules = self.run_test("Get Course Modules", "GET", f"courses/{course_id}/modules", 200)
        if success and modules:
            print(f"   Found {len(modules)} modules")
            for module in modules[:3]:  # Show first 3
                print(f"     - {module.get('title', 'Untitled')}: {module.get('duration_hours', 0)}h")
        
        # Test content generation queue status
        success, queue_status = self.run_test("Get Queue Status", "GET", "content/queue-status", 200)
        if success:
            print(f"   Queue status: {queue_status}")
        
        # Test content generation logs
        success, logs = self.run_test("Get Generation Logs", "GET", f"courses/{course_id}/logs", 200)
        if success:
            logs_data = logs.get('logs', [])
            print(f"   Found {len(logs_data)} generation log entries")
        
        return course_id

    def test_ai_chat_endpoint(self):
        """Test AI chat endpoint"""
        print("\n=== TESTING AI CHAT ENDPOINT ===")
        
        chat_data = {
            "message": "What is dentistry?",
            "course_id": None,
            "history": []
        }
        
        success, response = self.run_test("AI Chat", "POST", "chat", 200, data=chat_data)
        if success and "response" in response:
            print(f"   AI Response: {response['response'][:100]}...")

    def test_error_cases(self):
        """Test error handling"""
        print("\n=== TESTING ERROR CASES ===")
        
        # Test non-existent major
        self.run_test("Get Non-existent Major", "GET", "majors/INVALID_ID", 404)
        
        # Test non-existent course
        self.run_test("Get Non-existent Course", "GET", "courses/INVALID_ID", 404)
        
        # Test invalid year query
        self.run_test("Get Years (Invalid Major)", "GET", "years?major_id=INVALID", 200)

def main():
    print("🎓 UG University Assistant API Testing")
    print("=" * 50)
    
    tester = UGUniversityAPITester()
    
    # Run all tests
    tester.test_health_endpoints()
    
    # Seed database first
    seed_success = tester.test_seed_database()
    if not seed_success:
        print("⚠️  Database seeding failed, continuing with existing data...")
    
    # Test main functionality
    major_id, year_id, course_id = tester.test_catalog_endpoints()
    tester.test_auth_endpoints()
    tester.test_ai_chat_endpoint()
    tester.test_content_generation_endpoints(course_id)
    tester.test_error_cases()
    
    # Print summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS:")
        for failure in tester.failed_tests:
            print(f"  - {failure.get('test', 'Unknown')}: {failure}")
    
    # Return appropriate exit code
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())