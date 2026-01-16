import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, FileText, Send, User, Bot, Copy, ThumbsUp, Upload, LogOut } from 'lucide-react';
import StatusStepper from '@/components/StatusStepper';
import { useChatStream } from '@/hooks/useChatStream';
import { useUploadedDocuments } from '../hooks/useUploadedDocuments.jsx';
import { useAuth } from '@/hooks/useAuth';
import { formatGeminiText } from './../lib/utils.jsx';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const [input, setInput] = useState('');
  const [chats , setChats] = useState([]);
  const [currentChat , setCurrentChat] = useState(null);
  const [showDropdown , setShowDropdown] = useState(false);
  const { messages, currentStep, isProcessing, sendMessage ,setMessages } = useChatStream();
  const { user, signOut } = useAuth();
  const scrollRef = useRef(null);
  let {documents , setDocuments , currentDocument , setCurrentDocument , fetchDocuments , pollerRef} = useUploadedDocuments()
  console.log(documents);
  
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isProcessing]);

  useEffect(() => {
    async function getMyChats() {
      const res = await fetch("http://127.0.0.1:8000/api/v1/users/mychat" , {
            credentials : "include"
      })
      const data = await res.json()
      console.log(data);
      setChats(data.chats)
    }
    getMyChats()
  } , [user])

  useEffect(() => {
       fetchDocuments()
       return () => {
         console.log("Hey");
         
         clearInterval(pollerRef.current)
         pollerRef.current = null;
       }
  } , [])

  const handleSend = () => {
    if (!input.trim() || isProcessing) return;
    sendMessage(input , currentChat , setChats , setCurrentChat , (currentDocument ? currentDocument.id : null));
    setInput('');
  };

  const handleSignOut = async () => {
    await signOut();
  };

  const handleChangeOfChat = (chatId) => {
    async function callBackend() {
       const res = await fetch(`http://127.0.0.1:8000/api/v1/chats/${chatId}` , {
           credentials: "include"
       })
       const chatObject = await res.json();
       setCurrentChat(chatId)
       setMessages(chatObject.messages)
    }
    callBackend();
  }

  return (
    <div className="flex h-screen min-h-0 bg-background text-foreground">

      {/* Sidebar */}
      <aside className="w-72 bg-sidebar flex flex-col border-r border-sidebar-border min-h-0">
        <div className="p-6 flex items-center gap-3 border-b border-sidebar-border">
          <div className="bg-primary p-2 rounded-lg shadow-lg animate-pulse-glow">
            <ShieldAlert className="text-primary-foreground" size={20} />
          </div>
          <span className="font-display font-bold text-sidebar-foreground tracking-tight text-lg">
            RiskSense <span className="text-gradient">Pro</span>
          </span>
        </div>

        <div className="p-4 flex flex-col flex-1 mt-4 min-h-0">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-2 mb-4">
            Intelligence Feed
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {chats.length === 0 && (
              <div className="text-sm text-muted-foreground px-2">
                No chats yet
              </div>
            )}

            {[...chats].reverse().map((chat, index) => (
              <button
                key={chat._id ?? index}
                onClick={() => handleChangeOfChat(chat._id)}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-xl
                           bg-secondary text-secondary-foreground text-sm
                           border border-border hover:border-primary/50 transition-colors"
              >
                <FileText size={16} className="text-primary" />
                {chat.title}
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              setCurrentChat(null);
              setMessages([]);
            }}
            className="w-full mt-3 flex items-center gap-3 px-3 py-2 rounded-xl
                       bg-secondary text-secondary-foreground text-sm
                       border border-border hover:border-primary/50 transition-colors"
          >
            <FileText size={16} className="text-primary" />
            New Chat
          </button>

          <div className="mt-3">
            <Link to="/upload">
              <Button variant="outline" className="w-full justify-start gap-2">
                <Upload size={16} />
                Upload Documents
              </Button>
            </Link>
          </div>
        </div>

        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
              <User size={20} className="text-primary" />
            </div>
            <p className="text-sm font-medium truncate">
              {user?.email}
            </p>
          </div>

          <Button
            variant="ghost"
            className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground"
            onClick={handleSignOut}
          >
            <LogOut size={16} />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main Container */}
      <main className="flex-1 flex flex-col m-2 ml-0 rounded-3xl
                       bg-card/50 border border-border overflow-hidden shadow-2xl">

        {/* Header */}
        <header
  className="relative h-20 border-b border-border flex items-center
             px-8 bg-card/80 backdrop-blur-xl"
>
  {/* LEFT — flexible, can shrink */}
  <div className="flex items-center gap-3 min-w-0 flex-1">
    <p className="text-xl font-display font-bold whitespace-nowrap">
      Risk Intelligence Terminal
    </p>

    {currentDocument && (
  <div
    className="flex items-center gap-2 px-3 py-1 rounded-xl
               bg-secondary border border-border text-sm
               text-foreground
               max-w-[280px] min-w-[120px]"
  >
    <FileText size={14} className="text-primary flex-shrink-0" />

    <span
      className="truncate max-w-[220px]"
      title={currentDocument.filename}
    >
      {currentDocument.filename}
    </span>
  </div>
)}

  </div>

  {/* RIGHT — fixed, never pushed */}
  <div className="flex items-center gap-4 flex-shrink-0">
    <div
      className={`transition-all duration-500 ${
        isProcessing ? 'opacity-100' : 'opacity-0'
      }`}
    >
      <StatusStepper currentStep={currentStep} />
    </div>

    {/* Button */}
    <button
      onClick={(e) => {
        e.stopPropagation();
        setShowDropdown((prev) => !prev);
      }}
      className="px-4 py-2 rounded-xl bg-secondary border border-border
                 text-sm font-medium hover:border-primary/50 transition-all"
    >
      Intelligence ▾
    </button>

    {/* DROPDOWN — FIXED POSITION (not clipped) */}
    {showDropdown && (
      <div
        onClick={(e) => e.stopPropagation()}
        className="fixed right-8 top-24 w-72 rounded-2xl
                   bg-card/95 backdrop-blur-xl border border-border
                   shadow-2xl z-50
                   animate-in fade-in slide-in-from-top-2"
      >
        <div className="px-4 py-3 border-b border-border">
          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Signals
          </p>
        </div>

        <div className="max-h-64 overflow-y-auto p-2 space-y-1">
          {documents.map((item, idx) => {
            const isComplete = item.percent_complete === 100;

            return (
              <button
                key={idx}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDropdown(false);
                  if (isComplete) setCurrentDocument(item);
                }}
                className={`w-full text-left px-3 py-2 rounded-xl text-sm
                            border border-border transition-colors
                            ${
                              isComplete
                                ? 'bg-green-500/15 text-green-600 hover:bg-green-500/25'
                                : 'bg-yellow-500/15 text-yellow-600 hover:bg-yellow-500/25'
                            }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate font-medium">
                    {item.filename}
                  </span>

                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full
                                ${
                                  isComplete
                                    ? 'bg-green-500/20 text-green-700'
                                    : 'bg-yellow-500/20 text-yellow-700'
                                }`}
                  >
                    {item.percent_complete}%
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    )}
  </div>
</header>


        {/* Chat Thread */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 md:p-12 space-y-12 bg-background"
        >
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-primary/10 flex items-center justify-center">
                  <ShieldAlert className="text-primary" size={32} />
                </div>
                <h3 className="font-display text-2xl font-bold mb-2">
                  Welcome to RiskSense Pro
                </h3>
                <p className="text-muted-foreground">
                  Ask about financial risks or upload documents for analysis.
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className="flex gap-6 max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700"
            >
              <div className="flex-shrink-0 mt-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  msg.role === 'user'
                    ? 'bg-secondary'
                    : 'border border-primary/30 text-primary'
                }`}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={18} />}
                </div>
              </div>

              <div className="flex-1 space-y-2">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-40">
                  {msg.role === 'user' ? 'User' : 'RiskSense Intelligence'}
                </div>

                <div className="leading-relaxed text-[16px] font-light">
                  {formatGeminiText(msg.content)}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <footer className="p-6 bg-gradient-to-t from-card via-card to-transparent">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end bg-secondary border border-border
                            rounded-2xl shadow-2xl p-2">
              <textarea
                rows="1"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask about financial risks..."
                className="w-full bg-transparent p-3 resize-none outline-none"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isProcessing}
                className="p-2 bg-primary rounded-xl text-primary-foreground"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
