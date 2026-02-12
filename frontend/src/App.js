import { useEffect, useState, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import CourseCatalog from "@/pages/CourseCatalog";
import CourseDetail from "@/pages/CourseDetail";
import Login from "@/pages/Login";
import AuthCallback from "@/pages/AuthCallback";
import GenerationProgress from "@/pages/GenerationProgress";
import UniversityCatalog from "@/pages/UniversityCatalog";
import VideoGallery from "@/pages/VideoGallery";
import StyleDemos from "@/pages/StyleDemos";
import CourseViewer from "@/pages/CourseViewer";
import StatsDashboard from "@/pages/StatsDashboard";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// App Router with session_id detection
function AppRouter() {
  const location = useLocation();
  
  // CRITICAL: Detect session_id synchronously during render
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }
  
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/catalog/:majorId" element={<CourseCatalog />} />
      <Route path="/university/:universityId" element={<UniversityCatalog />} />
      <Route path="/course/:courseId" element={<CourseDetail />} />
      <Route path="/videos" element={<VideoGallery />} />
      <Route path="/videos/:courseId" element={<CourseViewer />} />
      <Route path="/styles" element={<StyleDemos />} />
      <Route path="/admin/progress" element={<GenerationProgress />} />
      <Route path="/admin/stats" element={<StatsDashboard />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRouter />
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
