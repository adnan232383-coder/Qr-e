import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/context/ThemeContext";
import { 
  GraduationCap, 
  Sun, 
  Moon, 
  ArrowLeft,
  HelpCircle,
  Video,
  FileText,
  Loader2,
  CheckCircle,
  RefreshCw,
  Play
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function GenerationProgress() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchProgress();
    const interval = setInterval(fetchProgress, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchProgress = async () => {
    try {
      const res = await fetch(`${API}/generation-progress`);
      if (res.ok) {
        setProgress(await res.json());
      }
    } catch (e) {
      console.error("Error fetching progress:", e);
    } finally {
      setLoading(false);
    }
  };

  const startMCQGeneration = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/content/generate-all-mcq?count_per_course=200`, {
        method: "POST"
      });
      if (res.ok) {
        toast.success("MCQ generation started for all courses!");
        fetchProgress();
      } else {
        toast.error("Failed to start generation");
      }
    } catch (e) {
      toast.error("Error starting generation");
    } finally {
      setGenerating(false);
    }
  };

  const startVideoGeneration = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/video/generate-all`, {
        method: "POST"
      });
      if (res.ok) {
        toast.success("Video generation started for all modules!");
        fetchProgress();
      } else {
        toast.error("Failed to start video generation");
      }
    } catch (e) {
      toast.error("Error starting video generation");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const mcqProgress = progress?.mcq ? (progress.mcq.total_questions / progress.mcq.target) * 100 : 0;
  const videoProgress = progress?.videos ? (progress.videos.completed / progress.videos.total_modules) * 100 : 0;
  const scriptProgress = progress?.scripts ? (progress.scripts.completed / progress.scripts.total_modules) * 100 : 0;

  return (
    <div className="min-h-screen bg-background" data-testid="generation-progress-page">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="rounded-full">
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")}>
                <GraduationCap className="h-8 w-8 text-primary" />
                <span className="text-xl font-semibold">UG Assistant</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
                {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
              <Button variant="outline" size="sm" onClick={fetchProgress}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Content Generation Progress</h1>
          <p className="text-muted-foreground">
            Monitor the progress of AI-generated content for all courses
          </p>
        </div>

        <div className="grid gap-6">
          {/* MCQ Progress */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <HelpCircle className="h-6 w-6 text-blue-500" />
                  </div>
                  <div>
                    <CardTitle>MCQ Questions</CardTitle>
                    <CardDescription>200 questions per course × 90 courses</CardDescription>
                  </div>
                </div>
                <Button 
                  onClick={startMCQGeneration} 
                  disabled={generating}
                  variant={mcqProgress >= 100 ? "outline" : "default"}
                >
                  {generating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                  {mcqProgress >= 100 ? "Regenerate" : "Start Generation"}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>{progress?.mcq?.total_questions?.toLocaleString() || 0} / {progress?.mcq?.target?.toLocaleString() || 18000} questions</span>
                <span className="font-medium">{mcqProgress.toFixed(1)}%</span>
              </div>
              <Progress value={mcqProgress} className="h-3" />
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  {progress?.mcq?.courses_with_200_mcq || 0} courses complete
                </span>
                <span>•</span>
                <span>{progress?.mcq?.total_courses || 90} total courses</span>
              </div>
            </CardContent>
          </Card>

          {/* Scripts Progress */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10">
                  <FileText className="h-6 w-6 text-purple-500" />
                </div>
                <div>
                  <CardTitle>Module Scripts</CardTitle>
                  <CardDescription>Avatar video scripts (~12 min each)</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>{progress?.scripts?.completed || 0} / {progress?.scripts?.total_modules || 270} scripts</span>
                <span className="font-medium">{scriptProgress.toFixed(1)}%</span>
              </div>
              <Progress value={scriptProgress} className="h-3" />
              {scriptProgress >= 100 && (
                <Badge variant="outline" className="text-green-600 border-green-600">
                  <CheckCircle className="h-3 w-3 mr-1" /> All scripts generated
                </Badge>
              )}
            </CardContent>
          </Card>

          {/* Videos Progress */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-red-500/10">
                    <Video className="h-6 w-6 text-red-500" />
                  </div>
                  <div>
                    <CardTitle>Avatar Videos</CardTitle>
                    <CardDescription>Generated using Sora 2</CardDescription>
                  </div>
                </div>
                <Button 
                  onClick={startVideoGeneration} 
                  disabled={generating || scriptProgress < 100}
                  variant="outline"
                >
                  {generating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Video className="h-4 w-4 mr-2" />}
                  Generate Videos
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>{progress?.videos?.completed || 0} / {progress?.videos?.total_modules || 270} videos</span>
                <span className="font-medium">{videoProgress.toFixed(1)}%</span>
              </div>
              <Progress value={videoProgress} className="h-3" />
              {videoProgress === 0 && scriptProgress >= 100 && (
                <p className="text-sm text-muted-foreground">
                  Click "Generate Videos" to start creating avatar videos from scripts
                </p>
              )}
            </CardContent>
          </Card>

          {/* Stats Summary */}
          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="p-6">
              <div className="grid grid-cols-3 gap-6 text-center">
                <div>
                  <div className="text-3xl font-bold text-primary">
                    {progress?.mcq?.total_questions?.toLocaleString() || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">MCQ Questions</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary">
                    {progress?.scripts?.completed || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Scripts</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary">
                    {progress?.videos?.completed || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Videos</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
