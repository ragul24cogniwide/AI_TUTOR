import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Image as ImageIcon } from 'lucide-react';
import readingImg from './assets/reading.png';
import { v4 as uuidv4 } from 'uuid'; // npm i uuid

export default function ChatBot() {
  const starter = "Hey there! Ready to learn something cool today? Ask me anything!";
  const [messages, setMessages] = useState([{ role: 'assistant', content: starter, images: [] }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const API_URL = 'http://127.0.0.1:8000/ask';

  // Generate or retrieve session_id
  const [sessionId] = useState(() => {
    let existing = sessionStorage.getItem('session_id');
    if (!existing) {
      existing = uuidv4();
      sessionStorage.setItem('session_id', existing);
    }
    return existing;
  });

  // Scroll to bottom
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Send message to backend
  const sendMessage = async (text) => {
    const messageText = (typeof text === 'string' && text.trim()) ? text.trim() : input.trim();
    if (!messageText || isLoading) return;

    setMessages(prev => [...prev, { role: 'user', content: messageText, images: [] }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, question: messageText }),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || 'Network error');
      }

      const data = await res.json();

      // Ensure images is an array
      const images = Array.isArray(data.images) ? data.images : [];

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        images: images
      }]);
    } catch (err) {
      console.error('Send error', err);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Oops — could not reach the server. Try again.', images: [] }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) sendMessage();
    }
  };

  return (
    <div className="h-screen w-screen bg-white flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-indigo-600 p-4 text-white flex items-center gap-3 shadow">
        <div className="bg-white/20 p-2 rounded-full">
          <img src={readingImg} alt="Tutor" className="w-6 h-6 rounded-full" />
        </div>
        <div>
          <h2 className="text-lg font-bold">Student AI Tutor</h2>
          <p className="text-xs text-white/90">Your personal learning assistant</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-indigo-50 space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col gap-2 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-sky-500' : 'bg-indigo-600'} shadow`}>
                {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <img src={readingImg} alt="Tutor" className="w-5 h-5 rounded-full" />}
              </div>

              <div className={`max-w-[75%] rounded-2xl px-4 py-3 ${msg.role === 'user' ? 'bg-sky-500 text-white' : 'bg-white text-gray-900 border border-indigo-200'} shadow`}>
                <p className="whitespace-pre-wrap break-words">{msg.content}</p>

                {/* Render images */}
                {msg.images && msg.images.length > 0 && (
                  <div className="mt-2 space-y-2">
                    <div className="flex items-center gap-2 text-sm text-blue-600">
                      <ImageIcon className="w-4 h-4" />
                      <span>Related diagrams:</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {msg.images.map((img, i) => (
                        <div key={i} className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                          <img
                              src={`http://127.0.0.1:8000/output/book8/math8/${img.url}`} // prepend backend host
                              alt={'Diagram'}  
                              className="w-full h-auto max-h-48 object-contain"
                              onError={(e) => { e.target.style.display = 'none'; }}
                            />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-2">
            <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-indigo-600 shadow">
              <img src={readingImg} alt="Tutor" className="w-5 h-5 rounded-full" />
            </div>
            <div className="bg-white rounded-2xl px-4 py-3 shadow">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                <span className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t border-indigo-100 shadow-inner">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything..."
            disabled={isLoading}
            rows={2}
            className="flex-1 px-4 py-2 text-sm rounded-xl bg-white text-gray-900 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading}
            className="bg-indigo-600 text-white px-5 py-2 rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.28s ease-out; }
      `}</style>
    </div>
  );
}
