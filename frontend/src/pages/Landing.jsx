import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
  Heart
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Landing() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, login, isAuthenticated } = useAuth();
  const [universities, setUniversities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUniversities();
    seedDatabase();
  }, []);

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

  const getUniversityIcon = (name) => {
    if (name.toLowerCase().includes("georgia")) return Building2;
    if (name.toLowerCase().includes("vision")) return Heart;
    return GraduationCap;
  };

  const getUniversityColor = (id) => {
    if (id === "UG_TBILISI") return "from-sky-500/20 to-blue-500/10";
    if (id === "NVU") return "from-emerald-500/20 to-teal-500/10";
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
              <div className="text-3xl font-bold text-primary">160+</div>
              <div className="text-sm text-muted-foreground mt-1">Courses</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="text-3xl font-bold text-primary">2</div>
              <div className="text-sm text-muted-foreground mt-1">Universities</div>
            </div>
            <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <div className="text-3xl font-bold text-primary">15K+</div>
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
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto stagger-children">
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
                  <CardContent className="p-8">
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-xl bg-background text-primary">
                        <Icon className="h-8 w-8" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-2xl font-bold mb-2">{uni.name}</h3>
                        <p className="text-muted-foreground mb-2">
                          {uni.city}, {uni.country}
                        </p>
                        <p className="text-sm text-muted-foreground mb-4">
                          {uni.description?.substring(0, 100)}...
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
                  <MessageSquare className="h-6 w-6 text-accent-foreground" />
                </div>
                <h3 className="text-xl font-semibold mb-2">AI Study Assistant</h3>
                <p className="text-muted-foreground">
                  Get instant help with course material using our GPT-powered chatbot
                </p>
              </CardContent>
            </Card>
            
            <Card className="border-border/50 card-hover">
              <CardContent className="p-6">
                <div className="p-3 rounded-xl bg-accent w-fit mb-4">
                  <Award className="h-6 w-6 text-accent-foreground" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Course Summaries</h3>
                <p className="text-muted-foreground">
                  Access comprehensive summaries for each course to aid your studies
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* University Info */}
      <section className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold mb-6">
                University of Georgia, Tbilisi
              </h2>
              <p className="text-muted-foreground mb-6 text-lg">
                International private university offering English-taught programs for international students, focused on health and applied sciences.
              </p>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Globe className="h-5 w-5 text-primary" />
                  <span>English-taught programs</span>
                </div>
                <div className="flex items-center gap-3">
                  <Users className="h-5 w-5 text-primary" />
                  <span>International student community</span>
                </div>
                <div className="flex items-center gap-3">
                  <Award className="h-5 w-5 text-primary" />
                  <span>Accredited medical education</span>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-video rounded-2xl overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1761405973526-c2ce51b8a9c5?crop=entropy&cs=srgb&fm=jpg&q=85"
                  alt="University of Georgia"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute -bottom-6 -left-6 bg-card p-4 rounded-xl shadow-lg border border-border">
                <div className="text-2xl font-bold text-primary">Tbilisi</div>
                <div className="text-sm text-muted-foreground">Georgia</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-border bg-secondary/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-primary" />
              <span className="font-medium">UG University Assistant</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Supporting students at University of Georgia, Tbilisi
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
