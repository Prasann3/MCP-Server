import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, FileText, Send, User, Bot, Copy, ThumbsUp, Upload, LogOut } from 'lucide-react';
import StatusStepper from '@/components/StatusStepper';
import { useChatStream } from '@/hooks/useChatStream';
import { useAuth } from '@/hooks/useAuth';
import { formatGeminiText } from './../lib/utils.jsx';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const [input, setInput] = useState('');
  const { messages, currentStep, isProcessing, sendMessage } = useChatStream('http://localhost:8000/chat');
  const { user, signOut } = useAuth();
  const scrollRef = useRef(null);
  
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isProcessing]);

  const handleSend = () => {
    if (!input.trim() || isProcessing) return;
    sendMessage(input, setInput);
    setInput('');
  };

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 bg-sidebar flex flex-col border-r border-sidebar-border">
        <div className="p-6 flex items-center gap-3 border-b border-sidebar-border">
          <div className="bg-primary p-2 rounded-lg shadow-lg animate-pulse-glow">
            <ShieldAlert className="text-primary-foreground" size={20} />
          </div>
          <span className="font-display font-bold text-sidebar-foreground tracking-tight text-lg">
            RiskSense <span className="text-gradient">Pro</span>
          </span>
        </div>
        
        <div className="p-4 flex-1 space-y-4 mt-4">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-2 mb-4">
            Intelligence Feed
          </div>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded-xl bg-secondary text-secondary-foreground text-sm border border-border hover:border-primary/50 transition-colors">
            <FileText size={16} className="text-primary" /> 2024 10-K Report
          </button>
          
          <Link to="/upload" className="block">
            <Button variant="outline" className="w-full justify-start gap-2">
              <Upload size={16} /> Upload Documents
            </Button>
          </Link>
        </div>

        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
              <User size={20} className="text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">
                {user?.email}
              </p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground"
            onClick={handleSignOut}
          >
            <LogOut size={16} /> Sign Out
          </Button>
        </div>
      </aside>
  
      {/* Main Container */}
      <main className="flex-1 flex flex-col m-2 ml-0 rounded-3xl bg-card/50 border border-border overflow-hidden shadow-2xl">
        
        {/* Header */}
        <header className="h-20 border-b border-border flex items-center px-8 justify-between bg-card/80 backdrop-blur-xl">
          <div>
            <h2 className="text-[10px] font-bold text-primary uppercase tracking-[0.2em]">Live Analysis</h2>
            <p className="text-xl font-display font-bold text-foreground">Risk Intelligence Terminal</p>
          </div>
          <div className={`transition-all duration-500 ${isProcessing ? 'opacity-100' : 'opacity-0'}`}>
            <StatusStepper currentStep={currentStep} />
          </div>
        </header>
  
        {/* Chat Thread */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 md:p-12 space-y-12 bg-background">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-primary/10 flex items-center justify-center">
                  <ShieldAlert className="text-primary" size={32} />
                </div>
                <h3 className="font-display text-2xl font-bold text-foreground mb-2">
                  Welcome to RiskSense Pro
                </h3>
                <p className="text-muted-foreground">
                  Ask me anything about financial risks, regulatory compliance, or upload documents for analysis.
                </p>
              </div>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className="flex gap-6 max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
              
              <div className="flex-shrink-0 mt-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  msg.role === 'user' 
                    ? 'bg-secondary text-secondary-foreground' 
                    : 'bg-transparent text-primary border border-primary/30'
                }`}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={18} />}
                </div>
              </div>

              <div className="flex-1 space-y-2">
                <div className={`text-[10px] font-bold uppercase tracking-[0.2em] opacity-40 mb-2 ${
                  msg.role === 'user' ? 'text-muted-foreground' : 'text-primary'
                }`}>
                  {msg.role === 'user' ? 'User' : 'RiskSense Intelligence'}
                </div>

                <div className={`leading-relaxed text-[16px] text-foreground font-light ${
                  isProcessing && idx === messages.length - 1 
                    ? 'after:content-["▋"] after:ml-1 after:animate-pulse after:text-primary' 
                    : ''
                }`}>
                  {formatGeminiText(msg.content)}
                </div>

                {msg.role !== 'user' && (
                  <div className="flex items-center gap-4 pt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="text-muted-foreground hover:text-primary transition-colors">
                      <Copy size={14} />
                    </button>
                    <button className="text-muted-foreground hover:text-primary transition-colors">
                      <ThumbsUp size={14} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
  
        {/* Input Section */}
        <footer className="relative p-6 bg-gradient-to-t from-card via-card to-transparent">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-end bg-secondary border border-border rounded-2xl shadow-2xl focus-within:border-primary focus-within:ring-1 focus-within:ring-primary transition-all p-2">
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
                className="w-full bg-transparent p-3 text-[15px] outline-none resize-none placeholder:text-muted-foreground min-h-[44px] max-h-48 text-foreground"
              />
              <button 
                onClick={handleSend}
                disabled={!input.trim() || isProcessing}
                className="mb-1 mr-1 p-2 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 active:scale-90 transition-all disabled:bg-muted disabled:text-muted-foreground"
              >
                <Send size={20} />
              </button>
            </div>
            <p className="text-center text-[10px] text-muted-foreground mt-3 tracking-wide">
              RiskSense AI can make mistakes. Check important financial info.
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
