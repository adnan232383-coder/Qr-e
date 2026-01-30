import { useEffect, useState, useCallback } from "react";
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
  Play,
  Square,
  AlertCircle,
  Clock,
  Activity
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const JobStatusBadge = ({ status }) => {
  const styles = {
    queued: "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
    running: "bg-blue-500/10 text-blue-600 border-blue-500/30",
    done: "bg-green-500/10 text-green-600 border-green-500/30",
    failed: "bg-red-500/10 text-red-600 border-red-500/30",
    cancelled: "bg-gray-500/10 text-gray-600 border-gray-500/30"
  };
  
  const icons = {
    queued: <Clock className="h-3 w-3" />,
    running: <Activity className="h-3 w-3 animate-pulse" />,
    done: <CheckCircle className="h-3 w-3" />,
    failed: <AlertCircle className="h-3 w-3" />,
    cancelled: <Square className="h-3 w-3" />
  };
  
  return (
    <Badge variant="outline" className={`${styles[status] || styles.queued} flex items-center gap-1`}>
      {icons[status]}
      {status?.toUpperCase()}
    </Badge>
  );
};

export default function GenerationProgress() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [progress, setProgress] = useState(null);
  const [mcqJobProgress, setMcqJobProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [activeJobs, setActiveJobs] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchProgress = useCallback(async () => {
    try {
      const [progressRes, mcqRes, jobsRes] = await Promise.all([
        fetch(`${API}/generation-progress`),
        fetch(`${API}/admin/mcq/progress`),
        fetch(`${API}/admin/jobs`)
      ]);
      
      if (progressRes.ok) {
        setProgress(await progressRes.json());
      }
      
      if (mcqRes.ok) {
        const mcqData = await mcqRes.json();
        setMcqJobProgress(mcqData);
      }
      
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        const running = jobsData.recent_jobs?.filter(j => j.status === 'running') || [];
        setActiveJobs(running);
      }
    } catch (e) {
      console.error("Error fetching progress:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProgress();
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchProgress, 5000); // Poll every 5 seconds
    }
    return () => clearInterval(interval);
  }, [fetchProgress, autoRefresh]);

  const startMCQGeneration = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/admin/mcq/start?questions_per_course=200`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        toast.success("MCQ generation started!", {
          description: `Job ID: ${data.job?.job_id?.substring(0, 12)}...`
        });
        setCurrentJob(data.job);
        fetchProgress();
      } else {
        const error = await res.json();
        toast.error("Failed to start generation", {
          description: error.detail || "Unknown error"
        });
      }
    } catch (e) {
      toast.error("Error starting generation", {
        description: e.message
      });
    } finally {
      setGenerating(false);
    }
  };

  const cancelJob = async (jobId) => {
    try {
      const res = await fetch(`${API}/admin/jobs/${jobId}/cancel`, {
        method: "POST"
      });
      if (res.ok) {
        toast.success("Job cancelled");
        setCurrentJob(null);
        fetchProgress();
      } else {
        const error = await res.json();
        toast.error("Failed to cancel job", {
          description: error.detail || "Unknown error"
        });
      }
    } catch (e) {
      toast.error("Error cancelling job");
    }
  };

  const startScriptGeneration = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API}/admin/scripts/start`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        toast.success("Script generation started!", {
          description: `Job ID: ${data.job?.job_id?.substring(0, 12)}...`
        });
        fetchProgress();
      } else {
        const error = await res.json();
        toast.error("Failed to start script generation", {
          description: error.detail || "Unknown error"
        });
      }
    } catch (e) {
      toast.error("Error starting script generation");
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

  const getJobProgress = (job) => {
    if (!job?.progress?.total) return 0;
    return (job.progress.completed / job.progress.total) * 100;
  };

  const getJobLabel = (jobType) => {
    const labels = {
      'bulk_mcq': 'MCQ Generation',
      'bulk_script': 'Script Generation',
      'bulk_video': 'Video Generation',
      'mcq_generation': 'MCQ (Single)',
      'script_generation': 'Script (Single)'
    };
    return labels[jobType] || jobType;
  };

  return (
    <div className="min-h-screen bg-background" data-testid="generation-progress-page">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="rounded-full" data-testid="back-button">
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")}>
                <GraduationCap className="h-8 w-8 text-primary" />
                <span className="text-xl font-semibold">UG Assistant</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <Button 
                variant={autoRefresh ? "default" : "outline"} 
                size="sm" 
                onClick={() => setAutoRefresh(!autoRefresh)}
                data-testid="auto-refresh-toggle"
              >
                <Activity className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-pulse' : ''}`} />
                {autoRefresh ? "Live" : "Paused"}
              </Button>
              <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
                {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
              <Button variant="outline" size="sm" onClick={fetchProgress} data-testid="refresh-button">
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
            Monitor and control AI-generated content for all courses
          </p>
        </div>

        <div className="grid gap-6">
          {/* Active Jobs Status - Show all running jobs */}
          {activeJobs.length > 0 && (
            <Card className="border-blue-500/30 bg-blue-500/5" data-testid="active-jobs-card">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/20">
                    <Activity className="h-6 w-6 text-blue-500 animate-pulse" />
                  </div>
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      Active Jobs
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-600">
                        {activeJobs.length} running
                      </Badge>
                    </CardTitle>
                    <CardDescription>
                      Content generation in progress
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {activeJobs.map((job) => (
                  <div key={job.job_id} className="p-4 rounded-lg bg-background/50 border space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <JobStatusBadge status={job.status} />
                        <span className="font-medium">{getJobLabel(job.job_type)}</span>
                      </div>
                      <Button 
                        variant="destructive" 
                        size="sm" 
                        onClick={() => cancelJob(job.job_id)}
                      >
                        <Square className="h-3 w-3 mr-1" />
                        Cancel
                      </Button>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>{job.progress?.completed || 0} / {job.progress?.total || 0}</span>
                      <span className="font-medium">{getJobProgress(job).toFixed(1)}%</span>
                    </div>
                    <Progress value={getJobProgress(job)} className="h-2" />
                    <div className="text-xs text-muted-foreground truncate">
                      {job.progress?.current_item || `Job ID: ${job.job_id?.substring(0, 12)}...`}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* MCQ Progress */}
          <Card data-testid="mcq-progress-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <HelpCircle className="h-6 w-6 text-blue-500" />
                  </div>
                  <div>
                    <CardTitle>MCQ Questions</CardTitle>
                    <CardDescription>200 questions per course × {progress?.mcq?.total_courses || 90} courses</CardDescription>
                  </div>
                </div>
                <Button 
                  onClick={startMCQGeneration} 
                  disabled={generating || activeJobs.some(j => j.job_type === 'bulk_mcq')}
                  variant={mcqProgress >= 100 ? "outline" : "default"}
                  data-testid="start-mcq-button"
                >
                  {generating ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
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
          <Card data-testid="scripts-progress-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <FileText className="h-6 w-6 text-purple-500" />
                  </div>
                  <div>
                    <CardTitle>Module Scripts</CardTitle>
                    <CardDescription>Avatar video scripts (~12 min each)</CardDescription>
                  </div>
                </div>
                <Button 
                  onClick={startScriptGeneration} 
                  disabled={generating || (currentJob?.status === "running" && currentJob?.job_type?.includes("script"))}
                  variant={scriptProgress >= 100 ? "outline" : "default"}
                  data-testid="start-scripts-button"
                >
                  {generating ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  {scriptProgress >= 100 ? "Regenerate" : "Start Generation"}
                </Button>
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
          <Card data-testid="videos-progress-card">
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
                  data-testid="start-video-button"
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

          {/* Recent Jobs */}
          {mcqJobProgress?.recent_jobs?.length > 0 && (
            <Card data-testid="recent-jobs-card">
              <CardHeader>
                <CardTitle className="text-lg">Recent Jobs</CardTitle>
                <CardDescription>Last 10 generation jobs</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mcqJobProgress.recent_jobs.slice(0, 5).map((job) => (
                    <div 
                      key={job.job_id} 
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <JobStatusBadge status={job.status} />
                        <div>
                          <div className="text-sm font-medium">
                            {job.job_type === "bulk_mcq" ? "Bulk MCQ" : job.job_type}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {job.job_id?.substring(0, 12)}...
                          </div>
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="text-muted-foreground">
                          {job.progress?.completed || 0}/{job.progress?.total || 0}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {job.updated_at ? new Date(job.updated_at).toLocaleString() : ""}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Stats Summary */}
          <Card className="bg-primary/5 border-primary/20" data-testid="stats-summary-card">
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
