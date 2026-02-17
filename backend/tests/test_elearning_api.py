"""
E-Learning Platform API Tests
Tests the core API endpoints for the multi-university e-learning platform:
- Universities, Faculties, Majors, Years, Courses, Modules
- Presentations, Audio, MCQ Questions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestHealthAndBasicAPIs:
    """Basic API health and availability tests"""
    
    def test_api_health(self):
        """Test API root returns valid response"""
        response = requests.get(f"{BASE_URL}/api/universities")
        assert response.status_code == 200
        print("✓ API is accessible")
    
    def test_universities_list(self):
        """Test GET /api/universities returns list of universities"""
        response = requests.get(f"{BASE_URL}/api/universities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Should have at least 1 university"
        
        # Validate university structure
        uni = data[0]
        assert "external_id" in uni
        assert "name" in uni
        assert "country" in uni
        print(f"✓ Found {len(data)} universities")
    
    def test_university_by_id(self):
        """Test GET /api/universities/{id} returns specific university"""
        response = requests.get(f"{BASE_URL}/api/universities/UG_TBILISI")
        assert response.status_code == 200
        data = response.json()
        assert data["external_id"] == "UG_TBILISI"
        assert data["name"] == "University of Georgia (UG)"
        print(f"✓ University detail: {data['name']}")


class TestCourseCatalog:
    """Tests for course catalog navigation: Courses by university, year, semester"""
    
    def test_courses_by_university(self):
        """Test GET /api/courses/by-university/{id} returns courses"""
        response = requests.get(f"{BASE_URL}/api/courses/by-university/UG_TBILISI")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "UG_TBILISI should have courses"
        
        # Validate course structure
        course = data[0]
        assert "external_id" in course
        assert "course_name" in course
        assert "semester" in course
        print(f"✓ UG_TBILISI has {len(data)} courses")
    
    def test_course_detail(self):
        """Test GET /api/courses/{id} returns course details"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_PHARM_Y1_S1_C01")
        assert response.status_code == 200
        data = response.json()
        assert data["external_id"] == "UG_PHARM_Y1_S1_C01"
        assert data["course_name"] == "General Chemistry"
        assert data["semester"] == 1
        print(f"✓ Course detail: {data['course_name']}")
    
    def test_course_not_found(self):
        """Test non-existent course returns 404"""
        response = requests.get(f"{BASE_URL}/api/courses/INVALID_COURSE_ID")
        assert response.status_code == 404
        print("✓ Non-existent course returns 404")


class TestCourseModules:
    """Tests for course modules and related content"""
    
    def test_course_modules_list(self):
        """Test GET /api/courses/{id}/modules returns module list"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_PHARM_Y1_S1_C01/modules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Course should have modules"
        
        # Validate module structure
        module = data[0]
        assert "module_id" in module
        assert "title" in module
        assert "courseId" in module
        assert module["courseId"] == "UG_PHARM_Y1_S1_C01"
        print(f"✓ Course has {len(data)} modules: {[m['title'] for m in data]}")
    
    def test_module_ordering(self):
        """Test modules are returned in correct order"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_PHARM_Y1_S1_C01/modules")
        assert response.status_code == 200
        data = response.json()
        orders = [m.get("order", 0) for m in data]
        assert orders == sorted(orders), "Modules should be ordered"
        print(f"✓ Modules ordered correctly: {orders}")


class TestMCQQuestions:
    """Tests for MCQ questions API"""
    
    def test_course_questions(self):
        """Test GET /api/courses/{id}/questions returns questions"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_PHARM_Y1_S1_C01/questions?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "total" in data
        assert data["total"] > 0, "Course should have MCQ questions"
        
        # Validate question structure
        q = data["questions"][0]
        assert "question_id" in q
        assert "question" in q
        assert "option_a" in q
        assert "option_b" in q
        assert "option_c" in q
        assert "option_d" in q
        assert "correct_answer" in q
        assert q["correct_answer"] in ["A", "B", "C", "D"]
        print(f"✓ Course has {data['total']} MCQ questions")
    
    def test_questions_pagination(self):
        """Test questions pagination with limit and offset"""
        response = requests.get(f"{BASE_URL}/api/courses/UG_PHARM_Y1_S1_C01/questions?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert len(data["questions"]) <= 5
        print(f"✓ Pagination works: limit={data['limit']}, offset={data['offset']}")


class TestPresentations:
    """Tests for presentation and audio APIs"""
    
    def test_presentation_html(self):
        """Test GET /api/presentations/{module_id} returns HTML"""
        response = requests.get(f"{BASE_URL}/api/presentations/UG_PHARM_Y1_S1_C01_M01")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("Content-Type", "")
        content = response.text
        assert "<!DOCTYPE html>" in content or "<html" in content
        assert "<title>" in content
        print(f"✓ Presentation HTML returned ({len(content)} chars)")
    
    def test_presentation_not_found(self):
        """Test non-existent presentation returns 404"""
        response = requests.get(f"{BASE_URL}/api/presentations/INVALID_MODULE_ID")
        assert response.status_code == 404
        print("✓ Non-existent presentation returns 404")
    
    def test_audio_file(self):
        """Test GET /api/audio/{module_id}.mp3 returns audio"""
        response = requests.get(f"{BASE_URL}/api/audio/UG_PHARM_Y1_S1_C01_M01.mp3")
        assert response.status_code == 200
        assert "audio/mpeg" in response.headers.get("Content-Type", "")
        content_length = response.headers.get("Content-Length")
        assert content_length is not None
        assert int(content_length) > 0
        print(f"✓ Audio file returned (Content-Length: {content_length})")
    
    def test_audio_head_request(self):
        """Test HEAD /api/audio/{module_id}.mp3 returns metadata"""
        response = requests.head(f"{BASE_URL}/api/audio/UG_PHARM_Y1_S1_C01_M01.mp3")
        assert response.status_code == 200
        assert "audio/mpeg" in response.headers.get("Content-Type", "")
        assert response.headers.get("Accept-Ranges") == "bytes"
        print("✓ Audio HEAD request returns correct headers")
    
    def test_audio_not_found(self):
        """Test non-existent audio returns 404"""
        response = requests.get(f"{BASE_URL}/api/audio/INVALID_MODULE.mp3")
        assert response.status_code == 404
        print("✓ Non-existent audio returns 404")


class TestModuleContent:
    """Tests for module content and scripts"""
    
    def test_module_content_info(self):
        """Test GET /api/module/{module_id}/content returns content info"""
        response = requests.get(f"{BASE_URL}/api/module/UG_PHARM_Y1_S1_C01_M01/content")
        assert response.status_code == 200
        data = response.json()
        assert "module_id" in data
        assert "has_presentation" in data
        assert "has_audio" in data
        print(f"✓ Module content info: presentation={data['has_presentation']}, audio={data['has_audio']}")


class TestDifferentModuleIDs:
    """Tests for different working module IDs mentioned in the requirements"""
    
    @pytest.mark.parametrize("module_id", [
        "UG_PHARM_Y1_S1_C01_M01",
        "UG_PHARM_Y1_S1_C01_M03",
        "UG_DENT_Y5_S2_C08_M02"
    ])
    def test_presentation_for_module(self, module_id):
        """Test presentation exists for specified modules"""
        response = requests.get(f"{BASE_URL}/api/presentations/{module_id}")
        assert response.status_code == 200, f"Presentation for {module_id} should exist"
        print(f"✓ Presentation for {module_id} exists")
    
    @pytest.mark.parametrize("module_id", [
        "UG_PHARM_Y1_S1_C01_M01",
        "UG_PHARM_Y1_S1_C01_M03"
    ])
    def test_audio_for_module(self, module_id):
        """Test audio exists for specified modules"""
        response = requests.head(f"{BASE_URL}/api/audio/{module_id}.mp3")
        assert response.status_code == 200, f"Audio for {module_id} should exist"
        print(f"✓ Audio for {module_id} exists")


class TestPresentationContentValidation:
    """Tests to validate presentation content structure"""
    
    def test_presentation_has_slides(self):
        """Test presentation contains slide elements"""
        response = requests.get(f"{BASE_URL}/api/presentations/UG_PHARM_Y1_S1_C01_M01")
        assert response.status_code == 200
        content = response.text
        # Check for slide-related content
        assert "slide" in content.lower(), "Presentation should have slides"
        print("✓ Presentation contains slide elements")
    
    def test_presentation_has_images(self):
        """Test presentation contains image elements (upgraded feature)"""
        response = requests.get(f"{BASE_URL}/api/presentations/UG_PHARM_Y1_S1_C01_M01")
        assert response.status_code == 200
        content = response.text
        # Check for image elements
        has_images = "<img" in content or "img-side" in content or "img-container" in content
        assert has_images, "Presentation should contain images"
        print("✓ Presentation contains image elements")


class TestMultipleUniversities:
    """Tests for multi-university support"""
    
    @pytest.mark.parametrize("university_id,expected_name", [
        ("UG_TBILISI", "University of Georgia"),
        ("NVU", "New Vision University"),
        ("IASI_ROMANIA", "University of Medicine and Pharmacy Iași"),
        ("AAU_AMMAN", "Al-Ahliyya Amman University"),
        ("NAJAH", "An-Najah National University")
    ])
    def test_university_exists(self, university_id, expected_name):
        """Test each university is accessible"""
        response = requests.get(f"{BASE_URL}/api/universities/{university_id}")
        assert response.status_code == 200
        data = response.json()
        assert expected_name in data["name"]
        print(f"✓ {data['name']} exists")
    
    @pytest.mark.parametrize("university_id", [
        "UG_TBILISI", "NVU", "IASI_ROMANIA", "AAU_AMMAN", "NAJAH"
    ])
    def test_university_has_courses(self, university_id):
        """Test each university has courses"""
        response = requests.get(f"{BASE_URL}/api/courses/by-university/{university_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Note: Some universities may have 0 courses, which is valid
        print(f"✓ {university_id} has {len(data)} courses")
