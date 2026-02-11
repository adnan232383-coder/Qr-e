import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/context/ThemeContext";
import VideoPlayer from "@/components/VideoPlayer";
import { 
  GraduationCap, 
  Sun, 
  Moon, 
  ArrowLeft,
  Play,
  Palette,
  User,
  Layout,
  Sparkles,
  CheckCircle
} from "lucide-react";

// Demo styles configuration
const STYLE_DEMOS = [
  {
    id: "style_side_dark",
    name: "אווטאר בצד + רקע כהה",
    nameEn: "Avatar Side + Dark Background",
    description: "האווטאר ממוקם בצד שמאל עם רקע כהה מקצועי - מותיר מקום לתוכן בצד ימין",
    avatar: "Adriana Nurse Front",
    background: "#1a1a2e",
    voice: "Hope (נקבה)",
    videoFile: "demos_new/demo_adriana_side_dark.mp4",
    tags: ["רקע כהה", "פרזנטציה", "מקצועי"]
  },
  {
    id: "style_abigail_light",
    name: "אווטאר משרדי + רקע בהיר",
    nameEn: "Office Avatar + Light Background",
    description: "אווטאר בסגנון משרדי מקצועי עם רקע בהיר ונקי",
    avatar: "Abigail Office Front",
    background: "#f5f5f5",
    voice: "Ivy (נקבה)",
    videoFile: "demos_new/demo_abigail_light.mp4",
    tags: ["רקע בהיר", "משרדי", "מודרני"]
  },
  {
    id: "style_adrian_studio",
    name: "אווטאר גברי + סטודיו",
    nameEn: "Male Avatar + Studio",
    description: "אווטאר גברי בחליפה עם רקע סטודיו מודרני",
    avatar: "Adrian Blue Suit",
    background: "#263238",
    voice: "Andrew (זכר)",
    videoFile: "demos_new/demo_adrian_studio.mp4",
    tags: ["גברי", "סטודיו", "מקצועי"]
  },
  // Existing demos from previous session
  {
    id: "demo_adriana_nurse",
    name: "אחות רפואית",
    nameEn: "Medical Nurse",
    description: "אווטאר בסגנון רפואי מקצועי - מתאים לתוכן בריאותי",
    avatar: "Adriana Nurse",
    background: "רפואי",
    voice: "Hope (נקבה)",
    videoFile: "demos/demo_adriana_nurse.mp4",
    tags: ["רפואי", "מקצועי", "נקבה"]
  },
  {
    id: "demo_abigail_office",
    name: "משרד מקצועי",
    nameEn: "Professional Office",
    description: "אווטאר בסביבת משרד מקצועית - מתאים להרצאות כלליות",
    avatar: "Abigail Office",
    background: "משרדי",
    voice: "Ivy (נקבה)",
    videoFile: "demos/demo_abigail_office.mp4",
    tags: ["משרדי", "עסקי", "נקבה"]
  },
  {
    id: "demo_amanda",
    name: "קז'ואל יומיומי",
    nameEn: "Casual Style",
    description: "אווטאר בסגנון יומיומי נינוח - מתאים לתוכן קליל",
    avatar: "Amanda Casual",
    background: "ביתי",
    voice: "Hope (נקבה)",
    videoFile: "demos/demo_amanda.mp4",
    tags: ["קז'ואל", "נינוח", "נקבה"]
  }
];

// Style rotation plan for courses
const STYLE_ROTATION_PLAN = [
  { modules: "1-2", style: "אווטאר נקבה (Adriana Nurse) + רקע כהה", icon: "👩‍⚕️" },
  { modules: "3-4", style: "אווטאר נקבה (Abigail Office) + רקע בהיר", icon: "👩‍💼" },
  { modules: "5-6", style: "אווטאר גברי (Adrian) + סטודיו", icon: "👨‍🏫" },
  { modules: "7-8", style: "אווטאר נקבה (Adriana Business) + רקע מודרני", icon: "👩‍🔬" },
];

export default function StyleDemos() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [selectedDemo, setSelectedDemo] = useState(null);
  const [videoExists, setVideoExists] = useState({});

  // Check which demo videos exist
  useEffect(() => {
    const checkVideos = async () => {
      const exists = {};
      for (const demo of STYLE_DEMOS) {
        try {
          const response = await fetch(`/videos/${demo.videoFile}`, { method: 'HEAD' });
          exists[demo.id] = response.ok;
        } catch {
          exists[demo.id] = false;
        }
      }
      setVideoExists(exists);
    };
    checkVideos();
  }, []);

  return (
    <div className="min-h-screen bg-background" data-testid="style-demos-page">
      {/* Navigation */}
      <nav className="glass sticky top-0 z-40 border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="rounded-full">
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate("/")}>
                <Palette className="h-8 w-8 text-primary" />
                <span className="text-xl font-semibold hidden sm:inline">סגנונות אווטאר</span>
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
        {/* Header */}
        <div className="text-center mb-12">
          <Badge className="mb-4" variant="secondary">
            <Sparkles className="h-3 w-3 mr-1" />
            גיוון ויזואלי
          </Badge>
          <h1 className="text-3xl md:text-4xl font-bold mb-4">סגנונות פרזנטציה מגוונים</h1>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            כל 2 סרטונים בקורס יוצגו בסגנון שונה - אווטארים שונים, רקעים שונים ופורמטים מגוונים
          </p>
        </div>

        {/* Style Rotation Plan */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layout className="h-5 w-5" />
              תוכנית רוטציית סגנונות
            </CardTitle>
            <CardDescription>
              כך יראו הסרטונים בכל קורס - גיוון אוטומטי כל 2 מודולים
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {STYLE_ROTATION_PLAN.map((plan, index) => (
                <div 
                  key={index}
                  className="p-4 rounded-lg bg-secondary/30 border border-border"
                >
                  <div className="text-2xl mb-2">{plan.icon}</div>
                  <div className="font-medium text-sm mb-1">מודולים {plan.modules}</div>
                  <div className="text-xs text-muted-foreground">{plan.style}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Demo Videos Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Play className="h-5 w-5" />
            דמואים לצפייה
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {STYLE_DEMOS.map((demo) => (
              <Card 
                key={demo.id}
                className={`cursor-pointer transition-all hover:shadow-lg ${
                  selectedDemo?.id === demo.id ? 'ring-2 ring-primary' : ''
                } ${!videoExists[demo.id] ? 'opacity-60' : ''}`}
                onClick={() => videoExists[demo.id] && setSelectedDemo(demo)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{demo.name}</CardTitle>
                    {videoExists[demo.id] ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <Badge variant="outline" className="text-xs">בהכנה</Badge>
                    )}
                  </div>
                  <CardDescription className="text-xs">{demo.nameEn}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-3">{demo.description}</p>
                  
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center gap-2">
                      <User className="h-3 w-3" />
                      <span>אווטאר: {demo.avatar}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Palette className="h-3 w-3" />
                      <span>רקע: {demo.background}</span>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-1 mt-3">
                    {demo.tags.map((tag, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Video Player */}
        {selectedDemo && videoExists[selectedDemo.id] && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>{selectedDemo.name}</CardTitle>
              <CardDescription>{selectedDemo.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <video 
                controls 
                className="w-full rounded-lg"
                src={`/videos/${selectedDemo.videoFile}`}
                data-testid="demo-video-player"
              >
                Your browser does not support the video tag.
              </video>
            </CardContent>
          </Card>
        )}

        {/* Summary Section */}
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="pt-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              סיכום יכולות הגיוון
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="p-3 rounded-lg bg-background">
                <div className="font-medium mb-1">👤 אווטארים</div>
                <p className="text-muted-foreground text-xs">
                  נקבה: Adriana, Abigail, Amanda
                  <br />
                  זכר: Adrian, Aditya, Albert
                </p>
              </div>
              <div className="p-3 rounded-lg bg-background">
                <div className="font-medium mb-1">🎨 רקעים</div>
                <p className="text-muted-foreground text-xs">
                  כהה מקצועי, בהיר משרדי, סטודיו, רפואי, כיתת לימוד
                </p>
              </div>
              <div className="p-3 rounded-lg bg-background">
                <div className="font-medium mb-1">🗣️ קולות</div>
                <p className="text-muted-foreground text-xs">
                  נקבה: Hope, Ivy, Allison
                  <br />
                  זכר: Andrew, John, Patrick
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
