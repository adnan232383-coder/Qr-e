import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { 
  GraduationCap, 
  Sun, 
  Moon, 
  ArrowLeft,
  BookOpen, 
  ChevronRight,
  Stethoscope,
  Pill,
  Calendar,
  Clock
} from "lucide-react";
import ChatWidget from "@/components/ChatWidget";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CourseCatalog() {
  const navigate = useNavigate();
  const { majorId } = useParams();
  const { user, isAuthenticated, login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  
  const [major, setMajor] = useState(null);
  const [years, setYears] = useState([]);
  const [courses, setCourses] = useState([]);
  const [selectedYear, setSelectedYear] = useState(null);
  const [selectedSemester, setSelectedSemester] = useState("1");
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    if (majorId) {
      fetchMajorData();
    }
  }, [majorId]);

  useEffect(() => {
    if (selectedYear) {
      fetchCourses(selectedYear.external_id);
    }
  }, [selectedYear]);

  const fetchMajorData = async () => {
    setLoading(true);
    try {
      // Fetch major details
      const majorRes = await fetch(`${API}/majors/${majorId}`);
      if (majorRes.ok) {
        const majorData = await majorRes.json();
        setMajor(majorData);
      }

      // Fetch years for this major
      const yearsRes = await fetch(`${API}/years?major_id=${majorId}`);
      if (yearsRes.ok) {
        const yearsData = await yearsRes.json();
        setYears(yearsData);
        if (yearsData.length > 0) {
          setSelectedYear(yearsData[0]);
        }
      }
    } catch (e) {
      console.error("Error fetching major data:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchCourses = async (yearId) => {
    try {
      const response = await fetch(`${API}/courses?year_id=${yearId}`);
      if (response.ok) {
        const data = await response.json();
        setCourses(data);
      }
    } catch (e) {
      console.error("Error fetching courses:", e);
    }
  };

  const getMajorIcon = () => {
    if (major?.name?.toLowerCase().includes("dent")) return Stethoscope;
    if (major?.name?.toLowerCase().includes("pharm")) return Pill;
    return BookOpen;
  };

  const getMajorColor = () => {
    if (major?.name?.toLowerCase().includes("dent")) return "text-sky-500";
    if (major?.name?.toLowerCase().includes("pharm")) return "text-emerald-500";
    return "text-primary";
  };

  const filteredCourses = courses.filter(
    (course) => course.semester === parseInt(selectedSemester)
  );

  const Icon = getMajorIcon();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading curriculum...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="course-catalog-page">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(-1)}
                data-testid="back-btn"
                className="rounded-full"
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div 
                className="flex items-center gap-3 cursor-pointer"
                onClick={() => navigate("/")}
                data-testid="nav-logo"
              >
                <GraduationCap className="h-8 w-8 text-primary" />
                <span className="text-xl font-semibold hidden sm:inline">UG Assistant</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                data-testid="theme-toggle-btn"
                className="rounded-full"
              >
                {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
              
              {isAuthenticated ? (
                <Button
                  onClick={() => navigate("/dashboard")}
                  variant="outline"
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
                  Sign In
                </Button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Sidebar */}
          <aside className="lg:col-span-3">
            <div className="sticky top-24">
              {/* Major Info */}
              <Card className="mb-6 overflow-hidden">
                {major?.image_url && (
                  <div className="aspect-video">
                    <img
                      src={major.image_url}
                      alt={major.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <CardContent className="p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <Icon className={`h-6 w-6 ${getMajorColor()}`} />
                    <h1 className="text-xl font-bold">{major?.name}</h1>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {major?.degree} Program • {major?.years} Years
                  </p>
                </CardContent>
              </Card>

              {/* Year Navigation */}
              <div className="space-y-2">
                <h2 className="text-sm font-medium text-muted-foreground px-2 mb-3">
                  Select Year
                </h2>
                {years.map((year) => (
                  <button
                    key={year.external_id}
                    onClick={() => setSelectedYear(year)}
                    className={`w-full sidebar-nav-item ${
                      selectedYear?.external_id === year.external_id ? 'active' : ''
                    }`}
                    data-testid={`year-btn-${year.year_number}`}
                  >
                    <Calendar className="h-4 w-4" />
                    <span>{year.year_title}</span>
                  </button>
                ))}
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-9">
            {/* Header */}
            <div className="mb-6">
              <h2 className="text-2xl font-bold mb-2">
                {selectedYear?.year_title} Courses
              </h2>
              <p className="text-muted-foreground">
                {filteredCourses.length} courses in Semester {selectedSemester}
              </p>
            </div>

            {/* Semester Tabs */}
            <Tabs value={selectedSemester} onValueChange={setSelectedSemester} className="mb-6">
              <TabsList className="grid w-full max-w-md grid-cols-2">
                <TabsTrigger value="1" data-testid="semester-1-tab">
                  Semester 1
                </TabsTrigger>
                <TabsTrigger value="2" data-testid="semester-2-tab">
                  Semester 2
                </TabsTrigger>
              </TabsList>
            </Tabs>

            {/* Course Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger-children">
              {filteredCourses.map((course) => (
                <Card
                  key={course.external_id}
                  className="group cursor-pointer course-card hover:border-primary/50 transition-all duration-300 card-hover"
                  onClick={() => navigate(`/course/${course.external_id}`)}
                  data-testid={`course-card-${course.external_id}`}
                >
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-semibold mb-2 group-hover:text-primary transition-colors">
                          {course.course_name}
                        </h3>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {course.course_description}
                        </p>
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                    <div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="mono bg-secondary px-2 py-1 rounded">
                        {course.external_id.split('_').slice(-1)[0]}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Semester {course.semester}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {filteredCourses.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No courses found for this semester</p>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Chat Widget */}
      <ChatWidget isOpen={chatOpen} onToggle={() => setChatOpen(!chatOpen)} />
    </div>
  );
}
