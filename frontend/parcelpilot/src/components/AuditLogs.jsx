import React from 'react';

function AuditLogs({ logs }) {
  return (
    <div className="h-28 border-t border-gray-800 bg-[#070b13] p-3 flex flex-col overflow-hidden shrink-0">
      <h4 className="text-[9px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
        <i className="fa-solid fa-terminal mr-1"></i> Security Scoping Logs & Audit Trail
      </h4>
      <div className="flex-1 font-mono text-[9px] text-gray-400 overflow-y-auto bg-slate-900/10 border border-slate-950 p-2 rounded">
        {logs.map((log, idx) => (
          <div key={idx} className="leading-normal py-0.5">{log}</div>
        ))}
      </div>
    </div>
  );
}

export default AuditLogs;
