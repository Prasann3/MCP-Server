import { useState } from 'react';

export const useChatStream = (url) => {
  const [messages, setMessages] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (input, setInput) => {
    setIsProcessing(true);
    setCurrentStep(1);
    setError(null);
    
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    const aiMsgId = Date.now();
    
    setMessages(prev => [...prev, userMsg, { id: aiMsgId, role: 'assistant', content: '' }]);
    setInput('');
    setIsProcessing(true);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let tokenQueue = "";

      const drainInterval = setInterval(() => {
        if (tokenQueue.length > 0) {
          const nextChar = tokenQueue[0];
          tokenQueue = tokenQueue.slice(1);

          setMessages(prev => prev.map(m => 
            m.id === aiMsgId ? { ...m, content: m.content + nextChar } : m
          ));
        }
      }, 0.5);

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          const checkFinished = setInterval(() => {
            if (tokenQueue.length === 0) {
              clearInterval(drainInterval);
              clearInterval(checkFinished);
              setIsProcessing(false);
            }
          }, 100);
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        lines.forEach(line => {
          if (!line.trim()) return;
          try {
            const data = JSON.parse(line);
            if (data.answer) {
              tokenQueue += data.answer;
            }
            if (data.step) setCurrentStep(data.step);
          } catch (e) { 
            console.error("Error parsing:", e); 
          }
        });
      }
    } catch (err) {
      setError(err.message);
      setIsProcessing(false);
    }
  };

  return { messages, currentStep, isProcessing, error, sendMessage, setIsProcessing, setMessages, setCurrentStep };
};
