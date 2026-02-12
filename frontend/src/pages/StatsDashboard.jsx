import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useTheme } from "@/context/ThemeContext";
import {
  GraduationCap,
  BookOpen,
  FileQuestion,
  Download,
  RefreshCw,
  Sun,
  Moon,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Building2,
  Heart,
  Stethoscope,
  Globe,
  Award,
  TrendingUp,
  PieChart as PieChartIcon,
  BarChart3
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Chart colors
const COLORS = {
  complete: "#22c55e",    // green-500
  partial: "#eab308",     // yellow-500
  incomplete: "#ef4444",  // red-500
  primary: "#14b8a6",     // teal-500
  universities: ["#0ea5e9", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899"] // sky, emerald, violet, amber, pink
};

export default function StatsDashboard() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState(null);
  const [universities, setUniversities] = useState([]);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setRefreshing(true);
    try {
      // Use the optimized dashboard stats API
      const response = await fetch(`${API}/stats/dashboard`);
      if (response.ok) {
        const data = await response.json();
        setUniversities(data.universities);
        setStats(data);
      }
    } catch (e) {
      console.error("Error fetching stats:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const exportToCSV = () => {
    if (!stats) return;

    let csv = "University,Courses,Questions,300+ MCQ,200-299 MCQ,Under 200,Completion %\n";
    
    stats.universities.forEach(uni => {
      csv += `"${uni.name}",${uni.totalCourses},${uni.totalQuestions},${uni.coursesWith300},${uni.coursesWith200},${uni.coursesUnder200},${uni.completionRate.toFixed(1)}\n`;
    });

    csv += `\n"TOTAL",${stats.totals.totalCourses},${stats.totals.totalQuestions},${stats.totals.coursesWith300},${stats.totals.coursesWith200},${stats.totals.coursesUnder200},${stats.totals.overallCompletion.toFixed(1)}\n`;

    // Add detailed course list
    csv += "\n\nDetailed Course List\n";
    csv += "University,Course ID,Course Name,MCQ Count,Status\n";
    
    stats.universities.forEach(uni => {
      uni.courses.forEach(course => {
        const status = (course.mcq_count || 0) >= 300 ? "Complete" : 
                      (course.mcq_count || 0) >= 200 ? "Partial" : "Incomplete";
        csv += `"${uni.name}","${course.external_id}","${course.course_name}",${course.mcq_count || 0},${status}\n`;
      });
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `mcq_stats_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const getUniversityIcon = (name) => {
    if (name.toLowerCase().includes("georgia")) return Building2;
    if (name.toLowerCase().includes("vision")) return Heart;
    if (name.toLowerCase().includes("iași") || name.toLowerCase().includes("iasi")) return Stethoscope;
    if (name.toLowerCase().includes("amman") || name.toLowerCase().includes("aau")) return Globe;
    if (name.toLowerCase().includes("najah")) return Award;
    return GraduationCap;
  };

  const getStatusColor = (rate) => {
    if (rate >= 90) return "text-green-500";
    if (rate >= 70) return "text-yellow-500";
    return "text-red-500";
  };

  const getProgressColor = (rate) => {
    if (rate >= 90) return "bg-green-500";
    if (rate >= 70) return "bg-yellow-500";
    return "bg-red-500";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-50 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="icon" onClick={() => navigate("/")} data-testid="back-btn">
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <GraduationCap className="h-8 w-8 text-primary" />
              <span className="text-xl font-semibold">Content Statistics</span>
            </div>
            
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchStats}
                disabled={refreshing}
                data-testid="refresh-btn"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={exportToCSV}
                data-testid="export-btn"
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                data-testid="theme-toggle-btn"
                className="rounded-full"
              >
                {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card data-testid="total-universities-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Building2 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Universities</p>
                  <p className="text-2xl font-bold">{stats?.totals.totalUniversities}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card data-testid="total-courses-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <BookOpen className="h-5 w-5 text-blue-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Courses</p>
                  <p className="text-2xl font-bold">{stats?.totals.totalCourses}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card data-testid="total-questions-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-500/10">
                  <FileQuestion className="h-5 w-5 text-green-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total MCQs</p>
                  <p className="text-2xl font-bold">{stats?.totals.totalQuestions.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card data-testid="completion-rate-card">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10">
                  <TrendingUp className="h-5 w-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Completion</p>
                  <p className="text-2xl font-bold">{stats?.totals.overallCompletion.toFixed(1)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Overall Progress */}
        <Card className="mb-8" data-testid="overall-progress-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              Overall Content Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span>Courses with 300+ MCQs</span>
                <span className="font-medium text-green-500">
                  {stats?.totals.coursesWith300} / {stats?.totals.totalCourses}
                </span>
              </div>
              <Progress 
                value={stats?.totals.overallCompletion} 
                className="h-3"
              />
              <div className="grid grid-cols-3 gap-4 text-center text-sm">
                <div className="p-3 rounded-lg bg-green-500/10">
                  <p className="font-bold text-green-500">{stats?.totals.coursesWith300}</p>
                  <p className="text-muted-foreground">300+ MCQs</p>
                </div>
                <div className="p-3 rounded-lg bg-yellow-500/10">
                  <p className="font-bold text-yellow-500">{stats?.totals.coursesWith200}</p>
                  <p className="text-muted-foreground">200-299 MCQs</p>
                </div>
                <div className="p-3 rounded-lg bg-red-500/10">
                  <p className="font-bold text-red-500">{stats?.totals.coursesUnder200}</p>
                  <p className="text-muted-foreground">Under 200</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Pie Chart - Course Status Distribution */}
          <Card data-testid="pie-chart-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChartIcon className="h-5 w-5 text-primary" />
                Course Status Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: "300+ MCQs", value: stats?.totals.coursesWith300 || 0, color: COLORS.complete },
                        { name: "200-299 MCQs", value: stats?.totals.coursesWith200 || 0, color: COLORS.partial },
                        { name: "Under 200", value: stats?.totals.coursesUnder200 || 0, color: COLORS.incomplete }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={3}
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      labelLine={false}
                    >
                      {[COLORS.complete, COLORS.partial, COLORS.incomplete].map((color, index) => (
                        <Cell key={`cell-${index}`} fill={color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                        border: '1px solid #374151',
                        borderRadius: '8px'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-4 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.complete }}></div>
                  <span>Complete</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.partial }}></div>
                  <span>Partial</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.incomplete }}></div>
                  <span>Incomplete</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Bar Chart - Questions per University */}
          <Card data-testid="bar-chart-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                MCQ Questions by University
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={stats?.universities.map((uni, idx) => ({
                      name: uni.name.split(" ")[0], // Short name
                      fullName: uni.name,
                      questions: uni.totalQuestions,
                      courses: uni.totalCourses,
                      fill: COLORS.universities[idx % COLORS.universities.length]
                    })) || []}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis 
                      dataKey="name" 
                      tick={{ fontSize: 12 }}
                      stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                    />
                    <YAxis 
                      tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
                      stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                    />
                    <Tooltip
                      contentStyle={{ 
                        backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                        border: '1px solid #374151',
                        borderRadius: '8px'
                      }}
                      formatter={(value, name) => [value.toLocaleString(), name === 'questions' ? 'Questions' : name]}
                      labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                    />
                    <Bar dataKey="questions" radius={[4, 4, 0, 0]}>
                      {stats?.universities.map((_, idx) => (
                        <Cell key={`cell-${idx}`} fill={COLORS.universities[idx % COLORS.universities.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Completion Rate Bar Chart */}
        <Card className="mb-8" data-testid="completion-bar-chart-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Completion Rate by University
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={stats?.universities.map((uni, idx) => ({
                    name: uni.name.length > 20 ? uni.name.substring(0, 20) + "..." : uni.name,
                    fullName: uni.name,
                    completion: uni.completionRate,
                    courses300: uni.coursesWith300,
                    totalCourses: uni.totalCourses,
                    fill: COLORS.universities[idx % COLORS.universities.length]
                  })) || []}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis 
                    type="number" 
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                    stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                  />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    tick={{ fontSize: 11 }}
                    width={95}
                    stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: theme === 'dark' ? '#1f2937' : '#fff',
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                    formatter={(value, name, props) => [
                      `${value.toFixed(1)}% (${props.payload.courses300}/${props.payload.totalCourses} courses)`,
                      'Completion'
                    ]}
                    labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                  />
                  <Bar dataKey="completion" radius={[0, 4, 4, 0]}>
                    {stats?.universities.map((uni, idx) => (
                      <Cell 
                        key={`cell-${idx}`} 
                        fill={uni.completionRate >= 90 ? COLORS.complete : uni.completionRate >= 70 ? COLORS.partial : COLORS.incomplete} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* University Details */}
        <h2 className="text-xl font-bold mb-4">University Breakdown</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {stats?.universities.map((uni) => {
            const Icon = getUniversityIcon(uni.name);
            return (
              <Card 
                key={uni.external_id} 
                className="overflow-hidden"
                data-testid={`uni-card-${uni.external_id}`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{uni.name}</CardTitle>
                        <p className="text-sm text-muted-foreground">{uni.city}, {uni.country}</p>
                      </div>
                    </div>
                    <div className={`flex items-center gap-1 ${getStatusColor(uni.completionRate)}`}>
                      {uni.completionRate >= 90 ? (
                        <CheckCircle2 className="h-5 w-5" />
                      ) : (
                        <AlertCircle className="h-5 w-5" />
                      )}
                      <span className="font-bold">{uni.completionRate.toFixed(0)}%</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Progress bar */}
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">Progress</span>
                        <span>{uni.coursesWith300} / {uni.totalCourses} complete</span>
                      </div>
                      <div className="h-2 bg-secondary rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${getProgressColor(uni.completionRate)} transition-all`}
                          style={{ width: `${uni.completionRate}%` }}
                        />
                      </div>
                    </div>

                    {/* Stats grid */}
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="p-3 rounded-lg bg-secondary/50">
                        <p className="text-muted-foreground">Courses</p>
                        <p className="text-xl font-bold">{uni.totalCourses}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-secondary/50">
                        <p className="text-muted-foreground">Questions</p>
                        <p className="text-xl font-bold">{uni.totalQuestions.toLocaleString()}</p>
                      </div>
                    </div>

                    {/* Status breakdown */}
                    <div className="flex gap-2 text-xs">
                      <span className="px-2 py-1 rounded-full bg-green-500/10 text-green-500">
                        {uni.coursesWith300} complete
                      </span>
                      {uni.coursesWith200 > 0 && (
                        <span className="px-2 py-1 rounded-full bg-yellow-500/10 text-yellow-500">
                          {uni.coursesWith200} partial
                        </span>
                      )}
                      {uni.coursesUnder200 > 0 && (
                        <span className="px-2 py-1 rounded-full bg-red-500/10 text-red-500">
                          {uni.coursesUnder200} incomplete
                        </span>
                      )}
                    </div>

                    {/* View courses button */}
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={() => navigate(`/university/${uni.external_id}`)}
                      data-testid={`view-courses-${uni.external_id}`}
                    >
                      View Courses
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </main>
    </div>
  );
}
