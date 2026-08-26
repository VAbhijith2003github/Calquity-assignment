import React from 'react';

function AuditLogs({ logs }) {
  return (
    <div className="h-28 border-t border-gray-100 bg-white p-3 flex flex-col overflow-hidden shrink-0">
      <h4 className="text-[9px] font-medium text-gray-400 uppercase tracking-widest mb-1.5">
        <i className="fa-solid fa-terminal mr-1"></i> Security Scoping Logs & Audit Trail
      </h4>
      <div className="flex-1 font-mono text-[9px] text-gray-500 overflow-y-auto bg-gray-50 border border-gray-100 p-2 rounded">
        {logs.map((log, idx) => (
          <div key={idx} className="leading-normal py-0.5">{log}</div>
        ))}
      </div>
    </div>
  );
}

export default AuditLogs;
