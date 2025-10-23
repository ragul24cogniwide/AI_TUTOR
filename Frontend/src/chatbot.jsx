import React, { useState, useRef, useEffect, use } from 'react';
import { Send, User, Image, Sparkles } from 'lucide-react';

export default function ChatBot() {
  const starter = "Hey there! Ready to learn something cool today? Ask me anything!";
  const [messages, setMessages] = useState([{ role: 'assistant', content: starter, images: [] }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [subject, setSubject] = useState('english');
  const [chapter, setChapter] = useState([]);
  const messagesEndRef = useRef(null);
  const [showChapters, setShowChapters] = useState(true);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionIds, setSessionIds] = useState(null); //
  const [isPdfMode, setIsPdfMode] = useState(false); //



  useEffect(()=>{
    sendMessage('clear')
    initialMessage(subject)
  },[subject]);

  useEffect(()=>{
    sendmessages('clear')
  },[])

  const API_URL = 'https://schooldigitalised.cogniwide.com/api/sd/tutor/ask';


  const initialMessage = async (subject) => {
    const response = await fetch(`https://schooldigitalised.cogniwide.com/api/sd/tutor/get-initial-response/${subject}`);
    const data = await response.json();
    setMessages(prev => [...prev, { role: 'assistant', content: data?.response}]);
    console.log(data?.data);
   if (subject === 'english' && Array.isArray(data?.data)) {
  const grouped = Object.values(
    data.data.reduce((acc, item) => {
      if (!acc[item.Unit_Name]) {
        acc[item.Unit_Name] = {
          unit: item.Unit_Name,
          chapters: [],
        };
      }
      acc[item.Unit_Name].chapters.push({
        title: item.Lesson_Name,
        grammarTopics: item.Grammar_Topics || [],
      });
      return acc;
    }, {})
  );
  setChapter(grouped);
} else {
  setChapter(data?.data || []);
}


  }

  // Generate or retrieve session_id
  const [sessionId] = useState(() => {
    let existing = typeof window !== 'undefined' ? Math.random().toString(36).substr(2, 9) : 'demo';
    return existing;
  });

  // Scroll to bottom
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Send message to backend
  const sendMessage = async (text) => {
  const messageText = (typeof text === 'string' && text.trim()) ? text.trim() : input.trim();
  if (!messageText || isLoading) return;

  // Hide chapters if user clicked
  setShowChapters(false);
  setMessages(prev => 
    prev.map(msg => msg.role === 'assistant' ? { ...msg, quick_replies: [] } : msg)
  );
  setMessages(prev => [...prev, { role: 'user', content: messageText, images: [] }]);
  setInput('');
  setIsLoading(true);

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, question: messageText, subject: subject }),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || 'Network error');
    }

    const data = await res.json();
    console.log(data);

    const images = Array.isArray(data.images) ? data.images : [];
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.response.replace(/<\/?strong>/g, '')
        .replace(
          /<hint>\s*(.*?)\s*<\/hint>/gs,
          `<div style="background-color:#e6f3ff; padding:8px; border-radius:8px; font-style: italic;">$1</div>`
        ).replace(/\*\*(.*?)\*\*/g, '<b>$1</b>'),
      images: images,
      type: data.correct_answer,
      quick_replies: Array.isArray(data.quick_replies) ? data.quick_replies : []
    }]);


    console.log(data.type);

    if (data.type === 'cleared') {
      setMessages([{ role: 'assistant', content: starter, images: [] }]);
      setShowChapters(true); // reset for new session
    }
  } catch (err) {
    console.error('Send error', err);
    setMessages(prev => [...prev, { role: 'assistant', content: 'Oops — could not reach the server. Try again.', images: [] }]);
  } finally {
    setIsLoading(false);
  }

};

  const sendmessages = async (text) => {
  const messageText = (typeof text === 'string' && text.trim()) ? text.trim() : input.trim();
  if (!messageText || isLoading) return;

  // Hide chapters if user clicked
  setShowChapters(false);
  setMessages(prev => 
    prev.map(msg => msg.role === 'assistant' ? { ...msg, quick_replies: [] } : msg)
  );
  setMessages(prev => [...prev, { role: 'user', content: messageText, images: [] }]);
  setInput('');
  setIsLoading(true);
      try {
      const res = await fetch("http://127.0.0.1:8000/assignment/send-message", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({//
          session_id: sessionIds,
          student_message: messageText
        })
      });//
 
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || 'Network error');
      }
 
      const data = await res.json();
 
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.ai_message, images: [] }
      ]);
 
    } catch (err) {
      console.error('Send error', err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Oops — could not reach the server. Try again.',
        images: []
      }]);
    } finally {
      setIsLoading(false);
    }
  };

// ✅ Handle file upload and AI initial question
  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first.");
      return;
    }
 
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
 
      const startRes = await fetch("http://127.0.0.1:8000/assignment/start-session", {
        method: "POST",
        body: formData,
      });
 
      if (!startRes.ok) throw new Error("Failed to start session");
      const startData = await startRes.json();
      console.log("✅ Session started:", startData);
 
      if (startData.session_id) { //
      setSessionIds(startData.session_id); //
      setIsPdfMode(true);  //
    } //
 
      // ✅ Show first AI message (based on uploaded content)
      if (startData.ai_message) {
        setMessages(prev => [
          ...prev,
          { role: "user", content: `📤 Uploaded: ${file.name} succesfully`, images: []  },
          { role: "assistant", content: startData.ai_message, images: [] }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          { role: "assistant", content: "⚠️ No response received from AI. Please try again.", images: [] }
        ]);
      }
 
    } catch (error) {
      console.error("❌ Upload failed:", error);
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "❌ Upload failed. Please check your file and try again.", images: [] }
      ]);
    } finally {
      setLoading(false);
    }
  };


  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) { //
      if (isPdfMode) {  //
        sendmessages();  //
      } else { //
        sendMessage(); //
      }
    }
  }
    } //
  

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex flex-col overflow-hidden">
      {/* Header with gradient and glow effect */}
      <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-5 text-white shadow-xl">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-white rounded-full blur-md opacity-40 animate-pulse"></div>
              <div className="relative bg-white/20 backdrop-blur-sm p-3 rounded-full border-2 border-white/30">
                <Sparkles className="w-6 h-6" />
              </div>
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-wide flex items-center gap-2">
                Student AI Tutor
              </h2>
              <p className="text-sm text-white/90 font-light">Your personal learning assistant</p>
            </div>
          </div>

          {/* for uploading files */}
          <div>
  {/* Hidden file input */}
  <input
    type="file"
    id="fileInput"
    accept=".pdf,.docx,.jpg,.png"
    style={{ display: "none" }}
    onChange={(e) => setFile(e.target.files[0])}
  />
 
  {/* Upload button */}
  <button
    onClick={() => document.getElementById("fileInput").click()}
    className="px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50 transition-all duration-300 shadow-lg hover:bg-white/30 text-sm font-medium cursor-pointer"
  >
    📎 Choose File
  </button>
 
  {/* Show file name if selected */}
  
 
  {/* Upload trigger button */}
  <button
    onClick={handleUpload}
    disabled={loading || !file}
    className="ml-3 px-4 py-2 rounded-full bg-green-500 hover:bg-green-600 text-white border-2 border-white/30 transition-all duration-300 shadow-lg text-sm font-medium cursor-pointer disabled:opacity-50"
  >
    {loading ? "Uploading..." : "📤 Upload"}
  </button>
</div>
 
 
          
          {/* Subject Dropdown in Header */}
          <div className="flex items-center gap-2">
            {/* <label className="text-sm font-medium text-white/90">Subject:</label> */}
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50 transition-all duration-300 shadow-lg hover:bg-white/30 text-sm font-medium cursor-pointer"
            >
              <option value="english" className="bg-purple-600 text-white">📚 English</option>
              <option value="maths" className="bg-purple-600 text-white">🔢 Mathematics</option>
            </select>
                      <button onClick={()=>sendMessage('clear')} className="px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50 transition-all duration-300 shadow-lg hover:bg-white/30 text-sm font-medium cursor-pointer">clear</button>

          </div>

        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col gap-2 animate-slideIn ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar with glow */}
              <div className="relative flex-shrink-0">
                <div className={`absolute inset-0 rounded-full blur-lg opacity-20 ${msg.role === 'user' ? 'bg-blue-400' : 'bg-purple-400'}`}></div>
                <div className={`relative w-11 h-11 rounded-full flex items-center justify-center shadow-lg transform transition-all duration-300 hover:scale-110 ${msg.role === 'user' ? 'bg-gradient-to-br from-blue-500 to-cyan-500' : 'bg-gradient-to-br from-purple-500 to-pink-500'}`}>
                  {msg.role === 'user' ? (
                    <User className="w-6 h-6 text-white" />
                  ) : (
                    <Sparkles className="w-6 h-6 text-white" />
                  )}
                </div>
              </div>

              {/* Message Bubble with enhanced styling */}
              <div className={`relative group ${msg.role === 'user' ? 'ml-auto' : 'mr-auto'}`}>
                {/* Glow effect on hover */}
                <div className={`absolute inset-0 rounded-3xl blur-2xl opacity-0 group-hover:opacity-30 transition-opacity duration-300 ${msg.role === 'user' ? 'bg-blue-100' : msg.type == true ? 'bg-yellow-100' : 'bg-purple-100'}`}></div>
                
                {/* Achievement style for answers */}
                {msg.role === 'assistant' && msg.type == true && (
                  <>
                    <div className="absolute -top-2 -left-2 w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg animate-bounce-slow z-10">
                      <span className="text-2xl">🏆</span>
                    </div>
                    <div className="absolute -top-1 -right-1 w-8 h-8 bg-gradient-to-br from-yellow-300 to-yellow-500 rounded-full flex items-center justify-center shadow-md z-10">
                      <span className="text-lg">✨</span>
                    </div>
                  </>
                )}
                
                <div className={`relative rounded-3xl px-6 py-4 shadow-lg backdrop-blur-lg transition-all duration-300 group-hover:shadow-2xl
                  ${msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white border border-white/20'
                    : msg.type === true
                      ? 'bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 text-gray-800 border-2 border-yellow-300 shadow-xl'
                      : 'bg-white/90 text-gray-800 border border-purple-100'
                  }`}
                >
                  {/* Type label with badge style */}
                  {msg.type === true && (
                    <div className={`inline-block mb-2 px-3 py-1 rounded-full text-xs font-medium ${
                      msg.role === 'user' 
                        ? 'bg-white/20 text-white' 
                        : msg.type == true
                          ? 'bg-gradient-to-r from-yellow-400 to-orange-400 text-white shadow-md'
                          : 'bg-purple-100 text-purple-700'
                    }`}>
                      {msg.type === true ? '🎓 ' + msg.type : ''}
                    </div>
                  )}

                  {/* Message content */}
                  <div
                    className="whitespace-pre-wrap break-words leading-relaxed text-sm sm:text-base"
                    dangerouslySetInnerHTML={{ __html: msg.content }}
                  />

                  {/* Images with improved layout */}
                  {/* {msg.images?.length > 0 && (
                    <div className="mt-5 space-y-3">
                      <div className="flex items-center gap-2 text-sm font-semibold text-purple-600">
                        <Image className="w-4 h-4" />
                        <span>Related diagrams</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {msg.images.map((img, i) => (
                          <div
                            key={i}
                            className="relative group/img border-2 border-purple-100 rounded-2xl overflow-hidden bg-white shadow-md hover:shadow-2xl transition-all duration-300 hover:scale-105"
                          >
                            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10 opacity-0 group-hover/img:opacity-100 transition-opacity duration-300"></div>
                            <img
                              src={`http://127.0.0.1:8000/app/tutor_assistant/output/${img.name}`}
                              alt="Diagram"
                              className="relative w-full h-auto max-h-80 object-contain p-2"
                              onError={(e) => { e.target.style.display = 'none'; }}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )} */}
                </div>
              </div>
            </div>
            {/* Quick replies (per message) */}
          <div className={`flex gap-3 max-w-[85%] lg:ml-34 xl:ml-44 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>

            {msg.quick_replies && msg.quick_replies.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {msg.quick_replies.map((reply, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(reply)}
                    className="px-4 py-1.5 bg-purple-200 text-purple-800 rounded-full hover:bg-purple-300 transition-all text-sm font-medium"
                  >
                    {reply}
                  </button>
                ))}
              </div>
            )}
            </div>

          </div>
        ))}

      <div className="max-w-7xl mx-auto space-y-6">
{showChapters && Array.isArray(chapter) && (
  <>
    {/* Case 1: Flat list (Maths chapters) */}
    {chapter.every(item => 'title' in item && !('chapters' in item)) ? (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {chapter.map((item, idx) => (
          <button 
            key={idx}
            onClick={() => sendMessage(item.title)}
            className="px-4 py-2 bg-pink-100 from-purple-100 to-pink-500 text-purple-800 font-medium rounded-full shadow-md hover:shadow-lg hover:from-purple-500 hover:to-pink-600 transition-all duration-300"
          >
            {item.title}
          </button>
        ))}
      </div>
    ) : (
      // Case 2: English-style grouped by unit
      chapter.map((unit, unitIdx) => (
        <div 
          key={unitIdx} 
          className="mb-8 bg-gradient-to-r from-purple-50 to-pink-50 p-5 rounded-2xl shadow-inner"
        >
          <h3 className="text-xl font-bold text-purple-800 mb-4 border-b-2 border-purple-300 pb-2">
            {unit.unit}
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {unit.chapters.map((item, idx) => (
              <div
               onClick={() => sendMessage(unit.unit + " : " +  item.title + "\n" + 'Grammer topics' + "\n" + item.grammarTopics.join(", ")).replace(/,/g, ', ')}
                key={idx}
                className="cursor-pointer p-4 bg-white/80 backdrop-blur-sm rounded-xl shadow-sm hover:shadow-md hover:bg-gradient-to-br from-purple-100 to-pink-100 transition-all duration-300"
              >
                <button 
                  className="w-full text-left font-semibold text-purple-700 hover:text-pink-700 transition-colors bg-pink-200"
                >
                  {item.title}
                </button>

                {/* Grammar Topics */}
                <small className=" text-blue-500 px-3 py-1">Grammer topics</small>
                {item.grammarTopics && item.grammarTopics.length > 0 && (
                  
                  <ul className="mt-2 text-sm text-gray-700 list-disc pl-5 space-y-1">
                    {item.grammarTopics.map((topic, tIdx) => (
                      <li 
                        key={tIdx}
                        className="hover:text-pink-600 transition-colors"
                      >
                        {topic}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      ))
    )}
  </>
)}


</div>




        {/* Loading indicator with enhanced animation */}
        {isLoading && (
          <div className="flex gap-3 items-start animate-slideIn">
            <div className="relative flex-shrink-0">
              <div className="absolute inset-0 rounded-full blur-lg bg-purple-400 opacity-50"></div>
              <div className="relative w-11 h-11 rounded-full flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg">
                <Sparkles className="w-6 h-6 text-white animate-pulse" />
              </div>
            </div>
            <div className="bg-white/90 backdrop-blur-sm rounded-3xl px-6 py-4 shadow-lg border border-purple-100">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full animate-bounce"></span>
                <span className="w-2.5 h-2.5 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                <span className="w-2.5 h-2.5 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
  
     
      {/* Enhanced Input Area */}
      <div className="relative p-4 bg-white/80 backdrop-blur-xl border-t border-purple-100 shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-50 to-pink-50 opacity-50"></div>
        <div className="relative flex gap-2">
          <div className="flex-1 relative group">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-20 transition-opacity duration-300"></div>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything..."
              disabled={isLoading}
              rows={1}
              className="relative w-full px-5 py-3 text-sm rounded-2xl bg-white text-gray-800 border-2 border-purple-200 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent resize-none transition-all duration-300 shadow-md hover:shadow-lg placeholder-gray-400"
            />
          </div>
          <button //
  onClick={() => (isPdfMode ? sendmessages() : sendMessage())}
  disabled={!input.trim() || isLoading}
  className="relative group bg-gradient-to-r from-purple-600 to-pink-600 text-white px-5 py-3 rounded-2xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-300 shadow-lg hover:shadow-xl disabled:hover:shadow-lg transform hover:scale-105 disabled:hover:scale-100"
>
  <div className="absolute inset-0 bg-white rounded-2xl blur-lg opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
  <Send className="relative w-5 h-5" />
</button>
//
        </div>
      </div>

      {/* Enhanced Animations */}
      <style>{`
        @keyframes slideIn {
          from { 
            opacity: 0; 
            transform: translateY(20px) scale(0.95);
          }
          to { 
            opacity: 1; 
            transform: translateY(0) scale(1);
          }
        }
        .animate-slideIn { 
          animation: slideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
        }
        ::-webkit-scrollbar-track {
          background: rgba(139, 92, 246, 0.1);
          border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #a78bfa, #ec4899);
          border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #8b5cf6, #db2777);
        }
      `}</style>
    </div>
  );
}