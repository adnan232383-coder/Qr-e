import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { toast } from "sonner";
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
  ListOrdered,
  HelpCircle,
  Loader2,
  AlertCircle,
  RefreshCw,
  Video,
  Check,
  X
} from "lucide-react";
import ChatWidget from "@/components/ChatWidget";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Status badge component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    pending: { color: "bg-gray-500", label: "Pending" },
    generating: { color: "bg-yellow-500", label: "Generating..." },
    reviewed: { color: "bg-blue-500", label: "Ready" },
    published: { color: "bg-green-500", label: "Published" },
    failed: { color: "bg-red-500", label: "Failed" }
  };
  
  const config = statusConfig[status] || statusConfig.pending;
  
  return (
    <Badge className={`${config.color} text-white`}>
      {status === "generating" && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
      {config.label}
    </Badge>
  );
};

export default function CourseDetail() {
  const navigate = useNavigate();
  const { courseId } = useParams();
  const { user, isAuthenticated, login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  
  const [course, setCourse] = useState(null);
  const [content, setContent] = useState(null);
  const [modules, setModules] = useState([]);
  const [contentStatus, setContentStatus] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [scripts, setScripts] = useState([]);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatingVideos, setGeneratingVideos] = useState(false);
  const [generatingMCQ, setGeneratingMCQ] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  
  // Quiz state
  const [quizMode, setQuizMode] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [score, setScore] = useState(0);
  const [answeredQuestions, setAnsweredQuestions] = useState([]);

  useEffect(() => {
    if (courseId) {
      fetchAllData();
    }
  }, [courseId]);

  // Poll for status updates when generating
  useEffect(() => {
    let interval;
    if (contentStatus?.status === "generating") {
      interval = setInterval(() => {
        fetchContentStatus();
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [contentStatus?.status]);

  const fetchAllData = async () => {
    setLoading(true);
    await Promise.all([
      fetchCourseData(),
      fetchContentStatus(),
      fetchQuestions(),
      fetchScripts(),
      fetchVideos()
    ]);
    setLoading(false);
  };

  const fetchCourseData = async () => {
    try {
      const [courseRes, contentRes, modulesRes] = await Promise.all([
        fetch(`${API}/courses/${courseId}`),
        fetch(`${API}/courses/${courseId}/content`),
        fetch(`${API}/courses/${courseId}/modules`)
      ]);
      
      if (courseRes.ok) setCourse(await courseRes.json());
      if (contentRes.ok) setContent(await contentRes.json());
      if (modulesRes.ok) setModules(await modulesRes.json() || []);
    } catch (e) {
      console.error("Error fetching course data:", e);
    }
  };

  const fetchContentStatus = async () => {
    try {
      const res = await fetch(`${API}/courses/${courseId}/status`);
      if (res.ok) {
        setContentStatus(await res.json());
      }
    } catch (e) {
      console.error("Error fetching content status:", e);
    }
  };

  const fetchQuestions = async () => {
    try {
      const res = await fetch(`${API}/courses/${courseId}/questions?limit=200`);
      if (res.ok) {
        const data = await res.json();
        setQuestions(data.questions || []);
      }
    } catch (e) {
      console.error("Error fetching questions:", e);
    }
  };

  const fetchScripts = async () => {
    try {
      const res = await fetch(`${API}/courses/${courseId}/scripts`);
      if (res.ok) {
        setScripts(await res.json() || []);
      }
    } catch (e) {
      console.error("Error fetching scripts:", e);
    }
  };

  const fetchVideos = async () => {
    try {
      // Fetch videos for all modules in this course
      const modulesRes = await fetch(`${API}/courses/${courseId}/modules`);
      if (modulesRes.ok) {
        const modulesData = await modulesRes.json();
        const videoPromises = modulesData.map(m => 
          fetch(`${API}/video/${m.module_id}`).then(r => r.ok ? r.json() : null).catch(() => null)
        );
        const videosData = await Promise.all(videoPromises);
        setVideos(videosData.filter(v => v && v.video_path));
      }
    } catch (e) {
      console.error("Error fetching videos:", e);
    }
  };

  const generateContent = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/content/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_id: courseId })
      });
      
      if (res.ok) {
        toast.success("Content generation started!");
        await fetchContentStatus();
      } else {
        toast.error("Failed to start content generation");
      }
    } catch (e) {
      toast.error("Error starting content generation");
    } finally {
      setGenerating(false);
    }
  };

  const generateMCQ = async () => {
    setGeneratingMCQ(true);
    try {
      const res = await fetch(`${API}/content/generate-mcq/${courseId}?count=200`, {
        method: "POST"
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Generated ${data.questions_count} MCQ questions!`);
        await fetchQuestions();
      } else {
        toast.error("Failed to generate MCQ questions");
      }
    } catch (e) {
      toast.error("Error generating MCQ questions");
    } finally {
      setGeneratingMCQ(false);
    }
  };

  const generateVideos = async () => {
    setGeneratingVideos(true);
    try {
      const res = await fetch(`${API}/video/generate-course/${courseId}`, {
        method: "POST"
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(`Queued ${data.modules.length} videos for generation!`);
        // Poll for video status
        setTimeout(() => fetchVideos(), 30000);
      } else {
        toast.error("Failed to start video generation");
      }
    } catch (e) {
      toast.error("Error starting video generation");
    } finally {
      setGeneratingVideos(false);
    }
  };

  // Quiz functions
  const startQuiz = () => {
    setQuizMode(true);
    setCurrentQuestion(0);
    setScore(0);
    setAnsweredQuestions([]);
    setSelectedAnswer(null);
    setShowExplanation(false);
  };

  const selectAnswer = (answer) => {
    if (showExplanation) return;
    setSelectedAnswer(answer);
  };

  const submitAnswer = () => {
    const q = questions[currentQuestion];
    const isCorrect = selectedAnswer === q.correct_answer;
    if (isCorrect) setScore(s => s + 1);
    setAnsweredQuestions([...answeredQuestions, { index: currentQuestion, isCorrect, selected: selectedAnswer }]);
    setShowExplanation(true);
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(c => c + 1);
      setSelectedAnswer(null);
      setShowExplanation(false);
    } else {
      setQuizMode(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading course...</p>
        </div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">Course not found</p>
          <Button onClick={() => navigate(-1)} className="mt-4">Go Back</Button>
        </div>
      </div>
    );
  }

  const totalDuration = modules.reduce((sum, mod) => sum + (mod.duration_hours || 0), 0);
  const hasContent = content?.summary || questions.length > 0;
  const isPending = !contentStatus || contentStatus.status === "pending";
  const isGenerating = contentStatus?.status === "generating";

  return (
    <div className="min-h-screen bg-background" data-testid="course-detail-page">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate(-1)} data-testid="back-btn" className="rounded-full">
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")} data-testid="nav-logo">
                <GraduationCap className="h-8 w-8 text-primary" />
                <span className="text-xl font-semibold hidden sm:inline">UG Assistant</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={toggleTheme} data-testid="theme-toggle-btn" className="rounded-full">
                {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
              
              {isAuthenticated ? (
                <Button onClick={() => navigate("/dashboard")} variant="outline" data-testid="dashboard-btn" className="rounded-full">
                  Dashboard
                </Button>
              ) : (
                <Button onClick={login} data-testid="login-btn" className="rounded-full">Sign In</Button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Course Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-3 text-sm text-muted-foreground mb-4 flex-wrap">
            <span className="mono bg-secondary px-2 py-1 rounded">{course.external_id.split('_').slice(-1)[0]}</span>
            <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> Semester {course.semester}</span>
            {modules.length > 0 && <span className="flex items-center gap-1"><ListOrdered className="h-4 w-4" /> {modules.length} Modules</span>}
            {totalDuration > 0 && <span className="flex items-center gap-1"><Play className="h-4 w-4" /> {totalDuration} Hours</span>}
            {questions.length > 0 && <span className="flex items-center gap-1"><HelpCircle className="h-4 w-4" /> {questions.length} Questions</span>}
            <StatusBadge status={contentStatus?.status || "pending"} />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">{course.course_name}</h1>
          <p className="text-lg text-muted-foreground">{course.course_description}</p>
        </div>

        {/* Content Generation CTA if no content */}
        {isPending && !hasContent && (
          <Card className="mb-8 border-dashed border-2 border-primary/30 bg-primary/5">
            <CardContent className="p-6 text-center">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-primary/60" />
              <h3 className="text-xl font-semibold mb-2">Content Not Yet Generated</h3>
              <p className="text-muted-foreground mb-4">
                This course needs AI-generated content including summary, MCQ questions, and module scripts.
              </p>
              <Button onClick={generateContent} disabled={generating} data-testid="generate-content-btn">
                {generating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Generate Content
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Generating Status */}
        {isGenerating && (
          <Card className="mb-8 border-yellow-500/50 bg-yellow-500/5">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-yellow-500" />
                <div className="flex-1">
                  <h3 className="font-semibold">Generating Content...</h3>
                  <p className="text-sm text-muted-foreground">AI is creating summary, {questions.length > 0 ? questions.length : "200"} MCQs, and module scripts</p>
                </div>
                <Button variant="outline" size="sm" onClick={fetchAllData}>
                  <RefreshCw className="h-4 w-4 mr-2" /> Refresh
                </Button>
              </div>
              <Progress className="mt-4" value={33} />
            </CardContent>
          </Card>
        )}

        <Separator className="my-6" />

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-4 w-full max-w-xl">
            <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
            <TabsTrigger value="modules" data-testid="tab-modules">Modules</TabsTrigger>
            <TabsTrigger value="quiz" data-testid="tab-quiz" disabled={questions.length === 0}>
              Quiz {questions.length > 0 && `(${questions.length})`}
            </TabsTrigger>
            <TabsTrigger value="scripts" data-testid="tab-scripts" disabled={scripts.length === 0}>
              Scripts
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Course Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  Course Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                {content?.summary ? (
                  <div className="prose dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap">{content.summary}</div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="h-10 w-10 mx-auto mb-3 opacity-50" />
                    <p>{isGenerating ? "Summary being generated..." : "Course summary not yet available"}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Sources */}
            {content?.sources && content.sources.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Research Sources</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {content.sources.map((source, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 bg-secondary/50 rounded-lg">
                        <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">{idx + 1}</span>
                        <div>
                          <p className="font-medium">{source.topic}</p>
                          <p className="text-sm text-muted-foreground">{source.concepts?.join(", ")}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* AI Assistant CTA */}
            <Card className="bg-primary/5 border-primary/20 cursor-pointer hover:bg-primary/10 transition-colors" onClick={() => setChatOpen(true)} data-testid="ai-assistant-cta">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="p-3 rounded-xl bg-primary/10">
                  <MessageSquare className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Need help understanding this course?</h3>
                  <p className="text-sm text-muted-foreground">Ask our AI Study Assistant</p>
                </div>
                <Button data-testid="ask-ai-btn">Ask AI</Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Modules Tab */}
          <TabsContent value="modules">
            <Card data-testid="modules-section">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ListOrdered className="h-5 w-5 text-primary" />
                  Course Modules
                  <Badge variant="secondary">{modules.length} modules</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {modules.length > 0 ? (
                  <Accordion type="single" collapsible className="w-full">
                    {modules.map((module, index) => {
                      const moduleScript = scripts.find(s => s.module_id === module.module_id);
                      return (
                        <AccordionItem key={module.module_id} value={module.module_id} data-testid={`module-item-${index}`}>
                          <AccordionTrigger className="hover:no-underline">
                            <div className="flex items-center gap-4 text-left">
                              <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm">
                                {module.order || index + 1}
                              </span>
                              <div>
                                <div className="font-semibold flex items-center gap-2">
                                  {module.title}
                                  {moduleScript && <Badge variant="outline" className="text-xs"><Video className="h-3 w-3 mr-1" />Script</Badge>}
                                </div>
                                <div className="text-sm text-muted-foreground flex items-center gap-2 mt-1">
                                  {module.duration_hours && <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{module.duration_hours}h</span>}
                                  {module.topics?.length > 0 && <span>• {module.topics.length} topics</span>}
                                </div>
                              </div>
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="pl-12 space-y-4">
                              {module.description && <p className="text-muted-foreground">{module.description}</p>}
                              {module.topics?.length > 0 && (
                                <div>
                                  <h4 className="font-medium mb-2">Topics Covered:</h4>
                                  <ul className="space-y-2">
                                    {module.topics.map((topic, topicIdx) => (
                                      <li key={topicIdx} className="flex items-center gap-2 text-sm">
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
                      );
                    })}
                  </Accordion>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <ListOrdered className="h-10 w-10 mx-auto mb-3 opacity-50" />
                    <p>No modules available yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Quiz Tab */}
          <TabsContent value="quiz">
            {questions.length === 0 ? (
              <Card className="border-dashed border-2 border-primary/30 bg-primary/5">
                <CardContent className="p-6 text-center">
                  <HelpCircle className="h-12 w-12 mx-auto mb-4 text-primary/60" />
                  <h3 className="text-xl font-semibold mb-2">No Quiz Questions Yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Generate 200 MCQ questions with AI for this course
                  </p>
                  <Button onClick={generateMCQ} disabled={generatingMCQ} data-testid="generate-mcq-btn">
                    {generatingMCQ ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <HelpCircle className="h-4 w-4 mr-2" />}
                    Generate 200 MCQ Questions
                  </Button>
                </CardContent>
              </Card>
            ) : !quizMode ? (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <HelpCircle className="h-5 w-5 text-primary" />
                        Practice Quiz
                      </CardTitle>
                      <CardDescription>
                        Test your knowledge with {questions.length} multiple-choice questions
                      </CardDescription>
                    </div>
                    {questions.length < 200 && (
                      <Button variant="outline" onClick={generateMCQ} disabled={generatingMCQ} size="sm">
                        {generatingMCQ ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                        Generate More
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-4 bg-green-500/10 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{questions.filter(q => q.difficulty === "easy").length}</div>
                      <div className="text-sm text-muted-foreground">Easy</div>
                    </div>
                    <div className="p-4 bg-yellow-500/10 rounded-lg">
                      <div className="text-2xl font-bold text-yellow-600">{questions.filter(q => q.difficulty === "medium").length}</div>
                      <div className="text-sm text-muted-foreground">Medium</div>
                    </div>
                    <div className="p-4 bg-red-500/10 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">{questions.filter(q => q.difficulty === "hard").length}</div>
                      <div className="text-sm text-muted-foreground">Hard</div>
                    </div>
                  </div>
                  <Button onClick={startQuiz} className="w-full" size="lg" data-testid="start-quiz-btn">
                    <Play className="h-4 w-4 mr-2" /> Start Quiz
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card data-testid="quiz-active">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Question {currentQuestion + 1} of {questions.length}</CardTitle>
                      <CardDescription>Score: {score}/{answeredQuestions.length}</CardDescription>
                    </div>
                    <Badge variant={questions[currentQuestion]?.difficulty === "easy" ? "secondary" : questions[currentQuestion]?.difficulty === "hard" ? "destructive" : "default"}>
                      {questions[currentQuestion]?.difficulty}
                    </Badge>
                  </div>
                  <Progress value={(currentQuestion / questions.length) * 100} className="mt-2" />
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-lg font-medium">{questions[currentQuestion]?.question}</p>
                  
                  <div className="space-y-2">
                    {["A", "B", "C", "D"].map((option) => {
                      const optionKey = `option_${option.toLowerCase()}`;
                      const isSelected = selectedAnswer === option;
                      const isCorrect = questions[currentQuestion]?.correct_answer === option;
                      
                      let bgClass = "bg-secondary hover:bg-secondary/80";
                      if (showExplanation) {
                        if (isCorrect) bgClass = "bg-green-500/20 border-green-500";
                        else if (isSelected && !isCorrect) bgClass = "bg-red-500/20 border-red-500";
                      } else if (isSelected) {
                        bgClass = "bg-primary/20 border-primary";
                      }
                      
                      return (
                        <button
                          key={option}
                          onClick={() => selectAnswer(option)}
                          className={`w-full p-4 text-left rounded-lg border-2 transition-colors ${bgClass}`}
                          disabled={showExplanation}
                          data-testid={`option-${option}`}
                        >
                          <span className="font-semibold mr-2">{option}.</span>
                          {questions[currentQuestion]?.[optionKey]}
                          {showExplanation && isCorrect && <Check className="inline ml-2 h-4 w-4 text-green-500" />}
                          {showExplanation && isSelected && !isCorrect && <X className="inline ml-2 h-4 w-4 text-red-500" />}
                        </button>
                      );
                    })}
                  </div>
                  
                  {showExplanation && (
                    <Card className="bg-blue-500/10 border-blue-500/30">
                      <CardContent className="p-4">
                        <p className="font-medium mb-1">Explanation:</p>
                        <p className="text-sm">{questions[currentQuestion]?.explanation}</p>
                      </CardContent>
                    </Card>
                  )}
                  
                  <div className="flex gap-4">
                    {!showExplanation ? (
                      <Button onClick={submitAnswer} disabled={!selectedAnswer} className="flex-1" data-testid="submit-answer-btn">
                        Submit Answer
                      </Button>
                    ) : (
                      <Button onClick={nextQuestion} className="flex-1" data-testid="next-question-btn">
                        {currentQuestion < questions.length - 1 ? "Next Question" : "Finish Quiz"}
                      </Button>
                    )}
                    <Button variant="outline" onClick={() => setQuizMode(false)}>Exit Quiz</Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Scripts Tab */}
          <TabsContent value="scripts">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Video className="h-5 w-5 text-primary" />
                      Module Scripts & Videos
                    </CardTitle>
                    <CardDescription>
                      Avatar video scripts for each module (~12 minutes each)
                    </CardDescription>
                  </div>
                  <Button 
                    onClick={generateVideos} 
                    disabled={generatingVideos || scripts.length === 0}
                    data-testid="generate-videos-btn"
                  >
                    {generatingVideos ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Video className="h-4 w-4 mr-2" />}
                    Generate Videos
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px]">
                  <div className="space-y-6">
                    {scripts.map((script, idx) => {
                      const module = modules.find(m => m.module_id === script.module_id);
                      const video = videos.find(v => v.module_id === script.module_id);
                      return (
                        <Card key={script.script_id} className="border-border/50">
                          <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                              <CardTitle className="text-lg">{module?.title || `Module ${idx + 1}`}</CardTitle>
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Clock className="h-4 w-4" />
                                ~{script.estimated_duration_minutes} min
                                <span className="mx-2">|</span>
                                {script.word_count} words
                                {video && (
                                  <>
                                    <span className="mx-2">|</span>
                                    <Badge variant="outline" className="text-green-600 border-green-600">
                                      <Video className="h-3 w-3 mr-1" /> Video Ready
                                    </Badge>
                                  </>
                                )}
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {video && (
                              <div className="bg-black rounded-lg overflow-hidden aspect-video">
                                <video 
                                  controls 
                                  className="w-full h-full"
                                  src={`${API}/videos/${script.module_id}/file`}
                                >
                                  Your browser does not support the video tag.
                                </video>
                              </div>
                            )}
                            <details className="group">
                              <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground flex items-center gap-2">
                                <FileText className="h-4 w-4" />
                                View Script Text
                              </summary>
                              <div className="mt-2 bg-secondary/50 rounded-lg p-4 max-h-[300px] overflow-y-auto">
                                <pre className="whitespace-pre-wrap text-sm font-mono">{script.script_text}</pre>
                              </div>
                            </details>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Chat Widget */}
      <ChatWidget isOpen={chatOpen} onToggle={() => setChatOpen(!chatOpen)} courseId={courseId} courseName={course?.course_name} />
    </div>
  );
}
