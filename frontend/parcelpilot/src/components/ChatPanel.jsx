import React, { useRef, useEffect } from 'react';

function ChatPanel({ 
  messages, 
  inputValue, 
  setInputValue, 
  onSend, 
  pendingAction, 
  onConfirm, 
  suggestions 
}) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const parseMessageText = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .split('\n')
      .map((line, idx) => (
        <span key={idx}>
          <span dangerouslySetInnerHTML={{ __html: line }} />
          {idx < text.split('\n').length - 1 && <br />}
        </span>
      ));
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-950/20">
      
      {/* Messages List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex items-start gap-2.5 ${m.sender === 'user' ? 'justify-end' : ''}`}>
            {m.sender === 'agent' && (
              <div className="w-6 h-6 rounded bg-gray-800 border border-gray-700 flex items-center justify-center text-blue-400 text-[10px] font-bold shrink-0">
                AI
              </div>
            )}
            <div 
              className={`p-3 rounded-xl text-xs max-w-[85%] leading-relaxed ${m.sender === 'user' ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-sm' : 'bg-gray-900 border border-gray-850 text-gray-200'}`}
            >
              {parseMessageText(m.text)}
              {m.tool_used && (
                <div className="mt-2 flex items-center gap-1.5 text-[8px] font-semibold tracking-wider text-gray-500 uppercase">
                  <i className="fa-solid fa-gears text-blue-500"></i> Tool: {m.tool_used.replace(/_/g, ' ')}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* State Action Confirmation Card */}
      {pendingAction && (
        <div className="p-4 border-t border-blue-500/20 bg-blue-500/5 flex flex-col gap-2 shrink-0">
          <div className="flex items-center gap-2 text-blue-400 text-[10px] font-bold uppercase tracking-wider">
            <i className="fa-solid fa-triangle-exclamation animate-pulse"></i> Action Confirmation Required
          </div>
          <p className="text-xs text-gray-300">
            {pendingAction.type === 'apply_credit' ? (
              <>Apply <strong>INR {Math.abs(pendingAction.amount)} {pendingAction.amount < 0 ? 'fee charge' : 'credit refund'}</strong> to order <strong>{pendingAction.order_id}</strong>?</>
            ) : pendingAction.type === 'escalate_ticket' ? (
              <>Escalate ticket <strong>{pendingAction.ticket_id}</strong> to the <strong>Engineering Lead</strong>?</>
            ) : (
              <>Execute pending status update?</>
            )}
          </p>
          <div className="flex gap-2 mt-1">
            <button 
              onClick={() => onConfirm(true)} 
              className="flex-1 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition duration-150 shadow"
            >
              Confirm
            </button>
            <button 
              onClick={() => onConfirm(false)} 
              className="flex-1 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 font-semibold text-xs border border-gray-700 transition duration-150"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Suggestion Chips */}
      <div className="px-4 py-2 border-t border-gray-800 bg-[#070b13]/25 shrink-0">
        <p className="text-[9px] text-gray-500 uppercase font-bold mb-1.5 tracking-wider">Suggested Queries:</p>
        <div className="flex flex-wrap gap-1">
          {suggestions.map((s, idx) => (
            <button 
              key={idx} 
              onClick={() => setInputValue(s)}
              className="text-[9px] bg-gray-900 hover:bg-gray-800 text-gray-400 border border-gray-850 rounded px-2.5 py-0.5 transition duration-100 font-medium"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Message Input Box Form */}
      <form onSubmit={onSend} className="p-3 border-t border-gray-800 bg-gray-950/40 flex items-center gap-2 shrink-0">
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask a question or request an action..." 
          className="flex-1 bg-gray-900 border border-gray-800 text-gray-200 text-xs rounded-lg px-3.5 py-2.5 focus:outline-none focus:border-blue-500/50 transition duration-150"
          autoComplete="off"
        />
        <button type="submit" className="w-9 h-9 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center text-white transition duration-150 shadow-md">
          <i className="fa-solid fa-paper-plane text-xs"></i>
        </button>
      </form>

    </div>
  );
}

export default ChatPanel;
