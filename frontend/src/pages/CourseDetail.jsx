import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { 
  GraduationCap, 
  Sun, 
  Moon, 
  ArrowLeft,
  BookOpen, 
  Clock,
  FileText,
  MessageSquare
} from "lucide-react";
import ChatWidget from "@/components/ChatWidget";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CourseDetail() {
  const navigate = useNavigate();
  const { courseId } = useParams();
  const { user, isAuthenticated, login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  
  const [course, setCourse] = useState(null);
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    if (courseId) {
      fetchCourseData();
    }
  }, [courseId]);

  const fetchCourseData = async () => {
    setLoading(true);
    try {
      // Fetch course details
      const courseRes = await fetch(`${API}/courses/${courseId}`);
      if (courseRes.ok) {
        const courseData = await courseRes.json();
        setCourse(courseData);
      }

      // Fetch course content
      const contentRes = await fetch(`${API}/courses/${courseId}/content`);
      if (contentRes.ok) {
        const contentData = await contentRes.json();
        setContent(contentData);
      }
    } catch (e) {
      console.error("Error fetching course data:", e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading course...</div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Course not found</p>
          <Button onClick={() => navigate(-1)} className="mt-4">
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="course-detail-page">
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
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Course Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-3 text-sm text-muted-foreground mb-4">
            <span className="mono bg-secondary px-2 py-1 rounded">
              {course.external_id.split('_').slice(-1)[0]}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              Semester {course.semester}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">{course.course_name}</h1>
          <p className="text-lg text-muted-foreground">{course.course_description}</p>
        </div>

        <Separator className="my-8" />

        {/* Course Summary */}
        <Card className="mb-8 animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Course Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            {content?.summary ? (
              <div className="prose dark:prose-invert max-w-none">
                <p>{content.summary}</p>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-10 w-10 mx-auto mb-3 opacity-50" />
                <p>Course summary coming soon</p>
                <p className="text-sm mt-2">
                  Use the AI Study Assistant to learn about this topic
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI Assistant CTA */}
        <Card 
          className="bg-primary/5 border-primary/20 cursor-pointer hover:bg-primary/10 transition-colors"
          onClick={() => setChatOpen(true)}
          data-testid="ai-assistant-cta"
        >
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 rounded-xl bg-primary/10">
              <MessageSquare className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">Need help understanding this course?</h3>
              <p className="text-sm text-muted-foreground">
                Ask our AI Study Assistant any questions about {course.course_name}
              </p>
            </div>
            <Button data-testid="ask-ai-btn">
              Ask AI
            </Button>
          </CardContent>
        </Card>

        {/* Chapters (if available) */}
        {content?.chapters && content.chapters.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-bold mb-4">Course Chapters</h2>
            <div className="space-y-3">
              {content.chapters.map((chapter, index) => (
                <Card key={index} className="card-hover">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <span className="mono text-sm bg-secondary px-2 py-1 rounded">
                        {index + 1}
                      </span>
                      <span className="font-medium">{chapter.title || chapter}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Chat Widget */}
      <ChatWidget 
        isOpen={chatOpen} 
        onToggle={() => setChatOpen(!chatOpen)} 
        courseId={courseId}
        courseName={course?.course_name}
      />
    </div>
  );
}
