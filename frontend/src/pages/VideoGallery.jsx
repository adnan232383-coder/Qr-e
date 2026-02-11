import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
  CheckCircle
} from "lucide-react";

// Course modules data
const COURSE_MODULES = [
  {
    id: 'module1',
    title: 'Introduction to Cell Biology',
    description: 'Overview of cell theory, cell types, and basic cellular organization',
    duration: '1:15',
    topics: ['Cell Theory', 'Prokaryotic vs Eukaryotic Cells', 'Cell Size and Scale'],
    videoFile: 'module1_video.mp4',
    hasSubtitles: ['he']
  },
  {
    id: 'module2',
    title: 'Cell Membrane and Transport',
    description: 'Structure of plasma membrane and mechanisms of cellular transport',
    duration: '1:18',
    topics: ['Phospholipid Bilayer', 'Membrane Proteins', 'Passive Transport', 'Active Transport'],
    videoFile: 'module2_video.mp4',
    hasSubtitles: ['he']
  },
  {
    id: 'module3',
    title: 'Cellular Organelles',
    description: 'Structure and function of major cellular organelles',
    duration: '1:19',
    topics: ['Nucleus', 'Mitochondria', 'Endoplasmic Reticulum', 'Golgi Apparatus', 'Lysosomes'],
    videoFile: 'module3_video.mp4',
    hasSubtitles: ['he']
  },
  {
    id: 'module4',
    title: 'Cellular Respiration and ATP',
    description: 'Energy production in cells through aerobic and anaerobic respiration',
    duration: '1:25',
    topics: ['Glycolysis', 'Krebs Cycle', 'Electron Transport Chain', 'ATP Synthesis'],
    videoFile: 'module4_video.mp4',
    hasSubtitles: []
  },
  {
    id: 'module5',
    title: 'Cell Cycle and Division',
    description: 'Phases of cell cycle, mitosis, and cell division regulation',
    duration: '1:23',
    topics: ['Interphase', 'Mitosis Stages', 'Cytokinesis', 'Cell Cycle Checkpoints'],
    videoFile: 'module5_video.mp4',
    hasSubtitles: []
  },
  {
    id: 'module6',
    title: 'DNA Structure and Replication',
    description: 'Molecular structure of DNA and the process of DNA replication',
    duration: '1:25',
    topics: ['DNA Double Helix', 'Nucleotides', 'Replication Fork', 'DNA Polymerase'],
    videoFile: 'module6_video.mp4',
    hasSubtitles: []
  },
  {
    id: 'module7',
    title: 'Gene Expression: Transcription and Translation',
    description: 'How genetic information flows from DNA to protein',
    duration: '1:26',
    topics: ['Transcription', 'mRNA Processing', 'Translation', 'Ribosomes', 'Genetic Code'],
    videoFile: 'module7_video.mp4',
    hasSubtitles: []
  },
  {
    id: 'module8',
    title: 'Basic Genetics and Inheritance',
    description: 'Mendelian genetics and patterns of inheritance',
    duration: '1:29',
    topics: ['Mendels Laws', 'Dominant and Recessive Alleles', 'Punnett Squares', 'Genetic Disorders'],
    videoFile: 'module8_video.mp4',
    hasSubtitles: []
  }
];

export default function VideoGallery() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [selectedModule, setSelectedModule] = useState(COURSE_MODULES[0]);
  const [completedModules, setCompletedModules] = useState([]);

  const markAsComplete = (moduleId) => {
    if (!completedModules.includes(moduleId)) {
      setCompletedModules([...completedModules, moduleId]);
    }
  };

  return (
    <div className="min-h-screen bg-background" data-testid="video-gallery-page">
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
                <span className="text-xl font-semibold hidden sm:inline">Course Videos</span>
              </div>
            </div>
            
            <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
              {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Course Header */}
        <div className="mb-8">
          <Badge className="mb-2">UG_DENT_Y1_S1_C01</Badge>
          <h1 className="text-3xl font-bold mb-2">General Biology</h1>
          <p className="text-muted-foreground">
            Foundations of cell biology and basic genetics for health sciences
          </p>
          <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <BookOpen className="h-4 w-4" /> 8 Modules
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" /> ~11 minutes
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4" /> {completedModules.length}/8 Complete
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Video Player */}
          <div className="lg:col-span-2 space-y-4">
            <VideoPlayer
              videoSrc={`/videos/${selectedModule.videoFile}`}
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
                    <p className="text-muted-foreground mt-1">{selectedModule.description}</p>
                  </div>
                  <Button 
                    variant={completedModules.includes(selectedModule.id) ? "secondary" : "default"}
                    onClick={() => markAsComplete(selectedModule.id)}
                  >
                    {completedModules.includes(selectedModule.id) ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" /> Completed
                      </>
                    ) : (
                      'Mark Complete'
                    )}
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
                {selectedModule.hasSubtitles.length > 0 && (
                  <p className="text-sm text-muted-foreground mt-4">
                    📝 Subtitles available in: {selectedModule.hasSubtitles.includes('he') && '🇮🇱 Hebrew'}
                  </p>
                )}
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
                    {COURSE_MODULES.map((module, index) => {
                      const isSelected = selectedModule.id === module.id;
                      const isCompleted = completedModules.includes(module.id);
                      
                      return (
                        <button
                          key={module.id}
                          onClick={() => setSelectedModule(module)}
                          className={`w-full text-left p-3 rounded-lg transition-colors flex items-start gap-3 ${
                            isSelected 
                              ? 'bg-primary/10 border border-primary/30' 
                              : 'hover:bg-secondary/50'
                          }`}
                          data-testid={`module-btn-${index}`}
                        >
                          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                            isCompleted 
                              ? 'bg-green-500 text-white' 
                              : isSelected 
                                ? 'bg-primary text-white' 
                                : 'bg-secondary'
                          }`}>
                            {isCompleted ? <CheckCircle className="h-4 w-4" /> : index + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`font-medium truncate ${isSelected ? 'text-primary' : ''}`}>
                              {module.title}
                            </p>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                              <span className="flex items-center gap-1">
                                <Play className="h-3 w-3" /> {module.duration}
                              </span>
                              {module.hasSubtitles.length > 0 && (
                                <Badge variant="outline" className="text-xs px-1 py-0">
                                  CC
                                </Badge>
                              )}
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
