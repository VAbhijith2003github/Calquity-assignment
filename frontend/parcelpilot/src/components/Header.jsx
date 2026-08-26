import React from 'react';

function Header({ activeSession, backendStatus }) {
  const getAvatarInitials = (name) => {
    if (!name) return "";
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  return (
    <header className="h-16 border-b border-gray-800 bg-[#070b13] px-6 flex items-center justify-between z-10 shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md">
          <i className="fa-solid fa-plane-departure text-md"></i>
        </div>
        <div>
          <h1 className="font-bold text-gray-100 text-sm tracking-wide">ParcelPilot</h1>
          <p className="text-[10px] text-gray-400 font-medium">Support & Operations Copilot</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Backend online status indicator */}
        {backendStatus === 'online' ? (
          <span className="px-2.5 py-0.5 rounded-full text-[9px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <i className="fa-solid fa-circle text-[6px] mr-1.5 align-middle"></i> backend online
          </span>
        ) : backendStatus === 'offline' ? (
          <span className="px-2.5 py-0.5 rounded-full text-[9px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse">
            <i className="fa-solid fa-circle text-[6px] mr-1.5 align-middle"></i> backend offline
          </span>
        ) : (
          <span className="px-2.5 py-0.5 rounded-full text-[9px] font-semibold bg-gray-500/10 text-gray-400 border border-gray-500/20">
            connecting...
          </span>
        )}
        
        {/* Active Profile Info */}
        <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-full px-3 py-1 ml-2">
          <div className="text-right">
            <p className="text-[10px] font-semibold text-gray-200">{activeSession.user_name}</p>
            <p className="text-[8px] text-gray-500 uppercase tracking-widest">{activeSession.role}</p>
          </div>
          <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 text-blue-400 text-xs font-bold shadow-inner">
            {getAvatarInitials(activeSession.user_name)}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
