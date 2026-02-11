import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Maximize, 
  Subtitles,
  Settings
} from "lucide-react";

const SUBTITLE_LANGUAGES = [
  { code: 'he', name: 'עברית', flag: '🇮🇱' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'ro', name: 'Română', flag: '🇷🇴' },
];

export default function VideoPlayer({ 
  videoSrc, 
  moduleId,
  title = "Video",
  subtitleBasePath = "/videos/subtitles"
}) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [subtitleLang, setSubtitleLang] = useState('off');
  const [availableSubtitles, setAvailableSubtitles] = useState([]);

  // Check which subtitle files exist
  useEffect(() => {
    const checkSubtitles = async () => {
      const available = [];
      for (const lang of SUBTITLE_LANGUAGES) {
        try {
          const response = await fetch(`${subtitleBasePath}/${moduleId}_${lang.code}.vtt`, { method: 'HEAD' });
          if (response.ok) {
            available.push(lang);
          }
        } catch (e) {
          // Subtitle not available
        }
      }
      setAvailableSubtitles(available);
    };
    
    if (moduleId) {
      checkSubtitles();
    }
  }, [moduleId, subtitleBasePath]);

  // Update subtitle track when language changes
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Remove existing tracks
    const tracks = video.querySelectorAll('track');
    tracks.forEach(track => track.remove());

    // Add new track if language selected
    if (subtitleLang !== 'off') {
      const track = document.createElement('track');
      track.kind = 'subtitles';
      track.label = SUBTITLE_LANGUAGES.find(l => l.code === subtitleLang)?.name || subtitleLang;
      track.srclang = subtitleLang;
      track.src = `${subtitleBasePath}/${moduleId}_${subtitleLang}.vtt`;
      track.default = true;
      video.appendChild(track);
      
      // Enable the track
      setTimeout(() => {
        if (video.textTracks[0]) {
          video.textTracks[0].mode = 'showing';
        }
      }, 100);
    }
  }, [subtitleLang, moduleId, subtitleBasePath]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime;
      const total = videoRef.current.duration;
      setCurrentTime(current);
      setProgress((current / total) * 100);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleProgressClick = (e) => {
    const progressBar = e.currentTarget;
    const clickPosition = e.nativeEvent.offsetX;
    const barWidth = progressBar.offsetWidth;
    const percentage = clickPosition / barWidth;
    
    if (videoRef.current) {
      videoRef.current.currentTime = percentage * videoRef.current.duration;
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div 
      className="relative bg-black rounded-lg overflow-hidden group"
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(isPlaying ? false : true)}
      data-testid="video-player"
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        src={videoSrc}
        className="w-full aspect-video"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onClick={togglePlay}
        crossOrigin="anonymous"
      />

      {/* Play/Pause Overlay */}
      {!isPlaying && (
        <div 
          className="absolute inset-0 flex items-center justify-center bg-black/30 cursor-pointer"
          onClick={togglePlay}
        >
          <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center shadow-lg hover:scale-110 transition-transform">
            <Play className="h-8 w-8 text-black ml-1" fill="black" />
          </div>
        </div>
      )}

      {/* Controls Bar */}
      <div 
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity ${
          showControls ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {/* Progress Bar */}
        <div 
          className="w-full h-1 bg-white/30 rounded-full mb-3 cursor-pointer group/progress"
          onClick={handleProgressClick}
        >
          <div 
            className="h-full bg-primary rounded-full relative"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover/progress:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Controls Row */}
        <div className="flex items-center justify-between">
          {/* Left Controls */}
          <div className="flex items-center gap-3">
            <button 
              onClick={togglePlay}
              className="text-white hover:text-primary transition-colors"
              data-testid="play-pause-btn"
            >
              {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
            </button>

            <button 
              onClick={toggleMute}
              className="text-white hover:text-primary transition-colors"
              data-testid="mute-btn"
            >
              {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
            </button>

            <span className="text-white text-sm font-mono">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          {/* Right Controls */}
          <div className="flex items-center gap-3">
            {/* Subtitle Selector */}
            <div className="flex items-center gap-2">
              <Subtitles className="h-4 w-4 text-white" />
              <Select value={subtitleLang} onValueChange={setSubtitleLang}>
                <SelectTrigger 
                  className="w-[130px] h-8 bg-white/10 border-white/20 text-white text-sm"
                  data-testid="subtitle-select"
                >
                  <SelectValue placeholder="Subtitles" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="off">Off</SelectItem>
                  {availableSubtitles.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </SelectItem>
                  ))}
                  {availableSubtitles.length === 0 && (
                    <SelectItem value="none" disabled>
                      No subtitles available
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <button 
              onClick={toggleFullscreen}
              className="text-white hover:text-primary transition-colors"
              data-testid="fullscreen-btn"
            >
              <Maximize className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Title Overlay */}
      {title && showControls && (
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/60 to-transparent p-4">
          <h3 className="text-white font-medium">{title}</h3>
        </div>
      )}
    </div>
  );
}
