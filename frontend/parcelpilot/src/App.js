import React, { useState, useEffect } from 'react';
import './App.css';

// Import modular dashboard components
import Header from './components/Header';
import ContextSwitcher from './components/ContextSwitcher';
import ChatPanel from './components/ChatPanel';
import DatabaseViewer from './components/DatabaseViewer';
import AuditLogs from './components/AuditLogs';

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'agent',
      text: "Welcome! I'm your Operations Copilot.\n\nI have secure access to the current ParcelPilot policies, custom SLAs, and assessment database. Let me know what I can help you resolve today."
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [activeSession, setActiveSession] = useState({
    account_id: null,
    role: 'support_agent',
    user_name: 'Priya Mehta (CSM)'
  });
  const [dbData, setDbData] = useState({ accounts: [], orders: [], tickets: [] });
  const [activeTab, setActiveTab] = useState('orders');
  const [pendingAction, setPendingAction] = useState(null);
  const [logs, setLogs] = useState(["System initialized. Scoping set to: Priya Mehta (CSM)."]);
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    fetchSession();
    refreshData();
  }, []);

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, `[${time}] ${msg}`]);
  };

  // ── API Operations ────────────────────────────────────────────────────────

  const fetchSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/session`);
      if (res.ok) {
        const data = await res.json();
        setActiveSession(data);
        setBackendStatus('online');
      }
    } catch (err) {
      console.error("Backend offline:", err);
      setBackendStatus('offline');
    }
  };

  const refreshData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/db-view`);
      if (res.ok) {
        const data = await res.json();
        setDbData(data);
        setBackendStatus('online');
      }
    } catch (err) {
      console.error("Error loading database:", err);
      setBackendStatus('offline');
    }
  };

  const handleSwitchSession = async (accountId, role, userName) => {
    try {
      const res = await fetch(`${API_BASE}/api/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account_id: accountId, role: role, user_name: userName })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveSession(data.session);
        setPendingAction(null);
        addLog(`Security context changed to: ${userName}. Scope: ${accountId || 'Global'}`);
        await refreshData();
      }
    } catch (err) {
      console.error("Error switching session:", err);
      addLog("Failed to change security context: Backend offline.");
    }
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!inputValue.trim()) return;

    const userText = inputValue;
    setInputValue('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);

    // Add placeholder message for real-time streaming
    setMessages((prev) => [...prev, { sender: 'agent', text: '', tool_used: '', isStreaming: true }]);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText })
      });

      if (!res.ok) {
        throw new Error("Backend response error");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // Keep last partial line in buffer

        let currentEvent = "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.replace("event:", "").trim();
          } else if (trimmed.startsWith("data:")) {
            const rawData = trimmed.replace("data:", "").trim();
            try {
              const data = JSON.parse(rawData);
              
              if (currentEvent === "chunk") {
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg && lastMsg.sender === 'agent') {
                    return [
                      ...updated.slice(0, -1),
                      { ...lastMsg, text: lastMsg.text + data.text }
                    ];
                  }
                  return updated;
                });
              } else if (currentEvent === "trace") {
                if (data.message) {
                  addLog(`[Agent Process] ${data.message}`);
                }
              } else if (currentEvent === "metadata") {
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg && lastMsg.sender === 'agent') {
                    return [
                      ...updated.slice(0, -1),
                      { ...lastMsg, text: data.text, tool_used: data.tool_used, isStreaming: false }
                    ];
                  }
                  return updated;
                });

                if (data.has_pending) {
                  setPendingAction(data.pending_action);
                  addLog(`Action proposal registered: ${data.pending_action.name || data.pending_action.type}`);
                } else {
                  setPendingAction(null);
                }
              } else if (currentEvent === "error") {
                console.error("SSE Error:", data.error);
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg && lastMsg.sender === 'agent') {
                    return [
                      ...updated.slice(0, -1),
                      { ...lastMsg, text: `Error: ${data.error}`, isStreaming: false }
                    ];
                  }
                  return updated;
                });
              }
            } catch (err) {
              console.error("Error parsing JSON chunk:", err, rawData);
            }
          }
        }
      }
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg && lastMsg.sender === 'agent' && lastMsg.text === '') {
          return [
            ...updated.slice(0, -1),
            { ...lastMsg, text: "Error communicating with operations agent loop. Make sure the backend is running.", isStreaming: false }
          ];
        }
        return [...prev, { sender: 'agent', text: "Error communicating with operations agent loop. Make sure the backend is running." }];
      });
    }
  };

  const handleConfirm = async (confirmBool) => {
    setPendingAction(null);
    try {
      const res = await fetch(`${API_BASE}/api/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm: confirmBool })
      });
      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, { sender: 'agent', text: data.message }]);
        addLog(confirmBool ? "Pending action executed & committed." : "Pending action aborted by user.");
        await refreshData();
      }
    } catch (err) {
      console.error("Confirmation error:", err);
      setMessages((prev) => [...prev, { sender: 'agent', text: "Failed to resolve pending action." }]);
    }
  };

  // ── Suggestions Selector Scoper ───────────────────────────────────────────

  const getSuggestions = () => {
    if (activeSession.account_id === null) {
      return [
        "Status of ticket TKT-501",
        "Apply credit for ORD-2002",
        "Why did bulk upload fail for ticket TKT-502?",
        "Can I cancel order ORD-1001?",
        "Escalate ticket TKT-504"
      ];
    }
    if (activeSession.account_id === "ACCT-001") {
      return [
        "Can I cancel order ORD-1001 without fee?",
        "What is my support SLA resolution target?",
        "Status of ticket TKT-501"
      ];
    }
    if (activeSession.account_id === "ACCT-002") {
      return [
        "Apply credit for order ORD-2002",
        "What are my cancellation terms?",
        "Why did my bulk upload fail (TKT-502)?"
      ];
    }
    return [
      "Check cancellation rules for ORD-3001",
      "What is the first-response target for my support plan?"
    ];
  };

  return (
    <div className="h-screen flex flex-col bg-[#0b0f19] text-gray-200 overflow-hidden font-sans">
      
      {/* Dynamic Header */}
      <Header activeSession={activeSession} backendStatus={backendStatus} />

      {/* Main Workspace Workspace Layout */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Left Side: Scope boundaries + Chatbot */}
        <section className="w-5/12 border-r border-gray-800 flex flex-col bg-[#070b13]/40 overflow-hidden">
          
          {/* Security Context Boundaries Switcher */}
          <ContextSwitcher 
            activeSession={activeSession} 
            onSwitchSession={handleSwitchSession} 
          />

          {/* Assistant Chat Panel */}
          <ChatPanel 
            messages={messages}
            inputValue={inputValue}
            setInputValue={setInputValue}
            onSend={handleSend}
            pendingAction={pendingAction}
            onConfirm={handleConfirm}
            suggestions={getSuggestions()}
          />

        </section>

        {/* Right Side: Database Explorer + Security Logs */}
        <section className="w-7/12 flex flex-col overflow-hidden bg-[#070b13]/10">
          
          {/* Tabbed Database View */}
          <DatabaseViewer 
            dbData={dbData}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />

          {/* Audit Logs Console */}
          <AuditLogs logs={logs} />

        </section>

      </main>

    </div>
  );
}

export default App;
