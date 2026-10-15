import React from 'react';

interface FileBadgeIconProps {
  name: string;
  category?: string;
  isDir?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const FileBadgeIcon: React.FC<FileBadgeIconProps> = ({
  name,
  category = '',
  isDir = false,
  size = 'md',
}) => {
  const lowerName = name.toLowerCase();
  const ext = lowerName.includes('.') ? lowerName.substring(lowerName.lastIndexOf('.')) : '';

  const dim = size === 'sm' ? 'w-7 h-7' : size === 'lg' ? 'w-11 h-11' : 'w-9 h-9';
  const textDim = size === 'sm' ? 'text-[9px]' : size === 'lg' ? 'text-[11px]' : 'text-[10px]';

  // Directory / Folder Icon (Matching the soft lavender/rose folder in the screenshots)
  if (isDir || category.includes('Worlds') || category.includes('Projects') || category.includes('Bots')) {
    return (
      <div 
        className={`${dim} rounded-xl flex items-center justify-center shrink-0 shadow-sm relative overflow-hidden transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #a5b4fc 0%, #818cf8 50%, #6366f1 100%)',
          boxShadow: '0 4px 12px -2px rgba(99, 102, 241, 0.45)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5 text-white/95 drop-shadow-xs">
          <path 
            d="M3 7V17C3 18.1046 3.89543 19 5 19H19C20.1046 19 21 18.1046 21 17V9C21 7.89543 20.1046 7 19 7H11L9.29289 5.29289C8.91786 4.91786 8.409 4.70711 7.87868 4.70711H5C3.89543 4.70711 3 5.60254 3 6.70711V7Z" 
            fill="currentColor"
            fillOpacity="0.9"
          />
          <path 
            d="M3 10H21V17C21 18.1046 20.1046 19 19 19H5C3.89543 19 3 18.1046 3 17V10Z" 
            fill="#ffffff" 
            fillOpacity="0.25"
          />
        </svg>
      </div>
    );
  }

  // PDF Badge (Soft Coral-Rose with "PDF" text)
  if (ext === '.pdf' || category.includes('PDF')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm font-bold tracking-tight text-white transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #f87171 0%, #ef4444 60%, #dc2626 100%)',
          boxShadow: '0 4px 14px -2px rgba(239, 68, 68, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M14 2v6h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>PDF</span>
      </div>
    );
  }

  // PNG / Image Badge (Sky blue with "PNG" or mountain graphic)
  if (['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.svg', '.raw', '.heic', '.psd'].includes(ext) || category.includes('Images')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #38bdf8 0%, #0ea5e9 60%, #0284c7 100%)',
          boxShadow: '0 4px 14px -2px rgba(14, 165, 233, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <rect width="18" height="18" x="3" y="3" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>
          <circle cx="9" cy="9" r="2" fill="currentColor"/>
          <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>
          {ext === '.png' ? 'PNG' : ext === '.jpg' || ext === '.jpeg' ? 'JPG' : 'IMG'}
        </span>
      </div>
    );
  }

  // Word / DOCX Badge (Cobalt Blue with "DOCX")
  if (['.doc', '.docx', '.odt', '.rtf', '.pages'].includes(ext) || category.includes('Documents')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 60%, #2563eb 100%)',
          boxShadow: '0 4px 14px -2px rgba(59, 130, 246, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <line x1="8" y1="13" x2="16" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          <line x1="8" y1="17" x2="16" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>DOCX</span>
      </div>
    );
  }

  // Archive / ZIP Badge (Amethyst Purple with "ZIP")
  if (['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.jar'].includes(ext) || category.includes('Archives')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #c084fc 0%, #a855f7 60%, #9333ea 100%)',
          boxShadow: '0 4px 14px -2px rgba(168, 85, 247, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <rect width="20" height="5" x="2" y="3" rx="1" stroke="currentColor" strokeWidth="2"/>
          <path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" stroke="currentColor" strokeWidth="2"/>
          <path d="M10 12h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>
          {ext === '.jar' ? 'JAR' : 'ZIP'}
        </span>
      </div>
    );
  }

  // Spreadsheets (Emerald Green)
  if (['.xls', '.xlsx', '.csv', '.tsv', '.ods'].includes(ext) || category.includes('Spreadsheets')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #4ade80 0%, #22c55e 60%, #16a34a 100%)',
          boxShadow: '0 4px 14px -2px rgba(34, 197, 94, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <rect width="18" height="18" x="3" y="3" rx="2" stroke="currentColor" strokeWidth="2"/>
          <path d="M3 9h18M3 15h18M9 3v18M15 3v18" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>XLS</span>
      </div>
    );
  }

  // Code / Development (Teal / Cyan)
  if (['.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.cpp', '.rs', '.go', '.json', '.html', '.css'].includes(ext) || category.includes('Development')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #2dd4bf 0%, #14b8a6 60%, #0d9488 100%)',
          boxShadow: '0 4px 14px -2px rgba(20, 184, 166, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <polyline points="16 18 22 12 16 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <polyline points="8 6 2 12 8 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>DEV</span>
      </div>
    );
  }

  // Audio (Amber / Honey Gold)
  if (['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac'].includes(ext) || category.includes('Audio')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 60%, #d97706 100%)',
          boxShadow: '0 4px 14px -2px rgba(245, 158, 11, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <path d="M9 18V5l12-2v13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          <circle cx="6" cy="18" r="3" fill="currentColor"/>
          <circle cx="18" cy="16" r="3" fill="currentColor"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>AUDIO</span>
      </div>
    );
  }

  // Video (Fuchsia / Magenta)
  if (['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv'].includes(ext) || category.includes('Videos')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #e879f9 0%, #d946ef 60%, #c026d3 100%)',
          boxShadow: '0 4px 14px -2px rgba(217, 70, 239, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <polygon points="23 7 16 12 23 17 23 7" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
          <rect width="15" height="14" x="1" y="5" rx="2" stroke="currentColor" strokeWidth="2"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>VID</span>
      </div>
    );
  }

  // AI & Models (Violet / Indigo)
  if (['.gguf', '.safetensors', '.ckpt', '.pt', '.onnx'].includes(ext) || category.includes('AI')) {
    return (
      <div 
        className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
        style={{
          background: 'linear-gradient(135deg, #818cf8 0%, #6366f1 60%, #4f46e5 100%)',
          boxShadow: '0 4px 14px -2px rgba(99, 102, 241, 0.42)',
        }}
      >
        <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
          <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
        <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono`}>AI</span>
      </div>
    );
  }

  // Default / Generic Document or File
  return (
    <div 
      className={`${dim} rounded-xl flex flex-col items-center justify-center shrink-0 shadow-sm text-white font-bold transition-transform group-hover:scale-105`}
      style={{
        background: 'linear-gradient(135deg, #94a3b8 0%, #64748b 60%, #475569 100%)',
        boxShadow: '0 4px 12px -2px rgba(100, 116, 139, 0.35)',
      }}
    >
      <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-white/90">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <span className={`${textDim} font-black leading-none mt-0.5 tracking-wider font-mono uppercase`}>
        {ext ? ext.replace('.', '').slice(0, 3) : 'FILE'}
      </span>
    </div>
  );
};
