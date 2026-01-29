import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
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
  MessageSquare,
  Play,
  CheckCircle,
  ListOrdered
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
  const [modules, setModules] = useState([]);
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

      // Fetch course modules
      const modulesRes = await fetch(`${API}/courses/${courseId}/modules`);
      if (modulesRes.ok) {
        const modulesData = await modulesRes.json();
        setModules(modulesData || []);
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

  const totalDuration = modules.reduce((sum, mod) => sum + (mod.duration_hours || 0), 0);

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
            {modules.length > 0 && (
              <span className="flex items-center gap-1">
                <ListOrdered className="h-4 w-4" />
                {modules.length} Modules
              </span>
            )}
            {totalDuration > 0 && (
              <span className="flex items-center gap-1">
                <Play className="h-4 w-4" />
                {totalDuration} Hours
              </span>
            )}
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">{course.course_name}</h1>
          <p className="text-lg text-muted-foreground">{course.course_description}</p>
        </div>

        <Separator className="my-8" />

        {/* Course Modules Section */}
        <Card className="mb-8 animate-slide-up" data-testid="modules-section">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ListOrdered className="h-5 w-5 text-primary" />
              Course Modules
              {modules.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {modules.length} modules
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {modules.length > 0 ? (
              <Accordion type="single" collapsible className="w-full">
                {modules.map((module, index) => (
                  <AccordionItem 
                    key={module.module_id} 
                    value={module.module_id}
                    data-testid={`module-item-${index}`}
                  >
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center gap-4 text-left">
                        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm">
                          {module.order || index + 1}
                        </span>
                        <div>
                          <div className="font-semibold">{module.title}</div>
                          <div className="text-sm text-muted-foreground flex items-center gap-2 mt-1">
                            {module.duration_hours && (
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {module.duration_hours}h
                              </span>
                            )}
                            {module.topics && module.topics.length > 0 && (
                              <span>• {module.topics.length} topics</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="pl-12 space-y-4">
                        {module.description && (
                          <p className="text-muted-foreground">{module.description}</p>
                        )}
                        {module.topics && module.topics.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-2">Topics Covered:</h4>
                            <ul className="space-y-2">
                              {module.topics.map((topic, topicIdx) => (
                                <li 
                                  key={topicIdx} 
                                  className="flex items-center gap-2 text-sm"
                                  data-testid={`topic-${index}-${topicIdx}`}
                                >
                                  <CheckCircle className="h-4 w-4 text-primary flex-shrink-0" />
                                  <span>{topic}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <ListOrdered className="h-10 w-10 mx-auto mb-3 opacity-50" />
                <p>No modules available yet</p>
                <p className="text-sm mt-2">
                  Course content is being prepared
                </p>
              </div>
            )}
          </CardContent>
        </Card>

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

        {/* Legacy Chapters (if available) */}
        {content?.chapters && content.chapters.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-bold mb-4">Additional Chapters</h2>
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
