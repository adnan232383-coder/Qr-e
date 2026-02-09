import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, BookOpen, GraduationCap, CheckCircle2 } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function UniversityCatalog() {
  const { universityId } = useParams();
  const [university, setUniversity] = useState(null);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch university info
        const uniRes = await fetch(`${API}/universities`);
        if (uniRes.ok) {
          const unis = await uniRes.json();
          const uni = unis.find(u => u.external_id === universityId);
          setUniversity(uni);
        }

        // Fetch courses
        const coursesRes = await fetch(`${API}/courses/by-university/${universityId}`);
        if (coursesRes.ok) {
          setCourses(await coursesRes.json());
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [universityId]);

  // Group courses by program
  const coursesByProgram = courses.reduce((acc, course) => {
    const program = course.program || "General";
    if (!acc[program]) acc[program] = [];
    acc[program].push(course);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <h1 className="text-xl font-bold">{university?.name || universityId}</h1>
              <p className="text-sm text-muted-foreground">{university?.city}, {university?.country}</p>
            </div>
          </div>
          <Badge variant="outline">{courses.length} Courses</Badge>
        </div>
      </header>

      {/* Content */}
      <main className="container mx-auto px-4 py-8">
        {Object.entries(coursesByProgram).map(([program, programCourses]) => (
          <div key={program} className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <GraduationCap className="h-6 w-6 text-primary" />
              <h2 className="text-2xl font-bold">{program}</h2>
              <Badge variant="secondary">{programCourses.length} courses</Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {programCourses.map((course) => {
                const mcqProgress = Math.min((course.mcq_count || 0) / 200 * 100, 100);
                const isComplete = course.mcq_count >= 200;

                return (
                  <Link key={course.external_id} to={`/course/${course.external_id}`}>
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full" data-testid={`course-card-${course.external_id}`}>
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between">
                          <CardTitle className="text-lg">{course.course_name}</CardTitle>
                          {isComplete && (
                            <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                          )}
                        </div>
                        <CardDescription>
                          Year {course.year} • Semester {course.semester}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="flex items-center gap-1">
                              <BookOpen className="h-4 w-4" />
                              MCQ Questions
                            </span>
                            <span className="font-medium">{course.mcq_count || 0}/200</span>
                          </div>
                          <Progress value={mcqProgress} className="h-2" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </main>
    </div>
  );
}
