import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTheme } from "@/context/ThemeContext";
import VideoPlayer from "@/components/VideoPlayer";
import { 
  GraduationCap, 
  Sun, 
  Moon, 
  ArrowLeft,
  Play,
  Clock,
  BookOpen,
  CheckCircle,
  Sparkles
} from "lucide-react";

// All courses data
const COURSES = {
  "UG_DENT_Y1_S1_C01": {
    id: "UG_DENT_Y1_S1_C01",
    name: "General Biology",
    description: "Foundations of cell biology and basic genetics for health sciences",
    videoDir: "diverse",
    modules: [
      { id: 'module1', title: 'Introduction to Cell Biology', topics: ['Cell Theory', 'Prokaryotic vs Eukaryotic'], style: { name: 'Medical Dark', color: '#1a1a2e' } },
      { id: 'module2', title: 'Cell Membrane and Transport', topics: ['Phospholipid Bilayer', 'Passive Transport'], style: { name: 'Medical Dark', color: '#1a1a2e' } },
      { id: 'module3', title: 'Cellular Organelles', topics: ['Nucleus', 'Mitochondria', 'ER'], style: { name: 'Office Light', color: '#f5f5f5' } },
      { id: 'module4', title: 'Cellular Respiration and ATP', topics: ['Glycolysis', 'Krebs Cycle'], style: { name: 'Office Light', color: '#f5f5f5' } },
      { id: 'module5', title: 'Cell Cycle and Division', topics: ['Interphase', 'Mitosis'], style: { name: 'Studio Dark', color: '#263238' } },
      { id: 'module6', title: 'DNA Structure and Replication', topics: ['Double Helix', 'DNA Polymerase'], style: { name: 'Studio Dark', color: '#263238' } },
      { id: 'module7', title: 'Gene Expression', topics: ['Transcription', 'Translation'], style: { name: 'Business Modern', color: '#1e3a5f' } },
      { id: 'module8', title: 'Basic Genetics and Inheritance', topics: ['Mendels Laws', 'Punnett Squares'], style: { name: 'Business Modern', color: '#1e3a5f' } },
    ]
  },
  "UG_PHARM_Y1_S1_C01": {
    id: "UG_PHARM_Y1_S1_C01",
    name: "General Chemistry",
    description: "Foundational chemistry concepts for pharmacy students",
    videoDir: "UG_PHARM_Y1_S1_C01",
    modules: [
      { id: 'module1', title: 'Introduction to Chemistry', topics: ['Atomic Structure', 'Periodic Table'], style: { name: 'Medical Dark', color: '#1a1a2e' } },
      { id: 'module2', title: 'Chemical Bonding', topics: ['Ionic Bonds', 'Covalent Bonds'], style: { name: 'Medical Dark', color: '#1a1a2e' } },
      { id: 'module3', title: 'Solutions and Concentrations', topics: ['Molarity', 'Dilutions'], style: { name: 'Office Light', color: '#f5f5f5' } },
      { id: 'module4', title: 'Acids, Bases and pH', topics: ['Buffer Systems', 'pH Scale'], style: { name: 'Office Light', color: '#f5f5f5' } },
      { id: 'module5', title: 'Thermodynamics', topics: ['Energy Transfer', 'Enthalpy'], style: { name: 'Studio Dark', color: '#263238' } },
      { id: 'module6', title: 'Reaction Kinetics', topics: ['Reaction Rates', 'Equilibrium'], style: { name: 'Studio Dark', color: '#263238' } },
      { id: 'module7', title: 'Organic Chemistry Basics', topics: ['Functional Groups', 'Nomenclature'], style: { name: 'Business Modern', color: '#1e3a5f' } },
      { id: 'module8', title: 'Pharmaceutical Chemistry', topics: ['Drug Structures', 'Stereochemistry'], style: { name: 'Business Modern', color: '#1e3a5f' } },
    ]
  }
};

export default function CourseViewer() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  
  const course = COURSES[courseId] || COURSES["UG_DENT_Y1_S1_C01"];
  const [selectedModule, setSelectedModule] = useState(course.modules[0]);
  const [completedModules, setCompletedModules] = useState([]);
  const [videoAvailability, setVideoAvailability] = useState({});

  // Check video availability
  useEffect(() => {
    const checkVideos = async () => {
      const availability = {};
      for (const module of course.modules) {
        try {
          const response = await fetch(`/videos/${course.videoDir}/${module.id}_diverse.mp4`, { method: 'HEAD' });
          availability[module.id] = response.ok;
        } catch {
          availability[module.id] = false;
        }
      }
      setVideoAvailability(availability);
    };
    checkVideos();
  }, [course]);

  const getVideoSrc = (module) => {
    if (videoAvailability[module.id]) {
      return `/videos/${course.videoDir}/${module.id}_diverse.mp4`;
    }
    // Fallback to main course videos or show placeholder
    return `/videos/${course.videoDir}/${module.id}.mp4`;
  };

  const markAsComplete = (moduleId) => {
    if (!completedModules.includes(moduleId)) {
      setCompletedModules([...completedModules, moduleId]);
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="course-viewer-page">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate("/courses")} className="rounded-full">
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3">
                <GraduationCap className="h-8 w-8 text-primary" />
                <span className="text-xl font-semibold hidden sm:inline">Course Videos</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => navigate("/styles")}>
                <Sparkles className="h-4 w-4 mr-2" />
                סגנונות
              </Button>
              <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
                {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Course Header */}
        <div className="mb-8">
          <Badge className="mb-2">{course.id}</Badge>
          <h1 className="text-3xl font-bold mb-2">{course.name}</h1>
          <p className="text-muted-foreground">{course.description}</p>
          <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <BookOpen className="h-4 w-4" /> {course.modules.length} Modules
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4" /> {completedModules.length}/{course.modules.length} Complete
            </span>
            <Badge variant="secondary" className="flex items-center gap-1">
              <Sparkles className="h-3 w-3" /> Diverse Styles
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Video Player */}
          <div className="lg:col-span-2 space-y-4">
            <VideoPlayer
              videoSrc={getVideoSrc(selectedModule)}
              moduleId={selectedModule.id}
              title={selectedModule.title}
              subtitleBasePath="/videos/subtitles"
            />
            
            {/* Module Details */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{selectedModule.title}</CardTitle>
                  </div>
                  <Button 
                    variant={completedModules.includes(selectedModule.id) ? "secondary" : "default"}
                    onClick={() => markAsComplete(selectedModule.id)}
                  >
                    {completedModules.includes(selectedModule.id) ? (
                      <><CheckCircle className="h-4 w-4 mr-2" /> Completed</>
                    ) : 'Mark Complete'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <h4 className="font-medium mb-2">Topics Covered:</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedModule.topics.map((topic, idx) => (
                    <Badge key={idx} variant="outline">{topic}</Badge>
                  ))}
                </div>
                
                <div className="mt-4 p-3 rounded-lg bg-secondary/30 flex items-center gap-3">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: selectedModule.style.color }} />
                  <div className="text-sm">
                    <span className="font-medium">{selectedModule.style.name}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Module List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Course Modules</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[600px]">
                  <div className="space-y-1 p-4">
                    {course.modules.map((module, index) => {
                      const isSelected = selectedModule.id === module.id;
                      const isCompleted = completedModules.includes(module.id);
                      
                      return (
                        <button
                          key={module.id}
                          onClick={() => setSelectedModule(module)}
                          className={`w-full text-left p-3 rounded-lg transition-colors flex items-start gap-3 ${
                            isSelected ? 'bg-primary/10 border border-primary/30' : 'hover:bg-secondary/50'
                          }`}
                          data-testid={`module-btn-${index}`}
                        >
                          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                            isCompleted ? 'bg-green-500 text-white' : isSelected ? 'bg-primary text-white' : 'bg-secondary'
                          }`}>
                            {isCompleted ? <CheckCircle className="h-4 w-4" /> : index + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className={`font-medium truncate ${isSelected ? 'text-primary' : ''}`}>
                                {module.title}
                              </p>
                              <Sparkles className="h-3 w-3 text-primary flex-shrink-0" />
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: module.style.color }} />
                              <span className="truncate">{module.style.name}</span>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
