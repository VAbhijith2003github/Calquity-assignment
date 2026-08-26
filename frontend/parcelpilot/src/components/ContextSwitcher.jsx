import React from 'react';

function ContextSwitcher({ activeSession, onSwitchSession }) {
  return (
    <div className="p-4 border-b border-gray-100 bg-white shrink-0">
      <h3 className="text-[10px] font-medium text-gray-400 uppercase tracking-widest mb-3">
        <i className="fa-solid fa-shield-halved mr-1.5 text-gray-400"></i> Access Boundaries
      </h3>
      <div className="grid grid-cols-2 gap-2">
        <button 
          onClick={() => onSwitchSession(null, 'support_agent', 'Priya Mehta (CSM)')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === null ? 'border-gray-900 bg-gray-900 text-white shadow-sm' : 'border-gray-200/70 bg-white text-gray-600 hover:bg-gray-50/70'}`}
        >
          <p className="font-medium"><i className="fa-solid fa-user-tie mr-1.5"></i> Priya M.</p>
          <p className={`text-[8px] mt-0.5 ${activeSession.account_id === null ? 'text-gray-400' : 'text-gray-400'}`}>CSM Agent (All Access)</p>
        </button>
        <button 
          onClick={() => onSwitchSession('ACCT-001', 'customer', 'Northstar Logistics')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === 'ACCT-001' ? 'border-gray-900 bg-gray-900 text-white shadow-sm' : 'border-gray-200/70 bg-white text-gray-600 hover:bg-gray-50/70'}`}
        >
          <p className="font-medium"><i className="fa-solid fa-building-flag mr-1.5"></i> Northstar</p>
          <p className={`text-[8px] mt-0.5 ${activeSession.account_id === 'ACCT-001' ? 'text-gray-400' : 'text-gray-400'}`}>Enterprise (ACCT-001)</p>
        </button>
        <button 
          onClick={() => onSwitchSession('ACCT-002', 'customer', 'LumenWorks')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === 'ACCT-002' ? 'border-gray-900 bg-gray-900 text-white shadow-sm' : 'border-gray-200/70 bg-white text-gray-600 hover:bg-gray-50/70'}`}
        >
          <p className="font-medium"><i className="fa-solid fa-briefcase mr-1.5"></i> LumenWorks</p>
          <p className={`text-[8px] mt-0.5 ${activeSession.account_id === 'ACCT-002' ? 'text-gray-400' : 'text-gray-400'}`}>Growth (ACCT-002)</p>
        </button>
        <button 
          onClick={() => onSwitchSession('ACCT-003', 'customer', 'Beacon Retail')}
          className={`p-2.5 rounded-lg text-left border text-xs transition duration-150 ${activeSession.account_id === 'ACCT-003' ? 'border-gray-900 bg-gray-900 text-white shadow-sm' : 'border-gray-200/70 bg-white text-gray-600 hover:bg-gray-50/70'}`}
        >
          <p className="font-medium"><i className="fa-solid fa-store mr-1.5"></i> Beacon Retail</p>
          <p className={`text-[8px] mt-0.5 ${activeSession.account_id === 'ACCT-003' ? 'text-gray-400' : 'text-gray-400'}`}>Standard (ACCT-003)</p>
        </button>
      </div>
    </div>
  );
}

export default ContextSwitcher;
