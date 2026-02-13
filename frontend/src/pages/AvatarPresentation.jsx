import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Play, Users, Clock, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AvatarPresentation() {
  const { moduleId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [module, setModule] = useState(null);
  const [presentationReady, setPresentationReady] = useState(false);

  useEffect(() => {
    const checkPresentation = async () => {
      try {
        // Check if presentation exists
        const response = await fetch(`${API}/presentations-50-50/${moduleId}`, { method: 'HEAD' });
        setPresentationReady(response.ok);
        
        // Get module info
        const moduleRes = await fetch(`${API}/modules/${moduleId}`);
        if (moduleRes.ok) {
          const data = await moduleRes.json();
          setModule(data);
        }
      } catch (err) {
        console.error("Error checking presentation:", err);
      } finally {
        setLoading(false);
      }
    };
    
    checkPresentation();
  }, [moduleId]);

  const openPresentation = () => {
    window.open(`${API}/presentations-50-50/${moduleId}`, '_blank');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-cyan-400">
          <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          <span>טוען מצגת...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-white/5 backdrop-blur-xl bg-slate-950/50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Button 
              variant="ghost" 
              onClick={() => navigate(-1)}
              className="text-slate-400 hover:text-white"
              data-testid="back-btn"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              חזרה
            </Button>
            
            <div className="flex items-center gap-2 text-cyan-400">
              <Users className="w-5 h-5" />
              <span className="text-sm">מצגת עם מרצה וירטואלי</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-20">
        <div className="text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 mb-8">
            <BookOpen className="w-4 h-4" />
            <span className="text-sm">מצגת אינטראקטיבית</span>
          </div>

          {/* Module Info */}
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {module?.title || moduleId}
          </h1>
          <p className="text-xl text-slate-400 mb-12">
            {module?.courseName || "קורס אקדמי"}
          </p>

          {/* Preview Card */}
          <div className="relative bg-slate-800/50 rounded-3xl border border-white/5 overflow-hidden mb-12">
            <div className="aspect-video relative">
              {/* Preview Image - 50/50 Layout */}
              <div className="absolute inset-0 flex">
                {/* Left - Avatar Side */}
                <div className="w-1/2 bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-400 to-purple-500 mx-auto mb-4 flex items-center justify-center">
                      <Users className="w-12 h-12 text-white" />
                    </div>
                    <p className="text-slate-400 text-sm">מרצה וירטואלי</p>
                  </div>
                </div>
                
                {/* Right - Slides Side */}
                <div className="w-1/2 bg-slate-900/80 flex items-center justify-center border-l border-white/5">
                  <div className="text-center">
                    <BookOpen className="w-16 h-16 text-cyan-400/50 mx-auto mb-4" />
                    <p className="text-slate-400 text-sm">שקופיות עם איורים</p>
                  </div>
                </div>
              </div>

              {/* Play Overlay */}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer" onClick={openPresentation}>
                <div className="w-20 h-20 rounded-full bg-gradient-to-r from-cyan-400 to-purple-500 flex items-center justify-center">
                  <Play className="w-10 h-10 text-white ml-1" />
                </div>
              </div>
            </div>
          </div>

          {/* CTA Button */}
          {presentationReady ? (
            <Button
              size="lg"
              className="px-12 py-6 text-lg bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-white rounded-full shadow-lg shadow-cyan-500/25"
              onClick={openPresentation}
              data-testid="start-presentation-btn"
            >
              <Play className="w-6 h-6 mr-3" />
              התחל מצגת
            </Button>
          ) : (
            <div className="text-slate-400">
              <p>המצגת עדיין לא מוכנה</p>
              <p className="text-sm mt-2">נסה שוב בעוד כמה דקות</p>
            </div>
          )}

          {/* Features */}
          <div className="grid grid-cols-3 gap-6 mt-16 text-center">
            <div className="p-6 rounded-2xl bg-slate-800/30 border border-white/5">
              <Users className="w-8 h-8 text-cyan-400 mx-auto mb-3" />
              <h3 className="text-white font-medium mb-1">אווטאר מדבר</h3>
              <p className="text-slate-400 text-sm">מרצה וירטואלי עם תנועות שפתיים</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-800/30 border border-white/5">
              <BookOpen className="w-8 h-8 text-purple-400 mx-auto mb-3" />
              <h3 className="text-white font-medium mb-1">שקופיות אינטראקטיביות</h3>
              <p className="text-slate-400 text-sm">איורים ותכנים מותאמים</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-800/30 border border-white/5">
              <Clock className="w-8 h-8 text-green-400 mx-auto mb-3" />
              <h3 className="text-white font-medium mb-1">סנכרון מלא</h3>
              <p className="text-slate-400 text-sm">אודיו ושקופיות מסונכרנים</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
