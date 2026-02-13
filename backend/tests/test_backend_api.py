"""
Backend API Tests for Multi-University E-Learning Platform
Tests 5 universities, 486+ courses, MCQ functionality, and video generation endpoints
"""
import pytest
import requests
import os

# Use the public URL for testing
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://virtual-prof-2.preview.emergentagent.com').rstrip('/')


class TestUniversities:
    """Test university endpoints - should have 5 universities"""
    
    def test_get_all_universities(self):
        """Test GET /api/universities returns all 5 universities"""
        response = requests.get(f"{BASE_URL}/api/universities")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of universities"
        assert len(data) == 5, f"Expected 5 universities, got {len(data)}"
        
        # Verify expected universities are present
        expected_ids = ["UG_TBILISI", "NVU", "IASI_ROMANIA", "AAU_AMMAN", "NAJAH"]
        actual_ids = [u["external_id"] for u in data]
        for expected_id in expected_ids:
            assert expected_id in actual_ids, f"Missing university: {expected_id}"
        
        print(f"✓ Found all 5 universities: {actual_ids}")
    
    def test_get_single_university_ug(self):
        """Test GET /api/universities/UG_TBILISI"""
        response = requests.get(f"{BASE_URL}/api/universities/UG_TBILISI")
        assert response.status_code == 200
        
        data = response.json()
        assert data["external_id"] == "UG_TBILISI"
        assert data["name"] == "University of Georgia (UG)"
        assert data["country"] == "Georgia"
        assert data["city"] == "Tbilisi"
        print(f"✓ UG_TBILISI details: {data['name']}, {data['city']}, {data['country']}")
    
    def test_get_single_university_nvu(self):
        """Test GET /api/universities/NVU"""
        response = requests.get(f"{BASE_URL}/api/universities/NVU")
        assert response.status_code == 200
        data = response.json()
        assert data["external_id"] == "NVU"
        print(f"✓ NVU details: {data['name']}")
    
    def test_get_single_university_iasi(self):
        """Test GET /api/universities/IASI_ROMANIA"""
        response = requests.get(f"{BASE_URL}/api/universities/IASI_ROMANIA")
        assert response.status_code == 200
        data = response.json()
        assert data["external_id"] == "IASI_ROMANIA"
        print(f"✓ IASI_ROMANIA details: {data['name']}")
    
    def test_get_single_university_aau(self):
        """Test GET /api/universities/AAU_AMMAN"""
        response = requests.get(f"{BASE_URL}/api/universities/AAU_AMMAN")
        assert response.status_code == 200
        data = response.json()
        assert data["external_id"] == "AAU_AMMAN"
        print(f"✓ AAU_AMMAN details: {data['name']}")
    
    def test_get_single_university_najah(self):
        """Test GET /api/universities/NAJAH"""
        response = requests.get(f"{BASE_URL}/api/universities/NAJAH")
        assert response.status_code == 200
        data = response.json()
        assert data["external_id"] == "NAJAH"
        print(f"✓ NAJAH details: {data['name']}")
    
    def test_get_nonexistent_university(self):
        """Test 404 for non-existent university"""
        response = requests.get(f"{BASE_URL}/api/universities/NONEXISTENT")
        assert response.status_code == 404
        print("✓ Non-existent university returns 404")


class TestCoursesAPI:
    """Test course endpoints - should have 486+ courses total"""
    
    def test_get_courses_by_university_ug(self):
        """Test GET /api/courses/by-university/UG_TBILISI"""
        response = requests.get(f"{BASE_URL}/api/courses/by-university/UG_TBILISI")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 50, f"Expected at least 50 UG courses, got {len(data)}"
        
        # Verify all courses have required fields
        for course in data[:5]:
            assert "external_id" in course
            assert "course_name" in course
            assert "mcq_count" in course
        
        print(f"✓ UG_TBILISI has {len(data)} courses")
    
    def test_get_courses_by_university_nvu(self):
        """Test GET /api/courses/by-university/NVU"""
        response = requests.get(f"{BASE_URL}/api/courses/by-university/NVU")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 50, f"Expected at least 50 NVU courses, got {len(data)}"
        print(f"✓ NVU has {len(data)} courses")
    
    def test_get_specific_course(self):
        """Test GET /api/courses/UG_DENT_Y1_S1_C01"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_DENT_Y1_S1_C01")
        assert response.status_code == 200
        
        data = response.json()
        assert data["external_id"] == "UG_DENT_Y1_S1_C01"
        assert data["course_name"] == "General Biology"
        assert "course_description" in data
        assert "semester" in data
        
        print(f"✓ Course UG_DENT_Y1_S1_C01: {data['course_name']}")
    
    def test_get_course_modules(self):
        """Test GET /api/courses/UG_DENT_Y1_S1_C01/modules"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_DENT_Y1_S1_C01/modules")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Expected at least 1 module"
        
        # Verify module structure
        module = data[0]
        assert "module_id" in module
        assert "title" in module
        assert "courseId" in module
        assert module["courseId"] == "UG_DENT_Y1_S1_C01"
        
        print(f"✓ Course UG_DENT_Y1_S1_C01 has {len(data)} modules")


class TestMCQQuestions:
    """Test MCQ questions - should have 300+ per course target, 145k+ total"""
    
    def test_get_course_questions(self):
        """Test GET /api/courses/UG_DENT_Y1_S1_C01/questions"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_DENT_Y1_S1_C01/questions?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "questions" in data
        assert isinstance(data["questions"], list)
        
        # Verify MCQ structure
        if len(data["questions"]) > 0:
            q = data["questions"][0]
            assert "question" in q
            assert "option_a" in q
            assert "option_b" in q
            assert "option_c" in q
            assert "option_d" in q
            assert "correct_answer" in q
            assert "explanation" in q
            assert q["correct_answer"] in ["A", "B", "C", "D"]
        
        print(f"✓ Course UG_DENT_Y1_S1_C01 has {data['total']} MCQ questions")
    
    def test_get_questions_with_difficulty(self):
        """Test filtering by difficulty"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_DENT_Y1_S1_C01/questions?difficulty=medium&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        # Verify all returned questions are medium difficulty
        for q in data["questions"]:
            if "difficulty" in q:
                assert q["difficulty"] == "medium", f"Expected medium, got {q.get('difficulty')}"
        
        print(f"✓ Difficulty filter working")


class TestDashboardStats:
    """Test dashboard statistics API"""
    
    def test_get_dashboard_stats(self):
        """Test GET /api/stats/dashboard returns comprehensive stats"""
        response = requests.get(f"{BASE_URL}/api/stats/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify structure
        assert "universities" in data
        assert "totals" in data
        
        totals = data["totals"]
        assert totals["totalUniversities"] == 5, f"Expected 5 universities, got {totals['totalUniversities']}"
        assert totals["totalCourses"] >= 400, f"Expected 400+ courses, got {totals['totalCourses']}"
        assert totals["totalQuestions"] >= 100000, f"Expected 100K+ MCQs, got {totals['totalQuestions']}"
        
        # Verify university breakdown
        for uni in data["universities"]:
            assert "external_id" in uni
            assert "totalCourses" in uni
            assert "totalQuestions" in uni
            assert "coursesWith300" in uni
            assert "completionRate" in uni
        
        print(f"✓ Dashboard stats: {totals['totalUniversities']} universities, {totals['totalCourses']} courses, {totals['totalQuestions']:,} MCQs")
        print(f"  - Courses with 300+ MCQs: {totals['coursesWith300']}")
        print(f"  - Completion rate: {totals['overallCompletion']:.1f}%")


class TestVideoEndpoints:
    """Test video generation endpoints"""
    
    def test_get_video_status(self):
        """Test GET /api/video/UG_DENT_Y1_S1_C01_M01"""
        response = requests.get(f"{BASE_URL}/api/video/UG_DENT_Y1_S1_C01_M01")
        assert response.status_code == 200
        
        data = response.json()
        assert data["module_id"] == "UG_DENT_Y1_S1_C01_M01"
        assert data["status"] == "completed"
        assert "video_url" in data or "video_path" in data
        
        print(f"✓ Video for module UG_DENT_Y1_S1_C01_M01: status={data['status']}")
        if "video_url" in data:
            print(f"  - video_url: {data['video_url']}")
    
    def test_get_course_scripts(self):
        """Test GET /api/courses/UG_DENT_Y1_S1_C01/scripts"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_DENT_Y1_S1_C01/scripts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            script = data[0]
            assert "script_id" in script
            assert "module_id" in script
            assert "script_text" in script
            assert "word_count" in script
            assert len(script["script_text"]) > 0, "Script text should not be empty"
        
        print(f"✓ Course UG_DENT_Y1_S1_C01 has {len(data)} scripts")


class TestCourseContent:
    """Test course content endpoints"""
    
    def test_get_course_content(self):
        """Test GET /api/courses/UG_DENT_Y1_S1_C01/content"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_DENT_Y1_S1_C01/content")
        assert response.status_code == 200
        
        data = response.json()
        assert "course_id" in data
        print(f"✓ Course content endpoint working")
    
    def test_get_course_status(self):
        """Test GET /api/courses/UG_DENT_Y1_S1_C01/status"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_DENT_Y1_S1_C01/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "questions_count" in data
        assert "scripts_count" in data
        
        print(f"✓ Course status: {data['status']}, MCQs: {data['questions_count']}, Scripts: {data['scripts_count']}")


class TestUGCoursesUnder300MCQ:
    """Test UG courses that have under 300 MCQs"""
    
    def test_identify_ug_courses_under_300(self):
        """Identify which UG courses have under 300 MCQs"""
        response = requests.get(f"{BASE_URL}/api/stats/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        
        # Find UG university stats
        ug_data = None
        for uni in data["universities"]:
            if uni["external_id"] == "UG_TBILISI":
                ug_data = uni
                break
        
        assert ug_data is not None, "UG_TBILISI not found in stats"
        
        under_300 = [c for c in ug_data["courses"] if c["mcq_count"] < 300]
        
        print(f"\n✓ UG courses with under 300 MCQs: {len(under_300)}")
        print(f"  Total UG courses: {ug_data['totalCourses']}")
        print(f"  Courses with 300+: {ug_data['coursesWith300']}")
        
        if len(under_300) > 0:
            print(f"\n  Courses needing more MCQs:")
            for c in under_300[:10]:  # Show first 10
                print(f"    - {c['external_id']}: {c['course_name']} ({c['mcq_count']} MCQs)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
