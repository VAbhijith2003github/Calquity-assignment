import React, { useRef, useEffect } from 'react';

/* ── Typing dots animation (CSS injected once) ─────────────────────────── */
const TYPING_STYLE = `
@keyframes bounce-dot {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40%            { transform: translateY(-5px); opacity: 1; }
}
.typing-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #6b7280;
  display: inline-block;
  animation: bounce-dot 1.2s infinite ease-in-out;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
`;

if (!document.getElementById('typing-anim-style')) {
  const style = document.createElement('style');
  style.id = 'typing-anim-style';
  style.textContent = TYPING_STYLE;
  document.head.appendChild(style);
}

/* ── Component ──────────────────────────────────────────────────────────── */
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
    <div className="flex-1 flex flex-col overflow-hidden bg-gray-50/50">
      
      {/* Messages List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex items-start gap-2.5 ${m.sender === 'user' ? 'justify-end' : ''}`}>
            {m.sender === 'agent' && (
              <div className="w-6 h-6 rounded bg-gray-900 flex items-center justify-center text-white text-[9px] font-bold shrink-0 shadow-sm">
                AI
              </div>
            )}
            <div 
              className={`p-3 rounded-xl text-xs max-w-[85%] leading-relaxed shadow-sm ${m.sender === 'user' ? 'bg-gray-900 text-white' : 'bg-white border border-gray-100 text-gray-800'}`}
            >
              {/* Show animated dots if streaming with no text yet */}
              {m.isStreaming && !m.text ? (
                <span className="flex items-center gap-1.5 py-0.5 px-1">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </span>
              ) : (
                <>
                  {parseMessageText(m.text)}
                  {m.tool_used && (
                    <div className="mt-2 flex items-center gap-1.5 text-[8px] font-medium tracking-wider text-gray-400 uppercase">
                      <i className="fa-solid fa-gears text-gray-400"></i> Tool: {m.tool_used.replace(/_/g, ' ')}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* State Action Confirmation Card */}
      {pendingAction && (
        <div className="p-4 border-t border-gray-100 bg-white flex flex-col gap-2 shrink-0 shadow-inner">
          <div className="flex items-center gap-2 text-indigo-600 text-[10px] font-semibold uppercase tracking-wider">
            <i className="fa-solid fa-circle-info"></i> Action Confirmation Required
          </div>
          <p className="text-xs text-gray-700 font-medium">
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
              className="flex-1 py-1.5 rounded bg-gray-900 hover:bg-gray-800 text-white font-medium text-xs transition duration-150 shadow-sm"
            >
              Confirm
            </button>
            <button 
              onClick={() => onConfirm(false)} 
              className="flex-1 py-1.5 rounded bg-white hover:bg-gray-50 text-gray-600 font-medium text-xs border border-gray-200/80 transition duration-150"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Suggestion Chips */}
      <div className="px-4 py-2 border-t border-gray-100 bg-white shrink-0">
        <p className="text-[9px] text-gray-400 uppercase font-medium mb-1.5 tracking-wider">Suggested Queries:</p>
        <div className="flex flex-wrap gap-1">
          {suggestions.map((s, idx) => (
            <button 
              key={idx} 
              onClick={() => setInputValue(s)}
              className="text-[9px] bg-gray-50 hover:bg-gray-100 text-gray-600 border border-gray-200/60 rounded px-2.5 py-0.5 transition duration-100 font-medium"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Message Input Box Form */}
      <form onSubmit={onSend} className="p-3 border-t border-gray-100 bg-white flex items-center gap-2 shrink-0">
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask a question or request an action..." 
          className="flex-1 bg-gray-50 border border-gray-200/80 text-gray-900 placeholder-gray-500 text-xs rounded-lg px-3.5 py-2.5 focus:outline-none focus:border-gray-400 focus:bg-white transition duration-150"
          autoComplete="off"
        />
        <button type="submit" className="w-9 h-9 rounded-lg bg-gray-900 hover:bg-gray-800 flex items-center justify-center text-white transition duration-150 shadow-sm">
          <i className="fa-solid fa-paper-plane text-xs"></i>
        </button>
      </form>

    </div>
  );
}

export default ChatPanel;
