import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";
import { 
  GraduationCap, 
  BookOpen, 
  MessageSquare, 
  Sun, 
  Moon, 
  ChevronRight,
  Stethoscope,
  Pill,
  Users,
  Globe,
  Award,
  Building2,
  Heart,
  Search,
  X
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Landing() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, login, isAuthenticated } = useAuth();
  const [universities, setUniversities] = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState({ universities: [], courses: [] });
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef(null);

  useEffect(() => {
    fetchUniversities();
    fetchAllCourses();
    seedDatabase();
  }, []);

  // Close search results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Search filter
  useEffect(() => {
    if (searchQuery.trim() === "") {
      setSearchResults({ universities: [], courses: [] });
      setShowResults(false);
      return;
    }

    const query = searchQuery.toLowerCase();
    
    const filteredUniversities = universities.filter(u => 
      u.name.toLowerCase().includes(query) || 
      u.city?.toLowerCase().includes(query)
    );
    
    const filteredCourses = allCourses.filter(c => 
      c.course_name.toLowerCase().includes(query)
    ).slice(0, 10); // Limit to 10 results

    setSearchResults({ universities: filteredUniversities, courses: filteredCourses });
    setShowResults(true);
  }, [searchQuery, universities, allCourses]);

  const seedDatabase = async () => {
    try {
      await fetch(`${API}/seed`, { method: "POST" });
    } catch (e) {
      console.error("Seed error:", e);
    }
  };

  const fetchUniversities = async () => {
    try {
      const response = await fetch(`${API}/universities`);
      if (response.ok) {
        const data = await response.json();
        setUniversities(data);
      }
    } catch (e) {
      console.error("Error fetching universities:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllCourses = async () => {
    try {
      // Fetch courses from all universities
      const uniIds = ["UG_TBILISI", "NVU", "IASI_ROMANIA", "AAU_AMMAN", "NAJAH"];
      const responses = await Promise.all(
        uniIds.map(id => fetch(`${API}/courses/by-university/${id}`))
      );
      
      let courses = [];
      for (let i = 0; i < responses.length; i++) {
        if (responses[i].ok) {
          const data = await responses[i].json();
          courses = [...courses, ...data.map(c => ({ ...c, university: uniIds[i] }))];
        }
      }
      setAllCourses(courses);
    } catch (e) {
      console.error("Error fetching courses:", e);
    }
  };

  const getUniversityIcon = (name) => {
    if (name.toLowerCase().includes("georgia")) return Building2;
    if (name.toLowerCase().includes("vision")) return Heart;
    if (name.toLowerCase().includes("iași") || name.toLowerCase().includes("iasi")) return Stethoscope;
    if (name.toLowerCase().includes("amman") || name.toLowerCase().includes("aau")) return Globe;
    if (name.toLowerCase().includes("najah")) return Award;
    return GraduationCap;
  };

  const getUniversityColor = (id) => {
    if (id === "UG_TBILISI") return "from-sky-500/20 to-blue-500/10";
    if (id === "NVU") return "from-emerald-500/20 to-teal-500/10";
    if (id === "IASI_ROMANIA") return "from-purple-500/20 to-violet-500/10";
    if (id === "AAU_AMMAN") return "from-amber-500/20 to-orange-500/10";
    if (id === "NAJAH") return "from-rose-500/20 to-pink-500/10";
    return "from-primary/20 to-accent/10";
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-50 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <GraduationCap className="h-8 w-8 text-primary" />
              <span className="text-xl font-semibold">Medical Studies</span>
            </div>
            
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                data-testid="theme-toggle-btn"
                className="rounded-full"
              >
                {theme === "light" ? (
                  <Moon className="h-5 w-5" />
                ) : (
                  <Sun className="h-5 w-5" />
                )}
              </Button>
              
              {isAuthenticated ? (
                <Button
                  onClick={() => navigate("/dashboard")}
                  data-testid="dashboard-btn"
                  className="rounded-full"
                >
                  Dashboard
                </Button>
              ) : (
                <Button
                  onClick={login}
                  data-testid="login-btn"
                  className="rounded-full"
                >
                  Sign In with Google
                </Button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 lg:py-32 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/10" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center max-w-3xl mx-auto animate-fade-in">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6" style={{ letterSpacing: '-0.02em' }}>
              Your{" "}
              <span className="text-primary">Medical Education</span>
              {" "}Journey
            </h1>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
              Navigate your medical education with AI-powered course summaries, MCQ practice, and an intelligent study assistant across multiple universities.
            </p>
            
            {/* Search Box */}
            <div className="max-w-xl mx-auto mb-8" ref={searchRef}>
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Search courses or universities..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-14 pl-12 pr-12 text-lg rounded-full border-2 focus:border-primary"
                  data-testid="search-input"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
              </div>
              
              {/* Search Results Dropdown */}
              {showResults && (searchResults.universities.length > 0 || searchResults.courses.length > 0) && (
                <div className="absolute left-0 right-0 mt-2 mx-auto max-w-xl bg-card border border-border rounded-2xl shadow-lg overflow-hidden z-50">
                  {/* Universities Results */}
                  {searchResults.universities.length > 0 && (
                    <div className="p-2">
                      <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase">
                        Universities
                      </div>
                      {searchResults.universities.map((uni) => (
                        <button
                          key={uni.external_id}
                          onClick={() => {
                            navigate(`/university/${uni.external_id}`);
                            setShowResults(false);
                            setSearchQuery("");
                          }}
                          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent text-left transition-colors"
                          data-testid={`search-result-uni-${uni.external_id}`}
                        >
                          <Building2 className="h-5 w-5 text-primary" />
                          <div>
                            <div className="font-medium">{uni.name}</div>
                            <div className="text-sm text-muted-foreground">{uni.city}, {uni.country}</div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                  
                  {/* Courses Results */}
                  {searchResults.courses.length > 0 && (
                    <div className="p-2 border-t border-border">
                      <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase">
                        Courses
                      </div>
                      {searchResults.courses.map((course) => {
                        const uniNames = {
                          "UG_TBILISI": "University of Georgia",
                          "NVU": "New Vision University",
                          "IASI_ROMANIA": "IASI Romania",
                          "AAU_AMMAN": "AAU Amman",
                          "NAJAH": "An-Najah University"
                        };
                        return (
                        <button
                          key={course.external_id}
                          onClick={() => {
                            navigate(`/course/${course.external_id}`);
                            setShowResults(false);
                            setSearchQuery("");
                          }}
                          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-accent text-left transition-colors"
                          data-testid={`search-result-course-${course.external_id}`}
                        >
                          <BookOpen className="h-5 w-5 text-primary" />
                          <div>
                            <div className="font-medium">{course.course_name}</div>
                            <div className="text-sm text-muted-foreground">
                              {uniNames[course.university] || course.university}
                              {course.mcq_count > 0 && ` • ${course.mcq_count} MCQs`}
                            </div>
                          </div>
                        </button>
                      )})}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => document.getElementById('universities')?.scrollIntoView({ behavior: 'smooth' })}
                data-testid="explore-courses-btn"
                className="rounded-full h-12 px-8"
              >
                Choose University
                <ChevronRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={login}
                data-testid="get-started-btn"
                className="rounded-full h-12 px-8"
              >
                Get Started Free
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-border/50 bg-secondary/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
              <div className="text-3xl font-bold text-primary">{allCourses.length > 0 ? `${allCourses.length}+` : '490+'}</div>
              <div className="text-sm text-muted-foreground mt-1">Courses</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="text-3xl font-bold text-primary">{universities.length || 5}</div>
              <div className="text-sm text-muted-foreground mt-1">Universities</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <div className="text-3xl font-bold text-primary">{allCourses.length > 0 ? `${Math.round(allCourses.reduce((sum, c) => sum + (c.mcq_count || 0), 0) / 1000)}K+` : '150K+'}</div>
              <div className="text-sm text-muted-foreground mt-1">MCQ Questions</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.4s' }}>
              <div className="text-3xl font-bold text-primary">AI</div>
              <div className="text-sm text-muted-foreground mt-1">Study Assistant</div>
            </div>
          </div>
        </div>
      </section>

      {/* Universities Section */}
      <section id="universities" className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Choose Your University</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Select your university to explore courses and start practicing
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto stagger-children">
            {universities.map((uni) => {
              const Icon = getUniversityIcon(uni.name);
              const gradientClass = getUniversityColor(uni.external_id);
              
              return (
                <Card
                  key={uni.external_id}
                  className={`group cursor-pointer overflow-hidden transition-all duration-300 hover:border-primary/50 card-hover bg-gradient-to-br ${gradientClass}`}
                  onClick={() => navigate(`/university/${uni.external_id}`)}
                  data-testid={`university-card-${uni.external_id}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-xl bg-background text-primary">
                        <Icon className="h-6 w-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-bold mb-1 truncate">{uni.name}</h3>
                        <p className="text-sm text-muted-foreground mb-2">
                          {uni.city}, {uni.country}
                        </p>
                        <div className="flex items-center text-sm text-primary font-medium group-hover:gap-2 transition-all">
                          Explore Courses
                          <ChevronRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 lg:py-24 bg-secondary/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Everything You Need</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Tools designed to support your academic success
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border-border/50 card-hover">
              <CardContent className="p-6">
                <div className="p-3 rounded-xl bg-accent w-fit mb-4">
                  <BookOpen className="h-6 w-6 text-accent-foreground" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Course Catalog</h3>
                <p className="text-muted-foreground">
                  Browse all courses organized by year and semester with detailed descriptions
                </p>
              </CardContent>
            </Card>
            
            <Card className="border-border/50 card-hover">
              <CardContent className="p-6">
                <div className="p-3 rounded-xl bg-accent w-fit mb-4">
                  <Award className="h-6 w-6 text-accent-foreground" />
                </div>
                <h3 className="text-xl font-semibold mb-2">MCQ Practice</h3>
                <p className="text-muted-foreground">
                  Practice with thousands of multiple choice questions for each course
                </p>
              </CardContent>
            </Card>
            
            <Card className="border-border/50 card-hover">
              <CardContent className="p-6">
                <div className="p-3 rounded-xl bg-accent w-fit mb-4">
                  <MessageSquare className="h-6 w-6 text-accent-foreground" />
                </div>
                <h3 className="text-xl font-semibold mb-2">AI Study Assistant</h3>
                <p className="text-muted-foreground">
                  Get instant help with course material using our GPT-powered chatbot
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-border bg-secondary/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-primary" />
              <span className="font-medium">Medical Studies Platform</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Supporting medical students worldwide
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
