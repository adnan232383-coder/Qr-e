import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { 
  GraduationCap, 
  Sun, 
  Moon, 
  LogOut, 
  BookOpen, 
  ChevronRight,
  Stethoscope,
  Pill,
  MessageSquare,
  User
} from "lucide-react";
import ChatWidget from "@/components/ChatWidget";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, isLoading, logout, checkAuth } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [majors, setMajors] = useState([]);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    // If user data passed from AuthCallback, use it
    if (location.state?.user && !user) {
      checkAuth();
    }
  }, [location.state, user, checkAuth]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !location.state?.user) {
      navigate("/login");
    }
  }, [isAuthenticated, isLoading, navigate, location.state]);

  useEffect(() => {
    fetchMajors();
  }, []);

  const fetchMajors = async () => {
    try {
      const response = await fetch(`${API}/majors`);
      if (response.ok) {
        const data = await response.json();
        setMajors(data);
      }
    } catch (e) {
      console.error("Error fetching majors:", e);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const displayUser = user || location.state?.user;

  if (isLoading && !location.state?.user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  const getMajorIcon = (name) => {
    if (name.toLowerCase().includes("dent")) return Stethoscope;
    if (name.toLowerCase().includes("pharm")) return Pill;
    return BookOpen;
  };

  const getMajorColor = (name) => {
    if (name.toLowerCase().includes("dent")) return "text-sky-500 bg-sky-500/10";
    if (name.toLowerCase().includes("pharm")) return "text-emerald-500 bg-emerald-500/10";
    return "text-primary bg-primary/10";
  };

  return (
    <div className="min-h-screen bg-background" data-testid="dashboard-page">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div 
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => navigate("/")}
              data-testid="nav-logo"
            >
              <GraduationCap className="h-8 w-8 text-primary" />
              <span className="text-xl font-semibold">UG Assistant</span>
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
              
              {displayUser && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="flex items-center gap-2 h-10 px-2" data-testid="user-menu-btn">
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={displayUser.picture} alt={displayUser.name} />
                        <AvatarFallback>{displayUser.name?.charAt(0)}</AvatarFallback>
                      </Avatar>
                      <span className="hidden sm:inline">{displayUser.name?.split(' ')[0]}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <div className="px-2 py-1.5">
                      <p className="text-sm font-medium">{displayUser.name}</p>
                      <p className="text-xs text-muted-foreground">{displayUser.email}</p>
                    </div>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => navigate("/")} data-testid="menu-home">
                      <GraduationCap className="mr-2 h-4 w-4" />
                      Home
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} data-testid="menu-logout">
                      <LogOut className="mr-2 h-4 w-4" />
                      Sign Out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Welcome back, {displayUser?.name?.split(' ')[0]}!
          </h1>
          <p className="text-muted-foreground">
            Continue your learning journey at University of Georgia
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Card 
            className="cursor-pointer hover:border-primary/50 transition-colors card-hover"
            onClick={() => setChatOpen(true)}
            data-testid="quick-action-chat"
          >
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-primary/10">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold">AI Study Assistant</h3>
                <p className="text-sm text-muted-foreground">Ask questions about your courses</p>
              </div>
            </CardContent>
          </Card>

          <Card 
            className="cursor-pointer hover:border-primary/50 transition-colors card-hover"
            onClick={() => document.getElementById('programs')?.scrollIntoView({ behavior: 'smooth' })}
            data-testid="quick-action-catalog"
          >
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-accent">
                <BookOpen className="h-6 w-6 text-accent-foreground" />
              </div>
              <div>
                <h3 className="font-semibold">Course Catalog</h3>
                <p className="text-sm text-muted-foreground">Browse all available courses</p>
              </div>
            </CardContent>
          </Card>

          <Card 
            className="cursor-pointer hover:border-primary/50 transition-colors card-hover"
            data-testid="quick-action-profile"
          >
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 rounded-xl bg-secondary">
                <User className="h-6 w-6 text-secondary-foreground" />
              </div>
              <div>
                <h3 className="font-semibold">My Profile</h3>
                <p className="text-sm text-muted-foreground">View and edit your profile</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Programs Section */}
        <section id="programs">
          <h2 className="text-2xl font-bold mb-6">Your Programs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {majors.map((major) => {
              const Icon = getMajorIcon(major.name);
              const colorClass = getMajorColor(major.name);
              
              return (
                <Card
                  key={major.external_id}
                  className="group cursor-pointer overflow-hidden transition-all duration-300 hover:border-primary/50 card-hover"
                  onClick={() => navigate(`/catalog/${major.external_id}`)}
                  data-testid={`program-card-${major.external_id}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-xl ${colorClass}`}>
                          <Icon className="h-6 w-6" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold mb-1">{major.name}</h3>
                          <p className="text-muted-foreground">
                            {major.degree} • {major.years} Year Program
                          </p>
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                    
                    <div className="mt-6 flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <BookOpen className="h-4 w-4" />
                        <span>{major.years * 10} Courses</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span>•</span>
                        <span>{major.years * 2} Semesters</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>
      </main>

      {/* Chat Widget */}
      <ChatWidget isOpen={chatOpen} onToggle={() => setChatOpen(!chatOpen)} />
    </div>
  );
}
