import React from 'react';

function ContextSwitcher({ activeSession, onSwitchSession }) {
  return (
    <div className="p-4 border-b border-gray-800 bg-[#070b13]/60 shrink-0">
      <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">
        <i className="fa-solid fa-shield-halved mr-1.5 text-blue-500"></i> Access Boundaries
      </h3>
      <div className="grid grid-cols-2 gap-2">
        <button 
          onClick={() => onSwitchSession(null, 'support_agent', 'Priya Mehta (CSM)')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === null ? 'border-blue-500 bg-blue-500/10 text-white' : 'border-gray-800 bg-gray-900/30 text-gray-400 hover:bg-gray-900/60'}`}
        >
          <p className="font-bold"><i className="fa-solid fa-user-tie mr-1.5"></i> Priya M.</p>
          <p className="text-[8px] text-gray-500 mt-0.5">CSM Agent (All Access)</p>
        </button>
        <button 
          onClick={() => onSwitchSession('ACCT-001', 'customer', 'Northstar Logistics')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === 'ACCT-001' ? 'border-amber-500 bg-amber-500/10 text-white' : 'border-gray-800 bg-gray-900/30 text-gray-400 hover:bg-gray-900/60'}`}
        >
          <p className="font-bold"><i className="fa-solid fa-building-flag mr-1.5"></i> Northstar</p>
          <p className="text-[8px] text-gray-500 mt-0.5">Enterprise (ACCT-001)</p>
        </button>
        <button 
          onClick={() => onSwitchSession('ACCT-002', 'customer', 'LumenWorks')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === 'ACCT-002' ? 'border-violet-500 bg-violet-500/10 text-white' : 'border-gray-800 bg-gray-900/30 text-gray-400 hover:bg-gray-900/60'}`}
        >
          <p className="font-bold"><i className="fa-solid fa-briefcase mr-1.5"></i> LumenWorks</p>
          <p className="text-[8px] text-gray-500 mt-0.5">Growth (ACCT-002)</p>
        </button>
        <button 
          onClick={() => onSwitchSession('ACCT-003', 'customer', 'Beacon Retail')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === 'ACCT-003' ? 'border-teal-500 bg-teal-500/10 text-white' : 'border-gray-800 bg-gray-900/30 text-gray-400 hover:bg-gray-900/60'}`}
        >
          <p className="font-bold"><i className="fa-solid fa-store mr-1.5"></i> Beacon Retail</p>
          <p className="text-[8px] text-gray-500 mt-0.5">Standard (ACCT-003)</p>
        </button>
      </div>
    </div>
  );
}

export default ContextSwitcher;
