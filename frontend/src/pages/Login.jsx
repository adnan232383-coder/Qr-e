import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { GraduationCap, Sun, Moon } from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated, isLoading } = useAuth();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate("/dashboard");
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="login-split">
      {/* Left side - Login Form */}
      <div className="flex flex-col justify-center px-8 py-12 lg:px-16">
        <div className="mb-8 flex items-center justify-between">
          <div 
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => navigate("/")}
            data-testid="logo-link"
          >
            <GraduationCap className="h-8 w-8 text-primary" />
            <span className="text-xl font-semibold">UG Assistant</span>
          </div>
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

        <div className="max-w-md mx-auto w-full">
          <Card className="border-border/50">
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-2xl">Welcome Back</CardTitle>
              <CardDescription>
                Sign in to access your course catalog and AI study assistant
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <Button
                onClick={login}
                className="w-full h-12 rounded-full text-base"
                data-testid="google-login-btn"
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </Button>

              <p className="text-center text-sm text-muted-foreground mt-6">
                By signing in, you agree to our Terms of Service
              </p>
            </CardContent>
          </Card>

          <p className="text-center text-sm text-muted-foreground mt-8">
            Don't have an account?{" "}
            <button
              onClick={login}
              className="text-primary hover:underline font-medium"
              data-testid="signup-link"
            >
              Sign up for free
            </button>
          </p>
        </div>
      </div>

      {/* Right side - Image */}
      <div
        className="login-image-side"
        style={{
          backgroundImage: `url(https://images.unsplash.com/photo-1761405973526-c2ce51b8a9c5?crop=entropy&cs=srgb&fm=jpg&q=85)`,
        }}
      >
        <div className="login-image-overlay flex items-end p-12">
          <div className="text-white max-w-md">
            <blockquote className="text-2xl font-serif italic mb-4">
              "Education is the passport to the future, for tomorrow belongs to those who prepare for it today."
            </blockquote>
            <p className="text-white/80">— Malcolm X</p>
          </div>
        </div>
      </div>
    </div>
  );
}
